"""
This module manages the preparation of the metadata needed by pre-publication
landing page service.  It uses an SIPBagger to create the NERDm metadata from 
POD metadata provided by MIDAS and assembles it into an exportable form.  
"""
import os, logging, re, json, copy
from collections import Mapping, OrderedDict

from .. import PublishSystem
from ...exceptions import (ConfigurationException, StateException,
                           SIPDirectoryNotFound, IDNotFound, PDRServiceException)
from ...preserv.bagger import (MIDASMetadataBagger, UpdatePrepService,
                               midasid_to_bagname)
from ...preserv.bagit import NISTBag, BagBuilder, DEF_MERGE_CONV
from ...utils import build_mime_type_map, read_nerd
from ....id import PDRMinter, NIST_ARK_NAAN
from ....nerdm import validate_nerdm
from ....nerdm.convert import Res2PODds
from .... import pdr
from . import midasclient as midas

log = logging.getLogger(PublishSystem().subsystem_abbrev)

class PrePubMetadataService(PublishSystem):
    """
    The class providing the implementation for the pre-publication metadata
    service.

    This service wraps the MIDASMetadataBagger class which examines the MIDAS 
    upload and review directories for data and metadata and prepares the 
    NERDm metadata.  This class then will serve out the final, combined NERDm 
    record, converting (if so configured) the downloadURLs to bypass the 
    data distribution service (as is necessary for the pre-publication data).  

    This class takes a configuration dictionary at construction; the following
    properties are supported:

    :prop working_dir str #req:  an existing directory where working data can
                      can be stored.  
    :prop review_dir  str #req:  an existing directory containing MIDAS review
                      data
    :prop upload_dir  str #req:  an existing directory containing MIDAS upload
                      data
    :prop id_registry_dir str:   a directory to store the minted ID registry.
                      the default is the value of the working directory.
    :prop mimetype_files list of str ([]):   an ordered list of filepaths to 
                      files that map file extensions to default MIME types.  
                      Mappings in the latter files override those in the former 
                      ones.
    :prop id_minter dict ({}):  a dictionary for configuring the ID minter 
                      instance.
    :prop bagger dict ({}):  a dictionary for configuring the SIPBagger instance
                      used to process the SIP (see SIPBagger implementation 
                      documentation for supported sub-properties).  
    """

    def __init__(self, config, workdir=None, reviewdir=None, uploaddir=None,
                 idregdir=None):
        """
        initialize the service.

        :param config   dict:  the configuration parameters for this service
        :param workdir   str:  the path to the workspace directory where this
                               service will write its data.  If not provided,
                               the value of the 'working_dir' configuration 
                               parameter will be used.
        :param reviewdir str:  the path to the MIDAS-managed directory for SIPs 
                               in the review state.  If not provided,
                               the value of the 'review_dir' configuration 
                               parameter will be used.
        :param uploaddir str:  the path to the MIDAS-managed directory for SIPs
                               in the upload state.  If not provided,
                               the value of the 'upload_dir' configuration 
                               parameter will be used.
        """
        if not isinstance(config, Mapping):
            raise ValueError("PrePubMetadataService: config argument not a " +
                             "dictionary: " + str(config))
        self.cfg = config

        self.log = log.getChild("mdserv")
        
        if not workdir:
            workdir = self.cfg.get('working_dir')
        if not workdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "working_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir

        if not reviewdir:
            reviewdir = self.cfg.get('review_dir')
        if not reviewdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "review_dir", sys=self)
        if not os.path.isdir(reviewdir):
            raise StateException("MIDAS review directory does not exist as a " +
                                 "directory: " + reviewdir, sys=self)
        self.reviewdir = reviewdir

        if not uploaddir:
            uploaddir = self.cfg.get('upload_dir')
        if not uploaddir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "upload_dir", sys=self)
        if not os.path.isdir(uploaddir):
            raise StateException("MIDAS Upload directory does not exist as a " +
                                 "directory: " + uploaddir, sys=self)
        self.uploaddir = uploaddir

        if not idregdir:
            idregdir = self.cfg.get('id_registry_dir', self.workdir)
        if not os.path.isdir(idregdir):
            raise StateException("ID Registry directory does not exist as a " +
                                 "directory: " + idregdir, sys=self)

        self._minter = self._create_minter(idregdir)

        mimefiles = self.cfg.get('mimetype_files', [])
        if not isinstance(mimefiles, list):
            mimefiles = [mimefiles]
        self.mimetypes = build_mime_type_map(mimefiles)

        self.prepsvc = None
        if 'repo_access' in self.cfg:
            # this service helps pull in information about previously published
            # versions.  
            self.prepsvc = UpdatePrepService(self.cfg['repo_access'])
        else:
            self.log.info("repo_access not configured; no access to published "+
                          "records.")

        # used for validating during updates (via patch_id())
        self._schemadir = None

        # used to convert NERDm to POD
        self._nerd2pod = Res2PODds(pdr.def_jq_libdir, logger=self.log)

        self._midascl = None
        ucfg = self.cfg.get('update', {})
        if ucfg.get('update_to_midas', ucfg.get('midas_service')):
            # set up the client if have the config data to do it unless
            # 'update_to_midas' is False
            self._midascl = midas.MIDASClient(ucfg.get('midas_service', {}),
                                         logger=self.log.getChild('midasclient'))

    def _create_minter(self, parentdir):
        cfg = self.cfg.get('id_minter', {})
        out = PDRMinter(parentdir, cfg)
        if not os.path.exists(out.registry.store):
            self.log.warn("Creating new ID minter")
        return out

    def prepare_metadata_bag(self, id, bagger=None):
        """
        Bag up the metadata from data provided by MIDAS for a given MIDAS ID.  

        :param str id:       the MIDAS identifier for the SIP
        :param MIDASMetadataBagger bagger:  an MIDASMetadataBagger instance to
                             use to prepare the bag.  If not provided, one will
                             be instantiated based on the current configurartion
        :param UpdatePrepper prepper:  an UpdatePrepper instance to use to 
                             initial the bag in the case where the dataset has
                             been published previously.
        """
        if not bagger:
            # this will raise an SIPDirectoryNotFound if there is no
            # submission data from MIDAS
            bagger = self.open_bagger(self.normalize_id(id))
            
        # update the metadata bag with the latest data from MIDAS
        bagger.ensure_preparation()
        return bagger

    def open_bagger(self, id):
        """
        create a MIDASMetadataBagger instance used to create/update the 
        metadata bag.
        """
        cfg = self.cfg.get('bagger', {})
        if 'store_dir' not in cfg and 'store_dir' in self.cfg:
            cfg['store_dir'] = self.cfg['store_dir']
        if 'repo_access' not in cfg and 'repo_access' in self.cfg:
            cfg['repo_access'] = self.cfg['repo_access']
            if 'store_dir' not in cfg['repo_access'] and 'store_dir' in cfg:
                cfg['repo_access']['store_dir'] = cfg['store_dir']
        if not os.path.exists(self.workdir):
            os.mkdir(workdir)
        elif not os.path.isdir(self.workdir):
            raise StateException("Working directory path not a directory: " +
                                 self.workdir)

        bagger = MIDASMetadataBagger(id, self.workdir, self.reviewdir,
                                     self.uploaddir, cfg, self._minter,
                         asyncexamine=self.cfg.get('async_file_examine', True))
        bagger.fileExaminer_autolaunch = False
        return bagger
        

    def make_nerdm_record(self, bagdir, datafiles=None, baseurl=None):
        """
        Given a metadata bag, generate a complete NERDm resource record.  

        This may convert all downloadURLs that go through the data distribution 
        service (i.e. that match that service's base URL) to URLs that go
        through a different server.  This is needed for as-yet unreleased data
        as this service is intended to serve.  Conversion is done either by 
        setting the 'download_base_url' parameter in the configuration or by
        providing a baseurl argument.  The value in both cases is the base URL
        to convert the download URLs to.  The config parameter, 
        'datadist_base_path', indicates the base URL path to look for to 
        recognize data distribution service URLs.  If datafiles is also 
        provided, substitution is restricted to those data files given in 
        that lookup map.

        :param bagdir str:  the directory representing the output bag to serve
                            the metadata from 
        :param datafiles str:  a mapping of filepath property values to 
                            locations to existing data files on disk; 
                            substitution is done for filepaths that match
                            one of the paths in the dictionary.  If None,
                            this requirement is not applied.  
        :param baseurl str: the baseurl to convert downloadURLs to; if None,
                            conversion will not be applied unless 
                            'download_base_url' is set (see above).  
        """
        bag = NISTBag(bagdir)
        out = bag.nerdm_record(merge_annots=True)

        if not baseurl:
            baseurl = self.cfg.get('download_base_url')
        if baseurl and 'components' in out:
            ddspath = self.cfg.get('datadist_base_url', '/od/ds/')
            if ddspath[0] != '/':
                ddspath = '/' + ddspath
            pat = re.compile(r'https?://[\w\.]+(:\d+)?'+ddspath)
            for comp in out['components']:
                # do a download URL substitution if 1) it looks like a
                # distribution service URL, and 2) the file exists in our
                # SIP areas.  
                if 'downloadURL' in comp and pat.search(comp['downloadURL']):
                    # it matches
                    filepath = comp.get('filepath',
                                        pat.sub('',comp['downloadURL']))
                    if datafiles is None or filepath in datafiles:
                        # it exists
                        comp['downloadURL'] = pat.sub(baseurl,
                                                      comp['downloadURL'])

        return out

    def normalize_id(self, id):
        """
        if necesary, transform the given SIP identifier into a normalized 
        form that will be be based to the bagger.  This allows requests 
        to resolve_id() and locate_data_file() to accept several different 
        forms.

        Currently, recognized input SIP IDs include:
          *  old-style, 32+-character MIDAS EDI identifiers
          *  ARK identifiers -- these start with "ark:/"
          *  Path-portion of an ARK identifer -- currently, an ID < 32 chars.
             not starting with "ark:/" is assumed to be of this form.
        """
        if len(id) < 32 and not id.startswith("ark:/"):
            naan = self.cfg.get('id_minter',{}).get('naan', NIST_ARK_NAAN)
            id = "ark:/{}/{}".format(naan, id)
        return id

    def resolve_id(self, id):
        """
        return a full NERDm resource record corresponding to the given 
        MIDAS ID.  
        """
        # this handles preparation for a dataset that has been published before.
        prepper = None

        normid = self.normalize_id(id)
        try:
            
            bagger = self.open_bagger(normid)
            
        except SIPDirectoryNotFound as ex:
            # there is no input data from midas...
            #
            # See if there is a working metadata bag cached
            bagdir = os.path.join(self.workdir, midasid_to_bagname(normid))
            if os.path.exists(bagdir):
                return self.make_nerdm_record(bagdir)
            
            # fall-back to a previously published record, if available
            if self.prepsvc:
                prepper = self.prepsvc.prepper_for(midasid_to_bagname(id),
                                                   log=self.log)
                nerdmfile = prepper.cache_nerdm_rec()
                if nerdmfile:
                    return read_nerd(nerdmfile)

            # Not previously published
            raise IDNotFound(id, "No data found for identifier: "+id)

        # There is a MIDAS submission in progress; create/update the 
        # metadata bag.
        bagger = self.prepare_metadata_bag(id, bagger)
        if bagger.fileExaminer:
            bagger.fileExaminer.launch(stop_logging=True)
        elif bagger.bagbldr:
            bagger.bagbldr.disconnect_logfile()
        return self.make_nerdm_record(bagger.bagdir, bagger.datafiles)

    def patch_id(self, id, frag):
        """
        update the NERDm metadata for the SIP with a given dataset identifier
        and return the full, updated record.  

        This implementation will examine each property in the input dictionary
        (frag) to ensure it is among those configured as updatable and its 
        value is valid.  Values for properties that are not configured as 
        updatable will be ignored.  Invalid values for updatable properties 
        will be cause the whole request to be rejected and an exception is 
        raised.  

        :param id    str:   the ID for the record being updated.
        :param frag dict:   a NERDm resource record fragment containing the 
                              properties to update.  
        :return dict:   the full, updated NERDm record
        :raise IDNotFound:  if the dataset with the given ID is not currently 
                              in an editable state.  
        :raise InvalidRequest:  if any of the updatable data included in the 
                              request is invalid.
        """
        datafiles = None
        try:

            bagger = self.open_bagger(self.normalize_id(id));

            # There is a MIDAS submission in progress; create the metadata bag 
            # and capture any updates from MIDAS
            bagger = self.prepare_metadata_bag(id, bagger)
            if bagger.fileExaminer:
                bagger.fileExaminer.launch(stop_logging=False)
                # bagger.fileExaminer.run()  # sync for testing
            elif bagger.bagbldr:
                bagger.bagbldr.disconnect_logfile()

            datafiles = bagger.datafiles
            bagbldr = bagger.bagbldr

        except SIPDirectoryNotFound as ex:

            # there is no input data from midas...
            #
            if self.cfg.get('update',{}).get('require_midas_sip', True) or \
               not self.prepsvc:
                # in principle, users need not edit data via MIDAS in order
                # to edit via the PDR; this parameter requires it.  
                raise IDNotFound('Dataset with ID is not currently editable');

            # See if there is a working metadata bag cached
            bagname = midasid_to_bagname(id);
            bagdir = os.path.join(self.workdir, bagname)
            if not os.path.exists(bagdir):

                # create a working metadata bag from the previously published
                # data
                prepper = self.prepsvc.prepper_for(bagname, log=self.log)
                                                   
                if not prepper.aip_exists():
                    raise IDNotFound('Dataset with ID not found.');

                if not self.workdir or not os.path.isdir(self.workdir):
                    raise ConfigurationException(bagdir +
                                                 ": working dir not found")
                prepper.create_new_update(bagdir);

            bagbldr = BagBuilder(self.workdir, bagname,
                              self.cfg.get('bagger', {}).get("bag_builder",{}));

        # this will raise an InvalidRequest exception if something wrong is
        # found with the input data
        updates = self._filter_and_check_updates(frag, bagbldr);

        outmsgs = []
        msg = "User-generated metadata updates to path='{0}': {1}"
        for destpath in updates:
            if destpath is not None:
                bagbldr.update_annotations_for(destpath, updates[destpath],
                        message=msg.format(destpath, str(updates[destpath].keys())))

        # save an updated POD and send it to MIDAS
        self.update_pod(updates[None], bagbldr)

        # mergeconv = bagbldr.cfg.get('merge_convention', DEF_MERGE_CONV)
        return self.make_nerdm_record(bagbldr.bagdir, datafiles)

    def _filter_and_check_updates(self, data, bldr):
        # filter out properties that are not updatable; check the values of
        # the remaining.  The returned value is a dictionary mapping filepath
        # values to the associated metadata for that component; the empty string
        # key maps to the resource-level metadata (which can include none-filepath
        # components.

        updatable = self.cfg.get('update',{}).get('updatable_properties',[])
        mergeconv = bldr.cfg.get('merge_convention', DEF_MERGE_CONV)

        def _filter_props(fromdata, todata, parent=''):
            # fromdata and todata are either Mapping objects or lists
            if isinstance(fromdata, list):
                # parent should end with '[]'
                for el in fromdata:
                    if parent in updatable:
                        todata.append(el)
                        continue
                    elif isinstance(el, list):
                        if not any([e.startswith(parent+'[]') for e in updatable]):
                            continue
                        subdata = []
                        _filter_props(el, subdata, parent+'[]')
                        if subdata:
                            todata.append(subdata)
                    elif isinstance(el, Mapping):
                        subdata = OrderedDict()
                        _filter_props(el, subdata, parent)
                        if subdata:
                            todata.append(subdata)
                        
            elif isinstance(fromdata, Mapping):
                for key in fromdata:
                    pkey = parent;
                    if pkey:  pkey += "."
                    pkey += key

                    if pkey in updatable:
                        todata[key] = fromdata[key]

                    elif isinstance(fromdata[key], list):
                        if not any([e.startswith(pkey+'[]') for e in updatable]):
                            continue
                        subdata = []
                        _filter_props(fromdata[key], subdata, pkey+'[]')
                        if subdata:
                            todata[key] = subdata

                    elif isinstance(fromdata[key], Mapping):
                        if not any([e.startswith(pkey+'.') for e in updatable]):
                            continue
                        subdata = OrderedDict()
                        _filter_props(fromdata[key], subdata, pkey)
                        if subdata:
                            todata[key] = subdata

                if pkey!='' and '@id' in fromdata and todata and '@id' not in todata:
                    todata['@id'] = fromdata['@id']

        fltrd = OrderedDict()
        _filter_props(data, fltrd)    # filter out properties you can't edit
        oldnerdm = bldr.bag.nerdm_record(mergeconv)
        newnerdm = self._validate_update(fltrd, oldnerdm, bldr)  # may raise InvalidRequest

        # separate file-based components from main metadata; return parts
        # by destination path.  Every component is now guaranteed to have an
        # '@id' property
        out = OrderedDict()
        if 'components' in fltrd:
            for i in range(len(fltrd['components'])-1, -1, -1):
                cmp = fltrd['components'][i]
                oldcmp = self._item_with_id(oldnerdm['components'], cmp['@id'])
                if 'filepath' in oldcmp:
                    del cmp['@id']  # don't update the ID
                    out[oldcmp['filepath']] = cmp
                    del fltrd['components'][i]
            if len(fltrd['components']) <= 0:
                del fltrd['components']
        out[''] = fltrd
        out[None] = newnerdm
        return out

    def _item_with_id(self, array, id):
        out = [e for e in array if e['@id'] == id]
        return (len(out) > 0 and out[0]) or None

    def _validate_update(self, updata, nerdm, bagbldr):
        # make sure the update produces valid NERDm.  This is done primarily by
        # merging the update with the current metadata and validating the results.
        # Other checks may be encapsulated in this function.  If any of the checks
        # fail, this function will raise a InvalidRequest exception

        if 'components' in updata and 'components' not in nerdm:
            del updata['components']
        if 'components' in updata:
            cmps = updata['components']

            # make sure the component updates correspond to components already
            # defined (as specified by the component's identifier); eliminate
            # those that do not.  
            for i in range(len(cmps)-1, -1, -1):
                if '@id' not in cmps[i] or \
                   not self._item_with_id(nerdm['components'], cmps[i]['@id']):
                    del cmps[i]
            if len(cmps) == 0:
                del updata['components']

        mergeconv = bagbldr.cfg.get('merge_convention', DEF_MERGE_CONV)
        merger = bagbldr.bag._make_merger(mergeconv, "Resource")

        # nerdm = bagbldr.bag.nerdm_record(mergeconv)
        updated = merger.merge(nerdm, updata)

        errs = self._validate_nerdm(updated, bagbldr.cfg.get('validator', {}))
        if len(errs) > 0:
            self.log.error("User update will make record invalid " +
                           "(see INFO details below)")
            self.log.info("metadata patch:\n" +
                           json.dumps(updata,indent=2))
            self.log.info("problems:\n " + "\n ".join(errs))
            raise InvalidRequest("Update makes record invalid", errs)

        return updated

    def _validate_nerdm(self, nerdm, valcfg):
        if not self._schemadir:
            self._schemadir = valcfg.get('nerdm_schema_dir', pdr.def_schema_dir)
            if not self._schemadir:
                raise ConfigurationException("Need to set "+
                                            "bag_builder.validator.nerdm_schema_dir")
            if not os.path.isdir(self._schemadir):
                raise ConfigurationException("nerdm_schema_dir directory does not "+
                                             "exist as a directory: " +
                                             self._schemadir)

        return [str(e) for e in validate_nerdm(nerdm, self._schemadir)]
        
                                           
    def locate_data_file(self, id, filepath):
        """
        return the location and recommended MIME-type for a data file associated
        with the dataset of a given ID.

        :param id       str:   the dataset's identifier
        :param filepath str:   the relative path to the data file within the 
                                 dataset
        :return tuple:  2-element tuple giving the full filepath and recommended
                                 MIME-type
        """
        bagger = self.prepare_metadata_bag(id)
        if filepath not in bagger.datafiles:
            return (None, None)

        loc = bagger.datafiles[filepath]

        # determine the MIME type to send data as
        bag = NISTBag(bagger.bagdir, True)
        dfmd = bag.nerd_metadata_for(filepath, merge_annots=True)
        if 'mediaType' in dfmd and dfmd['mediaType']:
            mt = str(dfmd['mediaType'])
        else:
            mt = self.mimetypes.get(os.path.splitext(loc)[1][1:],
                                    'application/octet-stream')
        return (loc, mt)

    def update_pod(self, nerdm, bagbldr):
        """
        create a POD record from the given NERDm record and determine if a 
        change has been made.  If so, save it to the metadata bag and submit 
        it to MIDAS.  

        :param Mapping nerdm:  The updated NERDm Resource record from which to 
                               get the POD data
        :param BagBuilder bagbldr:  A BagBuilder instance that should be used 
                               to save the POD 
        """
        # sanity check the input NERDm record
        
        # create the updated POD
        newpod = self._nerd2pod.convert_data(nerdm)
        pod4midas = self._pod4midas(newpod)

        # compare it to the currently saved POD record
        oldpod = self._pod4midas(bagbldr.bag.pod_record())
        if newpod.get('_committed', True) and pod4midas == oldpod:
            # nothing's changed
            self.log.debug("No change requiring update to POD detected")
            return

        # attempt to commit it to MIDAS.  If it fails, we'll try to get it
        # next time.
        if self._midascl and not self._submit_to_midas(pod4midas):
            newpod['_committed'] = False

        # save the updated POD to our bag
        bagbldr.add_ds_pod(newpod, convert=False)

    def _pod4midas(self, pod):
        pod = copy.deepcopy(pod)
        # del pod['...']
        
        return pod

    def _submit_to_midas(self, pod):
        # send the POD record to MIDAS via its API

        if not self._midascl:
            raise StateException("No MIDAS service available")

        midasid = pod.get('identifier')
        if not midasid:
            self.log.error("_submit_to_midas(): POD is missing identifier prop!")
            raise ValueError("POD record is missing required 'identifier' field")

        try:
            self._midascl.put_pod(pod, midasid)
        except Exception as ex:
            self.log.error("Failed to commit POD to MIDAS for ediid=%s", midasid)
            self.log.exception(ex)
            return False
                           
        return True

        
class InvalidRequest(PDRServiceException):
    """
    An invalid request was made of the metadata service.  
    """

    def __init__(self, message, reasons=[]):
        """
        create the exception

        :param str message:  the message summarizing what makes the request invalid
        :param reasons:  a list of the specific reasons why the request is invalid
        :type reasons: array of str
        """
        super(InvalidRequest, self).__init__("Metadata Service", http_code=400,
                                             message=message, sys=PublishSystem)
        self.reasons = reasons


