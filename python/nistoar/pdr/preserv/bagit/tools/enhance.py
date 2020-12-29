"""
various tools for enhancing the metadata and ancillary content of a 
NIST-style bag.  
"""
import re, logging
from collections import OrderedDict, Mapping

from nistoar.nerdm.convert import DOIResolver
from nistoar.doi import is_DOI, DOIResolutionException

class AuthorFetcher(object):
    """
    a tool that will set or update the NERDm encoded author list if the 
    resource's DOI is known.

    :seealso nistoar.nerdm.convert.DOIResolver:
    :seealso nistoar.nerdm.convert.PODds2Res:
    """

    def __init__(self, cfg=None):
        """
        create a fetcher with the given configuration.  The configuration
        parameters supported are the same as supported by DOIResolver.
        """
        if cfg == None: cfg = {}
        self.cfg = cfg
        self.doir = DOIResolver.from_config(self.cfg)

    def fetch_authors(self, nerd):
        """
        return an array containing the ordered list of authors for the resource
        described by the given NERDm record.  This will look for a 'doi' 
        property, resolve the identifier given there to its metadata, and 
        convert it to a NERDm author metadata list.  

        :param dict nerd:    the NERDm record describing a DOI-registered 
                             resource.
        :return list of dicts or None:  the NERDm author list based on the DOI
                             or null if a DOI is not set.
        :raises DOIDoesNotExist:  if the DOI is set but is not resolvable because
                             it is not currently registered with known DOI 
                             providers.  
        :raises DOIResolutionException:  if some other error occurs while 
                             attempting to resolve the DOI.
        """
        if not nerd.get('doi'):
            return None
        return self.doir.to_authors(nerd['doi'])


    def update_authors(self, bagbldr, as_annot=False):
        """
        update the NERDm metadata in the bag opened for updates via the given
        bag builder, setting or replacing the author list based on dataset's 
        DOI.  If the DOI is not set, the metadata will not be updated.  

        :param BagBuilder bagbldr:  the BagBuilder instance wrapping the bag to 
                                    update.  
        :param bool as_annot:       if True, the authors will be set as an
                                    annotation (i.e. in the annot.json file).
        :return bool:  False if a DOI was not set, or True if it was and an 
                       author list could be constructed from it.  
        :raises DOIDoesNotExist:  if the DOI is set but is not resolvable because
                             it is not currently registered with known DOI 
                             providers.  
        :raises DOIResolutionException:  if some other error occurs while 
                             attempting to resolve the DOI.
        """
        if not bagbldr.bag:
            return False
        
        resmd = bagbldr.bag.nerd_metadata_for("", True)
        auths = self.fetch_authors(resmd)
        if not auths:
            return False
        
        if as_annot:
            resmd = bagbldr.bag.annotations_metadata_for('');
            auths = self._merge_auths(resmd, auths)
            bagbldr.update_annotations_for('', {'authors': auths})

        else:
            auths = self._merge_auths(resmd, auths)
            bagbldr.update_metadata_for('', {'authors': auths})

        return True

    def _merge_auths(self, resmd, auths):
        # new author list will replace the old one
        return auths

def update_authors(bagbldr, as_annot=False, config=None):
    """
    update the NERDm metadata in the bag opened for updates via the given
    bag builder, setting or replacing the author list based on dataset's 
    DOI.  If the DOI is not set, the metadata will not be updated.  

    This is a convenience wrapper around the AuthorFetcher class.

    :param BagBuilder bagbldr:  the BagBuilder instance wrapping the bag to 
                                update.  
    :param bool as_annot:       if True, the authors will be set as an
                                annotation (i.e. in the annot.json file).
    :param dict config:         the configuration to use; the properties 
                                supported are the ones supported by the 
                                AuthorFetcher class (and the DOIResolver 
                                class).  If None, default values will be used. 
    :return bool:  False if a DOI was not set, or True if it was and an 
                   author list could be constructed from it.  
    :raises DOIDoesNotExist:  if the DOI is set but is not resolvable because
                         it is not currently registered with known DOI 
                         providers.  
    :raises DOIResolutionException:  if some other error occurs while 
                         attempting to resolve the DOI.

    """
    return AuthorFetcher(config).update_authors(bagbldr, as_annot)


_altdoifmt = re.compile('^((https?://dx.doi.org/)|(doi:))')
def normalize_doi(doi):
    """
    convert a DOI recognized as using an alternate format (i.e., beginning with "doi:" or 
    "https://ds.doi.org/") to the prefered format (i.e., beginning with "https://doi.org/")
    """
    return _altdoifmt.sub('https://doi.org/', doi)

class ReferenceEnhancer(object):
    """
    a tool that will, for the metadata in a given bag, enhance the references' 
    descriptions that are provided via a DOI by resolving it to its providers' 
    metadata.  

    :seealso nistoar.nerdm.convert.DOIResolver:
    :seealso nistoar.nerdm.convert.PODds2Res:
    """

    def __init__(self, cfg=None, log=None):
        """
        create an enhancer with the given configuration.  The configuration
        parameters supported are the same as supported by DOIResolver.
        """
        if cfg == None: cfg = {}
        self.cfg = cfg
        self.doir = DOIResolver.from_config(self.cfg)
        self.log = log

    def enhancer_for(self, bagbldr, as_annot=False):
        """
        return a ReferenceEnhancer.ForResource instance for the given builder-
        wrapped bag.  This method can be used to take finer control over the 
        update of references.  
        """
        refs = bagbldr.bag.nerd_metadata_for('', as_annot).get("references")
        return self.ForResource(self.doir, refs, self.log)

    def enhance_refs(self, bagbldr, as_annot=False, override=False):
        """
        enhance the descriptions of the references in the bag's metadata 
        having DOIs.

        :param BagBuilder bagbldr:  the bag (wrapped in a BagBuilder instance) 
                                    whose metadata should be updated
        :param bool      as_annot:  if True save the enhanced references as 
                                    annotations based on the merged version of 
                                    the metadata. (See also 
                                    synchronize_annotated_refs())
        :param bool      override:  If False, do not enhance a record that 
                                    already appears to be enhanced.  
        """
        if self.log:
            self.log.debug("Enhancing any DOI references found")
        enh = self.enhancer_for(bagbldr, as_annot)
        enh.enhance_existing(override)

        updmd = { 'references': enh.refs.values() }
        if as_annot:
            bagbldr.update_annotations_for('', updmd)
        else:
            bagbldr.update_metadata_for('', updmd)

    def synchronize_annotated_refs(self, bagbldr, override=False):
        """
        update the references given in the bag's annotations to be synchronized 
        with the un-annotated version of the references.  

        This method addresses a specific use case where the unannotated 
        references is updated by a publication ingest process (e.g. converted 
        from a POD record) but the enhanced version is stored as annotations
        (and is thus is manipulate-able by a user).  For references identified
        by a URL (including a DOI), the unannotated reference list should be the
        definitive source of which references should ultimately be included.  
        This method will not only ensure that enhanced references are saved 
        to the annotations but it will also remove those references that are 
        not part of the un-annotated list.  Note that annotatated references 
        that do not have a location property (e.g. because they are only 
        available in print, not on-line) will not be removed as they can only 
        be provided by the user.  

        Note that while the unannotated list controls which references get 
        included (mostly), the annotated list controls the order.  

        :param BagBuilder bagbldr:  the bag (wrapped in a BagBuilder instance) 
                                    whose metadata should be updated
        :param bool      override:  If False, do not enhance a record that 
                                    already appears to be enhanced.  
        """
        if self.log:
            self.log.debug("Enhancing any DOI references found")
        enh = self.enhancer_for(bagbldr, True)
        urefs = bagbldr.bag.nerd_metadata_for('', False)
        urefs = urefs.get('references', [])

        unannot = OrderedDict()
        for ref in urefs:
            if 'location' in ref:
                unannot[normalize_doi(ref['location'])] = ref

        # remove any references in the annotated reference list that
        # might have gotten removed from the unannotated list
        enh.remove_missing_from(unannot.values())

        # Now enhance the ones that are left.  References newly added to
        # the unannotated list will get added to the annotated list.
        for loc in unannot:
            if is_DOI(loc):
                enh.merge_enhanced_ref(loc, override)
            elif loc not in enh.refs:
                enh.refs[loc] = unannot[loc]

        # Now save the updated references to bag's annotations
        bagbldr.update_annotations_for('', { 'references': enh.refs.values() })
        
        

    class ForResource(object):
        """
        This inner class handles the updates for a specific list of references
        (presumably from a single NERDm record).  The initial list serves as 
        a base line and the guide for the proper order.  The 
        merge_enhanced_ref() method enhances the specific reference identified 
        by a DOI; if that DOI does not exist, an enhanced reference for it is 
        add to the list.  The enhance_existing() method will simply called 
        merge_enhanced_ref() for each DOI in the baseline list of references.  

        An instance of this class can also be used to remove references via
        its remove_missing_from() method.  

        These methods manipulate the baseline list of references which is stored
        in the ref property as an OrderedDict mapping a reference's URL location
        (which need not be a DOI) to its NERDm description.  This class does not
        take care of updating the bag that it came from; rather, the caller 
        (usually the parent ReferenceEnhancer instance) accesses the ref 
        property to create a new reference list to save back into the bag's
        metadata. 
        """

        def __init__(self, doi_resolver, baserefs, logger=None):
            """
            wrap and operate on a given list of 
            """
            self.doir = doi_resolver
            self.refs = self._index_refs(baserefs)
            self.log = logger

        def _index_refs(self, reflist):
            # create a mapping of URL locations to reference node for 
            # the previously existing references; preserve the order.
            if reflist is None:
                reflist = []
            out = OrderedDict()
            i=0
            for ref in reflist:
                if 'location' in ref:
                    key = normalize_doi(ref['location'])
                                         
                    out[key] = ref
                else:
                    # we won't allow updates to entries with out a URL
                    # location (i.e. just a citation), but we want to preserve
                    # the order, so give it a fake lookup.
                    out['_#'+str(i)] = ref
                i += 1

            return out

        def merge_enhanced_ref(self, doi, override=False):
            """
            resolve the doi into a NERDm reference description and merge
            it into reference list.  If override is false, the reference
            is already part of the list, and it has already been enhanced,
            the DOI will not be resolved and the existing reference
            description will not be overridden
            """
            key = normalize_doi(doi)
            try:

                if key in self.refs:
                    if not override and 'citation' in self.refs[key]:
                        return False
                    id = self.refs[key].get('@id')
                    refType = self.refs[key].get("refType")
                    self.refs[key].update(self.doir.to_reference(doi))
                    if id:
                        self.refs[key]['@id'] = id  # keep previous @id
                    if refType and refType != "References":
                        # "References" is a generic reference; if the enhanced one is more specific
                        # use it; otherwise, keep the original designation
                        self.refs[key]['refType'] = refType

                else:
                    self.refs[key] = self.doir.to_reference(doi)
                    if self.refs[key]['@id'].startswith("doi:"):
                        self.refs[key]['@id'] = normalize_doi(self.refs[key]['@id'])

            except DOIResolutionException as ex:
                if self.log:
                    self.log.error("Problem enhancing DOI, %s: %s" %
                                   (doi, str(ex)))
                return False

            return True

        def enhance_existing(self, override=False):
            locs = self.refs.keys()
            for loc in locs:
                if is_DOI(loc):
                    self.merge_enhanced_ref(loc, override)

        def remove_missing_from(self, refs):
            """
            remove references that are not included in the given list of
            references.  A list item can either be a doi or a nerdm
            reference.  A NERDm reference must have a location property, 
            or it will be ignored.  Existing references that do not have 
            real location value will not be removed.  
            """
            out = OrderedDict()
            locs = []
            for ref in refs:
                if isinstance(ref, (str, unicode)):
                    # it's a DOI
                    ref = normalize_doi(ref)
                elif isinstance(ref, Mapping) and 'location' in ref:
                    ref = normalize_doi(ref['location'])
                else:
                    continue
                locs.append(ref)

            for loc in self.refs:
                if loc.startswith('_#') or loc in locs:
                    out[loc] = self.refs[loc]

            self.refs = out
            
def enhance_refs(bagbldr, as_annot=False, override=False, config=None):
    """
    enhance the descriptions of the references identified by a DOI by resolving 
    it to its identifier metadata.  

    This is a convenience wrapper function around the ReferenceEnhancer; use 
    that class directly to take more control over the process.  

    :param BagBuilder bagbldr:  the bag (wrapped in a BagBuilder instance) 
                                whose metadata should be updated
    :param bool      as_annot:  if True save the enhanced references as 
                                annotations based on the merged version of 
                                the metadata. 
    :param bool      override:  If False, do not enhance a record that 
                                already appears to be enhanced.  
    :param dict      config:    the configuration to use; the properties 
                                supported are the ones supported by the 
                                ReferenceEnhancer class (and the DOIResolver 
                                class).  If None, default values will be used. 
    """
    return ReferenceEnhancer(config).enhance_refs(bagbldr, as_annot, override)

def synchronize_enhanced_refs(bagbldr, override=False, config=None, log=None):
    """
    enhance the reference descriptions, saving the enhancements as annotations,
    using the unannotated references as a guide.  

    This method addresses a specific use case where the unannotated 
    references is updated by a publication ingest process (e.g. converted 
    from a POD record) but the enhanced version is stored as annotations
    (and is thus is manipulate-able by a user).  For references identified
    by a URL (including a DOI), the unannotated reference list should be the
    definitive source of which references should ultimately be included.  
    This method will not only ensure that enhanced references are saved 
    to the annotations but it will also remove those references that are 
    not part of the un-annotated list.  Note that annotatated references 
    that do not have a location property (e.g. because they are only 
    available in print, not on-line) will not be removed as they can only 
    be provided by the user.  

    Note that while the unannotated list controls which references get 
    included (mostly), the annotated list controls the order.  

    :param BagBuilder bagbldr:  the bag (wrapped in a BagBuilder instance) 
                                whose metadata should be updated
    :param bool      override:  If False, do not enhance a record that 
                                already appears to be enhanced.  
    :param dict        config:  the configuration to use; the properties 
                                supported are the ones supported by the 
                                ReferenceEnhancer class (and the DOIResolver 
                                class).  If None, default values will be used. 
    :param Logger         log:  A logger to use for messages reporting on 
                                resolution activity.  If not provided, no 
                                messages will be logged.
    """
    return ReferenceEnhancer(config, log=log) \
                                  .synchronize_annotated_refs(bagbldr,override)

