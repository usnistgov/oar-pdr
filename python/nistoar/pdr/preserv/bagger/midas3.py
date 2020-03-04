"""
This module creates bags from MIDAS input data via the SIPBagger interface
according to the "Mark III" specifications.

It specifically provides two SIPBagger implementations: MIDASMetadataBagger and 
MIDASFinalBagger.  The former is used by the pre-publication landing page 
service to prepare the NERDm metadata to be displayed as a data publication
is being previewed as well as by the PDR publication tools that will collect
additional metadata.  The latter implementation is used complete the bagging 
process for the preservation service.

The implementations use the BagBuilder class to populate the output bag.   
"""
import os, errno, logging, re, json, shutil, threading, time
from datetime import datetime
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict, Mapping
from copy import deepcopy

from .base import SIPBagger, moddate_of, checksum_of, read_pod
from .base import sys as _sys
from . import utils as bagutils
from ..bagit.builder import BagBuilder, NERDMD_FILENAME, FILEMD_FILENAME
from ..bagit import NISTBag
from ..bagit.tools import synchronize_enhanced_refs
from ....id import PDRMinter, NIST_ARK_NAAN
from ... import def_merge_etcdir, utils
from .. import (SIPDirectoryError, SIPDirectoryNotFound, AIPValidationError,
                ConfigurationException, StateException, PODError,
                PreservationStateException)
from .... import pdr
from .prepupd import UpdatePrepService
from .datachecker import DataChecker
from nistoar.nerdm.merge import MergerFactory
from nistoar.nerdm.validate import create_validator

# _sys = PreservationSystem()
log = logging.getLogger(_sys.system_abbrev)   \
             .getChild(_sys.subsystem_abbrev) \
             .getChild("midas") 

DEF_MBAG_VERSION = bagutils.DEF_MBAG_VERSION
SUPPORTED_CHECKSUM_ALGS = [ "sha256" ]
DEF_CHECKSUM_ALG = "sha256"
DEF_MERGE_CONV = "initdef"  # For merging MIDAS-generated metadata with
                            # initial defaults
UNSYNCED_FILE = "_unsynced"
DEF_BASE_POD_SCHEMA = "https://data.nist.gov/od/dm/pod-schema/v1.1#"
DEF_POD_DATASET_SCHEMA = DEF_BASE_POD_SCHEMA + "/definitions/Dataset"

# type of update (see determine_update_version())
_NO_UPDATE    = 0
_MDATA_UPDATE = 1
_DATA_UPDATE  = 2

def _midadid_to_dirname(midasid, log=None):
    out = midasid

    if midasid.startswith("ark:/"+NIST_ARK_NAAN+"/"):
        # new ARK-based MIDAS identifiers: chars. after shoulder is the
        # record number and name of directory
        out = re.sub(r'^ark:/\d+/(mds\d+\-)?', '', midasid)
        return out
    
    if len(midasid) > 32:
        # Old UUID-based identifiers:
        # MIDAS drops the first 32 chars. of the ediid for the data
        # directory names
        out = midasid[32:]
    elif log:
        log.warn("Unexpected MIDAS ID (too short): "+midasid)
    return out

def midasid_to_bagname(midasid, log=None):
    out = midasid

    if midasid.startswith("ark:/"):
        out = re.sub(r'/', '_', re.sub(r'^ark:/\d+/', '', midasid))

    return out
        

class MIDASMetadataBagger(SIPBagger):
    """
    This class will ingest metadata provided by MIDAS into a working bag
    that only contains metadata and generated ancillary data.  This data 
    should be sufficient for generating a working landing page.  The 
    metadata is provided in the form of a POD record; this class converts
    it to NERDm and enhances with additional metadata extracted from the 
    available data files the record describes.  

    An instance of this class manages the creation and evolution of a 
    single dataset during its prepublication phase.  It manages this 
    phase by creating and managing a proto-preservation bag that contains 
    only metadata (and possible ancillary data; the data files usually 
    remain in SIP directories).  The lifecycle of the instance goes as 
    follows:

      1. The instance is constructed.  The underlying bag may or may not
         exist already in the working area; either way, construction makes 
         no changes.

      2. The underlying bag is created (if necessary) and readied for updates 
         with a call to prepare().  The bag may already exist from a previous 
         publishing session; otherwise, a new shell is created.  If the 
         dataset was published before, that previous version is used to 
         create a starting version for new version.  An explicit call to 
         prepare() is optional; it will be called automatically by the 
         subsequent steps if necessary.  Additional calls to this function
         will not update underlying bag (i.e. it is indepodent).  

      3. Metadata is updated by calling apply_pod().  This can be called 
         repeatedly as necessary.  The POD record provided to this function
         must be complete; in particular, this record defines exactly which 
         data files should be considered part of the publication.  If in 
         subsequent calls the list of file distributions changes, so does 
         membership of the dataset.  

      4. Metadata are enhanced by calling enhance_metadat().  This should 
         be called after apply_pod().  It will extract metadata from the 
         data files and ensure that the metadata is as complete as possible 
         as a result of the last call to apply_pod().  A hefty part of the 
         work of this method can be done asynchronously via a separate 
         thread.  

    Calling the above functions in a different order will not cause an error; 
    however, the metadata bag, which is used to provide metadata to the landing 
    page service, will be most complete when a call to enhance_metadata() is 
    called after the last call to apply_pod().  
    
    This class can take a configuration dictionary on construction; the 
    following parameters are supported:
    :prop bag_builder dict ({}): a set of parameters to pass to the BagBuilder
                                 object used to populate the output bag (see
                                 BagBuilder class documentation for supported
                                 parameters).
    :prop merge_etc        str:  the path to the directory containing the 
                                 metadata merge rule configurations.  If not
                                 set, the directory will be searched for in 
                                 some possible default locations.
    :prop hard_link_data bool (True):  if True, copy data files into the bag 
                                 using a hard link whenever possible.
    :prop update_by_checksum_size_lim int (0):  a size limit in bytes for which 
                                 files less than this will be checked to see 
                                 if it has changed (not yet implemented).
    :prop component_merge_convention str ("dev"): the merge convention name to 
                                 use to merge MIDAS-provided component metadata
                                 with the PDR's initial component metadata.
    :prop relative_to_indir bool (False):  If True, the output bag directory 
       is expected to be under one of the input directories; this base class
       will then ensure that it has write permission to create the output 
       directory.  If False, the bagger may raise an exception if the 
       requested output bag directory is found within an input SIP directory,
       regardless of whether the process has permission to write there.  
    """
    BGRMD_FILENAME = "__bagger-midas3.json"

    def __init__(self, midasid, workdir, reviewdir, uploaddir=None, config={},
                 minter=None, sipdirname=None):
        """
        Create an SIPBagger to operate on data provided by MIDAS

        :param midasid   str:  the identifier provided by MIDAS, used as the 
                               name of the directory containing the data.
        :param workdir   str:  the path to the directory that can contain the 
                               output bag
        :param reviewdir str:  the path to the directory containing submitted
                               datasets in the review state.
        :param uploaddir str:  the path to the directory containing submitted
                               datasets not yet in the review state.
        :param config   dict:  a dictionary providing configuration parameters
        :param minter IDMinter: a minter to use for minting new identifiers.
        :param sipdirname str: a relative directory name to look for that 
                               represents the SIP's directory.  If not provided,
                               the directory is determined based on the provided
                               MIDAS ID.  
        :param file_examine_mode str:  the mode for examine and extracting file 
                               metadata.  If null or not provided, the default 
                               mode will be "sync", which will cause the file examination
                               to be done synchronously when apply_pod() is called.
                               A value of "async" will trigger asynchronous 
                               examination in a separate thread when apply_pod() 
                               is called; this useful for large SIPs where file 
                               examination can take a while.  A value of "none"
                               will prevent file examination from happening 
                               automatically; one must call fileExaminer.run()
                               (or fileExaminer.launch()) explicitly.
        """
        self.midasid = midasid
        self.name = midasid_to_bagname(midasid)
        self.state = 'upload'
        self._indirs = []

        usenm = self.name
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        self.log = log.getChild(usenm)
        
        # ensure we have at least one readable input directory
        indirname = sipdirname
        if not indirname:
            indirname = _midadid_to_dirname(midasid, log)

        for dir in (reviewdir, uploaddir):
            if not dir:
                continue
            indir = os.path.join(dir, indirname)
            if os.path.exists(indir):
                if not os.path.isdir(indir):
                    raise SIPDirectoryError(indir, "not a directory", sys=self)
                if not os.access(indir, os.R_OK|os.X_OK):
                    raise SIPDirectoryError(indir, "lacking read/cd permission",
                                            sys=self)
                self._indirs.append(indir)
                if reviewdir and indir.startswith(reviewdir):
                    self.state = 'review'
                self.log.debug("Found input dir: %s", indir)
            else:
                self.log.debug("Candidate dir does not exist: %s", indir)    

        if not self._indirs:
            raise SIPDirectoryNotFound(msg="No input directories available",
                                       sys=self)
        
        super(MIDASMetadataBagger, self).__init__(workdir, config)

        # If None, we'll create a ID minter if we need one (in self._mint_id)
        self._minter = minter

        self.bagbldr = BagBuilder(self.bagparent, self.name,
                                  self.cfg.get('bag_builder', {}),
                                  logger=self.log)
        mergeetc = self.cfg.get('merge_etc', def_merge_etcdir)
        if not mergeetc:
            raise StateException("Unable to locate the merge configuration "+
                                 "directory")
        self._merger_factory = MergerFactory(mergeetc)

        self.schemadir = self.cfg.get('nerdm_schema_dir', pdr.def_schema_dir)
        self.hardlinkdata = self.cfg.get('hard_link_data', True)
        self.resmd = None
        self.prepared = False

        # this will contain a mapping of files that currently appear in the
        # MIDAS submission area; the keys are filepath values (in the NERDm
        # sense--i.e. relative to the dataset root), and values are the full
        # path to its location on disk.
        self.datafiles = None

        # A PrepService is used to cache the AIP metadata from the last publication
        # of this dataset
        self.prepsvc = None
        if 'repo_access' in self.cfg:
            # support for updates requires access to the distribution and
            # rmm services
            self.prepsvc = UpdatePrepService(self.cfg['repo_access'])
        else:
            self.log.warning("repo_access not configured; can't support updates!")

        # The file-examiner allows for ansynchronous examination of the data files
        self.fileExaminer = self._AsyncFileExaminer.getFor(self)
#        self.fileExaminer_mode = "none"
#        if examine_file_mode:
#            self.fileExaminer_mode = examine_file_mode

        self.ensure_bag_parent_dir()

    def _mint_id(self, ediid):
        if not self._minter:
            cfg = self.cfg.get('id_minter', {})
            self._minter = PDRMinter(self.bagparent, cfg)
            if not os.path.exists(self._minter.registry.store):
                log.warning("Creating new ID minter for bag, "+self.name)

        seedkey = self.cfg.get('id_minter', {}).get('ediid_data_key', 'ediid')
        return self._minter.mint({ seedkey: ediid })

    @property
    def bagdir(self):
        """
        The path to the output bag directory.
        """
        return self.bagbldr.bagdir

    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """
        raise PODError("POD files not expected in midas3 SIPs: use apply_pod()")

    def _mark_filepath_unsynced(self, filepath):
        self.bagbldr.ensure_bagdir()
        mdir = os.path.dirname(self.bagbldr.bag.nerd_file_for(filepath))
        if os.path.isdir(mdir):
            semaphore = os.path.join(mdir, UNSYNCED_FILE)
            if not os.path.exists(semaphore):
                # create 0-length the file
                with open(semaphore, 'a') as fd:
                    pass
                
    def _mark_filepath_synced(self, filepath):
        self.bagbldr.ensure_bagdir()
        mdir = os.path.dirname(self.bagbldr.bag.nerd_file_for(filepath))
        if os.path.isdir(mdir):
            semaphore = os.path.join(mdir, UNSYNCED_FILE)
            if os.path.exists(semaphore):
                os.remove(semaphore)
                
    def _mark_comps_unsynced(self, comps):
        for c in comps:
            if 'filepath' in c:
                self._mark_filepath_unsynced(c['filepath'])

    def _clear_all_unsynced_marks(self):
        if not self.bagbldr.bagdir:
            return
        mdir = os.path.join(self.bagbldr.bagdir, "metadata")
        if not os.path.exists(mdir):
            return
        for base, subdirs, files in os.walk(mdir):
            if UNSYNCED_FILE in files:
                semaphore = os.path.join(base, UNSYNCED_FILE)
                if os.path.exists(semaphore):
                    os.remove(semaphore)

    def registered_files(self):
        """
        return a mapping of component filepaths to actual filesystem paths
        to the corresponding file on disk.  To be included in the map, the 
        component must be registered in the NERDm metadata (and be included 
        in the last applied POD file), have a downloadURL that based in the PDR's
        data distribution service, and there is a corresponding file in either 
        the SIP upload directory or review directory.  

        :return dict: a mapping of logical filepaths relative to the dataset 
                      root to full paths to the input data file for all data
                      files found in the SIP.
        """
        out = OrderedDict()
        if not self.resmd:
            return out
        
        for comp in self.resmd.get('components', []):
            if 'filepath' not in comp or \
               any([":Subcollection" in t for t in comp.get('@type',[])]):
                continue
            srcpath = self.find_source_file_for(comp['filepath'])
            if srcpath:
                out[comp['filepath']] = srcpath

        return out

    def available_files(self):
        """
        get a list of the data files available in the SIP input directories
        (including hash files).  Some may not be currently part of the 
        collection; such files must be listed as distributions in the 
        POD record.

        :return dict: a mapping of logical filepaths relative to the dataset 
                      root to full paths to the input data file for all data
                      files found in the SIP.
        """
        datafiles = {}

        # check each of the possible locations; locations found later take
        # precedence
        for root in self._indirs:
            root = root.rstrip('/')
            for dir, subdirs, files in os.walk(root):
                reldir = dir[len(root)+1:]
                for f in files:
                    # don't descend into subdirectories with ignorable names
                    for d in range(len(subdirs)-1, -1, -1):
                        if subdirs[d].startswith('.') or \
                           subdirs[d].startswith('_'):
                            del subdirs[d]
                    
                    if f.startswith('.') or f.startswith('_'):
                        # skip dot-files and pod files written by MIDAS
                        continue

                    datafiles[os.path.join(reldir, f)] = os.path.join(dir, f)

        return datafiles

    def _merger_for(self, convention, objtype):
        return self._merger_factory.make_merger(convention, objtype)

    def ensure_preparation(self, nodata=True):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP, ready for POD-based updates.

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.  In this implementation, the 
                            default is True.
        """
        self.ensure_base_bag()
        self.ensure_res_metadata()

    def ensure_base_bag(self):
        """
        Establish an initial working bag.  If a working bag already exists, it 
        will be used as is.  Otherwise, this method will check to see if a 
        resource with with the same MIDAS identifier has been published before;
        if so, its metadata (with version information updated) will be used to 
        create the initial bag.  If not, it is assumed that this is a new 
        resource that has never been requested; a new bag directory will be 
        created and an AIP identifier will be assigned to it.  

        :return bool:  True if the initial state requires that the SIP-POD
                       be used to refresh the resource metadata
        """
        
        if os.path.exists(self.bagdir):
            # We already have an established working bag
            if not self.prepared:
                self.log.info("Refreshing previously established working bag")
            self.prepared = True
            return False

        elif self.prepsvc:
            self.log.debug("Looking for previously published version of bag")

            prepper = self.prepsvc.prepper_for(self.name,
                                               log=self.log.getChild("prepper"))

            if prepper.create_new_update(self.bagdir):
                self.log.info("Working bag initialized with metadata from previous "
                              "publication.")

        if not os.path.exists(self.bagdir):
            self.bagbldr.ensure_bag_structure()

            if self.midasid.startswith("ark:/"+NIST_ARK_NAAN+"/"):
                # new-style EDI ID is a NIST ARK identifier; use it as our SIP id
                id = self.midasid
            else:
                # support deprecated 32+-character EDI ID: convert to ARK ID
                log.warn("Minting ID for (deprecated) Non-ARK EDI-ID: "+
                         self.name)
                id = self._mint_id(self.midasid)

            self.bagbldr.assign_id( id )

            # set some minimal metadata
            updmd = OrderedDict([('ediid', self.midasid), ('version', "1.0.0")])
            self.bagbldr.update_metadata_for("", updmd)

            self.resmd = None  # set by ensure_res_metadata()

        return True
                
    def ensure_res_metadata(self):
        """
        ensure that at least there is minimal (though not neccessarily fully 
        compliant) metadata prior to introduction of POD metadata.  At the 
        moment, this just ensures the EDI-ID and an initial version.  (The @id 
        is already set by ensure_base_bag().) 
        """
        self.ensure_base_bag();

        resmd = self.bagbldr.bag.nerd_metadata_for("", True);
        updmd = OrderedDict();
        if 'ediid' not in resmd:
            updmd['ediid'] = self.midasid

        if updmd:
            self.bagbldr.update_metadata_for("", updmd)

        self.resmd = self.bagbldr.bag.nerdm_record(True);

        # ensure an initial version
        if 'version' not in self.resmd:
            self.resmd['version'] = "1.0.0"
            self.bagbldr.update_annotations_for('',
                                            {'version': self.resmd["version"]})

        self.datafiles = self.registered_files()
        

    def apply_pod(self, pod, validate=True, force=False):
        """
        update the SIP with an updated POD record.  This will look for changes to 
        the POD compared to the one currently cached to the bag and applies those 
        changes to the NERDm metadata.  If no changes are detected, the POD record 
        is ignored.  

        :param dict|string pod:  the new POD record to sync to.  If the value is 
                                 a string, it is taken as a local file path to the 
                                 JSON-serialized POD record.
        :param bool   validate:  if True (default) validate that the incoming POD 
                                 is a compliant POD document; if False, the POD 
                                 record is assumed to be compliant.
        """
        if not isinstance(pod, (str, unicode, Mapping)):
            raise NERDTypeError("dict", type(pod), "POD Dataset")
        self.ensure_base_bag()

        podfile = None
        if not isinstance(pod, Mapping):
            podfile = pod
            pod = read_pod(podfile)

        # validate the given POD (raises exception if not valid)
        if validate:
            if self.schemadir:
                valid8r = create_validator(self.schemadir, pod)
                valid8r.validate(pod, schemauri=DEF_POD_DATASET_SCHEMA,
                                 strict=True, raiseex=True)
            else:
                self.log.warning("Unable to validate submitted POD data")

        # determine if the pod record has changed
        oldpod = self.bagbldr.bag.pod_record()
        if not force and pod == oldpod:
            self.log.info("No change detected in given POD; ignoring")
            return

        # updated will contain the filepaths for components that were updated
        updated = self.bagbldr.update_from_pod(pod, True, True)

        # we're done; update the cached NERDm metadata and the data file map
        if not self.resmd or updated['updated'] or updated['added'] or updated['deleted']:
            self.resmd = self.bagbldr.bag.nerdm_record(True)
            self.datafiles = self.registered_files()
      
    def _get_ejs_flavor(self, data):
        """
        return the prefix (or a default) used to identify meta-properties
        used for (ejsonschema-based) validation.
        """
        for prop in "schema extensionSchemas".split():
            mpfxs = [k[0] for k in data.keys() if k[1:] == prop and k[0] in "_$"]
            if len(mpfxs) > 0:
                return mpfxs[0]
        return "_"
        

    def ensure_data_files(self, nodata=True, force=False, examine="async"):
        """
        ensure that all data files have up-to-date descriptions and are
        (if nodata=False) copied into the bag.  Only process files that 
        are described in the POD/NERDm record.  

        :param bool nodata:  if True (default), don't copy the actual data files 
                             to the output bag.  False will copy the files.
        :param bool force:   if False (default), the data files will be examined
                             for additional metadata only if the source data 
                             file is newer than the corresponding metadata file 
                             in the output bag.  
        :param str|bool examine:  a flag indicating whether and how to examine the 
                             individual files for metadata to extract.  A value of 
                             "async" will cause the files to be examined asynchronously
                             in a separate thread.  A value of "sync" or True will 
                             cause the examination to happen synchronously within this
                             function call.  A value of False or None will prevent 
                             files from being examined synchronously; files require
                             examination (because they have been updated since the 
                             last examination) will still be loaded into the 
                             fileExaminer.  
        """
        if not self.resmd:
            self.ensure_res_metadata()

        # we will determine if any of the submitted data files have changed since 
        # we last checked; get that last timestamp and update it.
        now = time.time()
        bmd = self.baggermd_for("")
        lasttime = bmd.get('last_file_examine', 0.0)
        self.update_bagger_metadata_for("", {
            'last_file_examine': now,
            'last_file_examine_datetime': datetime.fromtimestamp(now).isoformat(' ')
        })

        for destpath, srcpath in self.datafiles.items():
            fforce = force
            if not fforce:
                dfmd = self.bagbldr.bag.nerd_metadata_for(destpath)
                fforce = 'size' not in dfmd or 'checksum' not in dfmd

            if srcpath and moddate_of(srcpath) > lasttime:
                fforce = True
                self.fileExaminer.add(srcpath, destpath)

            self.ensure_file_metadata(srcpath, destpath, fforce, False)

            if not nodata:
                self.bagbldr.add_data_file(destpath, srcpath, False,
                                           self.hardlinkdata)

        # re-examine the files that have changed.
        if examine == "async":
            self.log.info("Launching file examiner thread")
            self.fileExaminer.launch()
        elif examine:
            # do it now!
            self.log.info("Running file examiner synchronously")
            self.fileExaminer.run()
        else:
            self._check_checksum_files()

    def _select_updated_since(self, pod, since):
        #DEPRECATED
        # This finds the data files listed as distributions in the given pod
        # and determines if any have been updated since the given date.  If 
        # anyone has, it is added to the fileExaminer
        
        ddspath = self.cfg.get('bagger',{}).get('datadist_base_url', '/od/ds/')
        if ddspath[0] != '/':
            ddspath = '/' + ddspath
        pat = re.compile(r'https?://[\w\.]+(:\d+)?'+ddspath)

        for dist in pod.get('distribution',[]):
            filepath = None
            if 'downloadURL' not in dist and pat.search(dist['downloadURL']):
                filepath = pat.sub('', dist['downloadURL'])

            if filepath:
                srcpath = self.find_source_file_for(filepath)
                if srcpath and moddate_of(srcpath) > since:
                    self.fileExaminer.add(srcpath, filepath)
                    out.append(filepath)

        return out

    def enhance_metadata(self, nodata=True, force=False, examine="sync"):
        """
        ensure that we have complete and updated metadata after applying a
        POD description.  This will look for updates to the submitted data
        file and, if necessary, extract updated metadata from the files.
        It will also ensure that all the subcollections are described with 
        metadata.  
        """
        if self.cfg.get('enrich_refs', False):
            self.ensure_enhanced_references()
        self.ensure_subcoll_metadata()
        self.ensure_data_files(nodata, force, examine)  # may be partially asynhronous

    def ensure_enhanced_references(self):
        """
        examine the references and, if necessary, enhance their descriptions from 
        metadata obtained by resolving their DOI metadata.
        """
        self.ensure_preparation()
        if 'references' in self.resmd:
            self.log.debug("Will enrich references as able")
            synchronize_enhanced_refs(self.bagbldr, config=self.cfg.get('doi_resolver'),
                                      log=self.log)
            nerd = self.bagbldr.bag.nerd_metadata_for("", True)
            self.resmd['references'] = nerd.get('references',[])

    def find_source_file_for(self, filepath):
        """
        return the location in the SIP of the source data file corresponding 
        to the given filepath (representing its target location in the output
        bag).  None is returned if the filepath cannot be found in any of the
        SIP locations.
        """
        for sipdir in reversed(self._indirs):
            srcpath = os.path.join(sipdir, filepath)
            if os.path.isfile(srcpath):
                return srcpath
        return None

    def ensure_subcoll_metadata(self):
        if not self.datafiles:
            self.ensure_res_metadata()

        colls = set()
        for filepath in self.datafiles:
            collpath = os.path.dirname(filepath)
            if collpath and collpath not in colls:
                collnerd = self.bagbldr.bag.nerd_file_for(collpath)
                filenerd = self.bagbldr.bag.nerd_file_for(filepath)
                if not os.path.exists(collnerd) or \
                   (os.path.exists(filenerd) and 
                    moddate_of(collnerd) < moddate_of(filenerd)):
                      self.log.debug("Ensuring metadata for collection: %s", collpath)
                      self.bagbldr.define_component(collpath, "Subcollection")
                      colls.add(collpath)


    def ensure_file_metadata(self, inpath, destpath, force=False, examine=False):
        """
        examine the given file and update the file metadata if necessary.

        If the file has a file modication time later than the corresponding 
        file metadata (if the latter exists), the metadata will be updated.  
        For smaller files, the files checksum will be checked as well:  if the 
        checksum is different from the previously record one, the file metadata
        will be updated.  

        :param inpath str:     the path to the input copy of the data file 
                                  relative to the SIP directory root.
        :param destpath str:   the path intended for this file in the output
                                  data collection
        """
        self.bagbldr.ensure_bagdir()
        nerdfile = self.bagbldr.bag.nerd_file_for(destpath)

        update = False
        if not os.path.exists(nerdfile):
            update = True
            self.log.info("Initializing metadata for datafile, %s", destpath)
        elif force or os.path.exists(os.path.join(os.path.dirname(nerdfile),
                                                  UNSYNCED_FILE)):
            # we marked this earlier that an update is recommended
            update = True
            self.log.debug("datafile, %s, requires update to metadata", destpath)

        if update:
            md = self.bagbldr.describe_data_file(inpath, destpath, examine)

            if self.fileExaminer:
                md["_status"] = "in progress"
                
                # the file examiner will calculate the file's checksum;
                # for now though, see if there is an associated checksum file 
                # provided by midas.  
                # (TODO: don't hard-wire checksum algorithm)
                csfile = inpath+".sha256"
                if os.path.exists(csfile):
                    try:
                        with open(csfile) as fd:
                            cs = fd.readline().split()[0]
                        self.bagbldr._add_checksum(cs, md)
                    except Exception as ex:
                        self.log.warn(csfile +
                                 ": trouble reading provided checksum file")

            # now save the metadata 
            md = self.bagbldr.update_metadata_for(destpath, md)
            if not self.fileExaminer:
                self._mark_filepath_synced(destpath)

            # update self.resmd; this is cheaper than recreating it from scratch
            # with nerdm_record()
            if self.resmd:
                cmps = self.resmd.get('components',[])
                for i in range(len(cmps)):
                    if md['@id'] == cmps[i]['@id']:
                        cmps[i] = md
                        break
                if i >= len(cmps):
                    if len(cmps) == 0:
                        self.resmd['components'] = [md]
                    else:
                        self.resmd['components'].append(md)


    def _check_checksum_files(self):
        # This file will look all of the files that have been identified as
        # ChecksumFiles to see if the value they contain matches the value
        # stored in the metadata for the datafile it is associated with.  If
        # they do not match, the valid metadata flag for the checksum file
        # will be set to false.
        for comp in self.resmd.get('components', []):
            if 'filepath' not in comp or \
               not any([":ChecksumFile" in t for t in comp.get('@type',[])]):
                continue

            srcpath = self.find_source_file_for(comp['filepath'])
            if srcpath:
                # read the checksum stored in the file
                try:
                    with open(srcpath) as fd:
                        cs = fd.readline().split()[0]
                except Exception as ex:
                    self.log.warn(comp['filepath']+
                             ": unexpected contents in checksum file (%s)" % 
                             str(ex))
                    cs = False   # this will be flagged invalid

                # this data file is a checksum file
                described = os.path.splitext(comp['filepath'])[0]   # default
                described = comp.get("describes","cmps/"+described)[5:]
                if os.path.isfile(self.bagbldr.bag.nerd_file_for(described)):
                    nerd = self.bagbldr.bag.nerd_metadata_for(described, True)

                    valid = nerd.get('checksum',{}).get('hash','') == cs
                    if not valid:
                        self.log.warn(nerd['filepath']+
                                 ": hash value in file looks invalid")
                    else:
                        self.log.debug(nerd['filepath']+": hash value looks valid")
                    comp['valid'] = bool(valid)
                    self.bagbldr.update_metadata_for(comp['filepath'],
                                                     {'valid': comp['valid']})


    class _AsyncFileExaminer():
        """
        a class for extracting metadata from files asynchronously.  The files 
        to be examined should be added via the add() function.  When all 
        desired files have been added, executing launch() will launch the 
        examination in a separate thread. 
        """

        # maps bag directory to a fileExaminer instance
        examiners = OrderedDict()

        #threads = OrderedDict()

        def __init__(self, bagger):
            self.bagger = bagger
            if not self.bagger.bagdir:
                raise ValueError("Bagger not prepped: no bag root dir set")
            self.id = self.bagger.bagdir
            self.files = OrderedDict()
            self.thread = None
            self.async = True
            self.stop_logging = False

        @classmethod
        def getFor(cls, bagger):
            if bagger.bagdir in cls.examiners:
                return cls.examiners[bagger.bagdir]
            out = cls(bagger)
            cls.examiners[out.id] = out
            return out

        def add(self, location, filepath):
            self.files[filepath] = location

        def _unregister(self):
            if self.id in self.examiners:
                self.examiners.pop(self.id, None)
        def __del__(self):
            self._unregister()

        def _prep(self, forasync=True):
            if self.running():
                log.debug("File examiner thread is still running")
                return False
            self.async = forasync
            self.thread = self._Thread(self)
            return True

        def running(self):
            return self.thread and (not self.async or self.thread.is_alive())

        def launch(self, stop_logging=False):
            # run in new thread
            if self._prep():
                self.stop_logging = stop_logging
                self.thread.start()

        def run(self):
            # run in this thread
            if self._prep(False):
                self.stop_logging = False
                self.thread.run()

        def finish(self):
            if self.stop_logging:
                self.bagger.bagbldr.disconnect_logfile()
            if not self.async:
                self.async = True

        def waitForCompletion(self, timeout):
            if self.running() and self.thread is not threading.current_thread():
                try:
                    self.thread.join(timeout)
                except RuntimeError as ex:
                    log.warn("Skipping wait for examiner thread, "+self.thread.getName()+
                             ", for deadlock danger")
                    return False
                if self.thread.is_alive():
                    log.warn("Thread waiting timed out: "+str(thrd))
                    return False
            return True

        def examine_next(self):
            filepath, location = self.files.popitem()
            try:
                md = self.bagger.bagbldr.bag.nerd_metadata_for(filepath)

                # if the metadata has been set, determine the conponent type
                ct = md.get('@type')
                if ct:
                    ct = re.sub(r'^[^:]*:', '', ct[0])
            
                md = self.bagger.bagbldr.describe_data_file(location, filepath,
                                                            True, ct)
                if '_status' in md:
                    md['_status'] = "updated"

                # it's possible that this file has been deleted while this
                # thread was launched; make sure it still exists
                if not self.bagger.bagbldr.bag.comp_exists(filepath):
                    self.log.warning("Examiner thread detected that component no " +
                                     "longer exists; skipping update for bag="+
                                     self.bagger.name+", path="+filepath)
                    return

                md = self.bagger.bagbldr.update_metadata_for(filepath, md, ct,
                                   "async metadata update for file, "+filepath)
                if '_status' in md:
                    del md['_status']
                    self.bagger.bagbldr.replace_metadata_for(filepath, md, '')
                self.bagger._mark_filepath_synced(filepath)

            except Exception as ex:
                log.error("%s: Failed to extract file metadata: %s"
                          % (location, str(ex)))

        @classmethod
        def wait_for_all(cls, timeout=10):
            log.info("Waiting for file examiner threads to finish")
            done = len(cls.examiners.keys())
            for exmnr in cls.examiners.values():
                if not exmnr.thread:
                    continue
                if exmnr.thread is threading.current_thread():
                    continue
                if exmnr.thread and not exmnr.thread.getName().startswith("Examiner-"):
                    continue
                try:
                    exmnr.thread.join(timeout)
                    if thrd.is_alive():
                        log.warn("Thread waiting timed out: "+str(thrd))
                    else:
                        done -= 1
                except RuntimeError as ex:
                    log.warn("Skipping wait for thread, "+str(thrd)+
                             ", for deadlock danger")
            return len(done) == 0

        class _Thread(threading.Thread):
            def __init__(self, exmnr):
                super(MIDASMetadataBagger._AsyncFileExaminer._Thread, self). \
                    __init__(name="Examiner-"+exmnr.id)
                self.exif = exmnr
            def run(self):
                # time.sleep(0.1)
                while self.exif.files:
                    self.exif.examine_next()
                self.exif.finish()
        

