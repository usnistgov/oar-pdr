"""
This module creates bags from MIDAS input data via the SIPBagger interface
according to the "Mark III" specifications.

It specifically provides two SIPBagger implementations: MIDAS3MetadataBagger and 
PreservationBagger.  The former is used by the PDR pubserver (driven by MIDAS)
to create a metadata bag from which a pre-publication landing page is constructed.
The latter will combine the metadata bag with the user-uploaded data to produce the
final (unserialized) bag for preservation.  (See the documentation for 
nistoar.pdr.preserv.service, particularly the siphandler sub-module, for triggering,
serializing, and storing of preservation bags.)

The implementations use the BagBuilder class to populate the output bag.   
"""
import os, errno, logging, re, json, shutil, threading, time, urllib
from datetime import datetime
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict, Mapping
from copy import deepcopy

from .base import SIPBagger, moddate_of, checksum_of, read_pod, read_json
from .base import sys as _sys
from . import utils as bagutils
from ..bagit.builder import BagBuilder, NERDMD_FILENAME, FILEMD_FILENAME
from ..bagit import NISTBag
from ..bagit.tools import synchronize_enhanced_refs
from ....id import PDRMinter
from ....nerdm import utils as nerdutils
from ... import def_merge_etcdir, utils, ARK_NAAN, PDR_PUBLIC_SERVER
from .. import (SIPDirectoryError, SIPDirectoryNotFound, AIPValidationError,
                ConfigurationException, StateException, PODError,
                PreservationStateError)
from .... import pdr
from .prepupd import UpdatePrepService
from .datachecker import DataChecker
from nistoar.nerdm.merge import MergerFactory
from nistoar.nerdm.validate import create_validator

# _sys = PreservationSystem()
log = logging.getLogger(_sys.system_abbrev)   \
             .getChild(_sys.subsystem_abbrev) \
             .getChild("midas3") 

DEF_MBAG_VERSION = bagutils.DEF_MBAG_VERSION
SUPPORTED_CHECKSUM_ALGS = [ "sha256" ]
DEF_CHECKSUM_ALG = "sha256"
DEF_MERGE_CONV = "initdef"  # For merging MIDAS-generated metadata with
                            # initial defaults
UNSYNCED_FILE = "_unsynced"
DEF_BASE_POD_SCHEMA = "https://data.nist.gov/od/dm/pod-schema/v1.1#"
DEF_POD_DATASET_SCHEMA = DEF_BASE_POD_SCHEMA + "/definitions/Dataset"
ark_naan = ARK_NAAN

# type of update (see determine_update_version())
_NO_UPDATE    = 0
_MDATA_UPDATE = 1
_DATA_UPDATE  = 2

_arkid_pfx_re = re.compile("^ark:/\d+/")

_minimal_pod = OrderedDict([
    ("title", ""),
    ("description", ""),
    ("publisher", OrderedDict([
        ("name", "National Institute of Standards and Technology"),
        ("@type", "org:Organization")
    ])),
    ("accessLevel", "public"),
    ("bureauCode", []),
    ("programCode", [])
])

def _midadid_to_dirname(midasid, log=None):
    out = midasid

    if midasid.startswith("ark:/"+ark_naan+"/"):
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

class MIDASSIP(object):
    """
    This class represents the Submission Information Package (SIP) provided by MIDAS as
    input to the bagging process.  It's main function is to provide the location of data 
    files given an inventory provided by a POD (or NERDm) record.
    """

    @classmethod
    def fromPOD(cls, podrec, reviewdir, uploaddir=None):
        """
        create an MIDASSIP instance from a given POD record.  This will extract the 
        MIDAS EDI-ID from the record and use it to determine the directories containing 
        submitted data.
        :param podrec  str|dict:  either the POD record data (as a dict) or a filepath to 
                                  the POD JSON file
        :param reviewdir    str:  the path to the parent directory containing submission 
                                  directories for data in the review state.
        :param uploaddir    str:  the path to the parent directory containing submission
                                  directories for data not yet in the review state.
        """
        if isinstance(podrec, Mapping):
            pod = podrec
        else:
            pod = read_json(podrec)
        midasid = pod.get('identifier')
        if not midasid:
            msg = "Missing required identifier property from POD"
            if not isinstance(podrec, Mapping):
                msg += " ("+podrec+")"
            raise PODError(msg)

        recnum = _midadid_to_dirname(midasid)
        revdir = os.path.join(reviewdir, recnum)
        upldir = None
        if uploaddir:
            upldir = os.path.join(uploaddir, recnum)
            if not os.path.isdir(upldir):
                upldir = None

        return cls(midasid, revdir, upldir, pod)

    @classmethod
    def fromNERD(cls, nerdrec, reviewdir, uploaddir=None):
        """
        create an MIDASSIP instance from a given NERDm record.  This will extract the 
        MIDAS EDI-ID from the record and use it to determine the directories containing 
        submitted data.
        :param nerdrec str|dict:  either the NERDm record data (as a dict) or a filepath to 
                                  the NERDm JSON file
        :param reviewdir    str:  the path to the parent directory containing submission 
                                  directories for data in the review state.
        :param uploaddir    str:  the path to the parent directory containing submission
                                  directories for data not yet in the review state.
        """
        if isinstance(nerdrec, Mapping):
            nerd = nerdrec
        else:
            nerd = read_json(nerdrec)
        midasid = nerd.get('ediid')
        if not midasid:
            msg = "Missing required ediid property from NERDm record"
            if not isinstance(nerdrec, Mapping):
                msg += " ("+nerdrec+")"
            raise NERDError(msg)

        recnum = _midadid_to_dirname(midasid)
        revdir = os.path.join(reviewdir, recnum)
        upldir = os.path.join(uploaddir, recnum)
        if not os.path.isdir(upldir):
            upldir = None

        return cls(midasid, revdir, upldir, nerdrec=nerd)

    def __init__(self, midasid, reviewdir, uploaddir=None, podrec=None, nerdrec=None):
        """
        :param midasid      str:  the identifier provided by MIDAS, used as the 
                                  name of the directory containing the data.
        :param reviewdir    str:  the path to the directory containing submitted
                                  datasets in the review state.
        :param uploaddir    str:  the path to the directory containing submitted
                                  datasets not yet in the review state.
        :param podrec  str|dict:  either the POD record data (as a dict) or a filepath to 
                                  the POD JSON file
        :param nerdrec str|dict:  either the NERDm record data (as a dict) or a filepath to 
                                  the NERDm JSON file
        """
        self.midasid = midasid

        # ensure we have at least one readable input directory
        self.revdatadir = self._check_input_datadir(reviewdir)
        self.upldatadir = self._check_input_datadir(uploaddir)

        self._indirs = []
        if self.revdatadir:
            self._indirs.append(self.revdatadir)
        if self.upldatadir:
            self._indirs.append(self.upldatadir)

        if not self._indirs:
            if log.isEnabledFor(logging.DEBUG):
                log.warn("No input directories available for midasid=%s", midasid)
                log.debug("Input dirs:\n  %s\n  %s", str(self.revdatadir), str(self.upldatadir))
            raise SIPDirectoryNotFound(msg="No input directories available", sys=self)

        self.nerd = nerdrec
        self.pod  = podrec

    @property
    def input_dirs(self):
        return tuple(self._indirs)

    def get_ediid(self):
        """
        open the available metadata file and return the EDI-ID.  None is returned 
        if the ID can not be determined (because no metadata files are available).
        """
        id = self._pod_rec().get('identifier')
        if not id:
            id = self._nerdm_rec().get('ediid')
        return id
        
    def get_pdrid(self):
        """
        open the available NERDm metadata file and return the current PDR-local identifier.  
        None is returned if the ID can not be determined (because no metadata files are 
        available).
        """
        return self._nerdm_rec().get('identifier')
        
    def _check_input_datadir(self, indir):
        if not indir:
            return None
        if os.path.exists(indir):
            if not os.path.isdir(indir):
                raise SIPDirectoryError(indir, "not a directory", sys=self)
            if not os.access(indir, os.R_OK|os.X_OK):
                raise SIPDirectoryError(indir, "lacking read/cd permission",
                                            sys=self)

            log.debug("Found input dir for %s: %s", self.midasid, indir)
            return indir

        log.debug("Candidate dir for %s does not exist: %s", self.midasid, indir)
        return None

    def _pod_rec(self):
        if not self.pod:
            return OrderedDict([("distribution", [])])
        
        if isinstance(self.pod, Mapping):
            return self.pod
        
        return utils.read_json(self.pod)

    def _nerdm_rec(self):
        if not self.nerd:
            return OrderedDict([("components", [])])
        
        if isinstance(self.nerd, Mapping):
            return self.nerd
        
        return utils.read_json(self.nerd)

    def list_registered_filepaths(self, prefer_pod=False):
        """
        return a list of the file paths that registered as being part of this dataset.  
        A file path is considered registered if it is listed as a member in the metadata.
        By default, the attached NERDm record is the source of the member list; otherwise,
        this attached POD record is the source.  If neither are available, this function
        returns an empty list.
        :param bool prefer_pod:   if True, the pod file is treated as the source of this 
                                  information, even if there exists an attached NERDm 
                                  record.  
        """
        if self.nerd and not prefer_pod:
            return self._filepaths_in_nerd()

        return self._filepaths_in_pod()

    def _filepaths_in_nerd(self):
        if not self.nerd:
            return []

        nerd = self._nerdm_rec()
        return [c['filepath'] for c in nerd['components']
                              if 'filepath' in c and
                                 any([t.endswith(":DataFile") or t.endswith(":ChecksumFile")
                                      for t in c['@type']])]

    _distsvcurl = re.compile("https?://[\w\.:]+/od/ds/(ark:/\w+/)?[\w\-]+/")
    def _filepaths_in_pod(self):
        if not self.pod:
            return []

        pod = self._pod_rec()

        return [self._distsvcurl.sub('', urllib.unquote(d['downloadURL']))
                for d in pod.get('distribution',[]) if 'downloadURL' in d]
                

    def registered_files(self, prefer_pod=False):
        """
        return a mapping of component filepaths to actual filesystem paths
        to the corresponding file on disk.  To be included in the map, the 
        component must be registered in the NERDm metadata (and be included 
        in the last applied POD file), have a downloadURL that is based in 
        the PDR's data distribution service, and there is a corresponding 
        file in either the SIP upload directory or review directory.  

        :return dict: a mapping of logical filepaths relative to the dataset 
                      root to full paths to the input data file for all data
                      files found in the SIP.
        """
        out = OrderedDict()

        for fp in self.list_registered_filepaths(prefer_pod):
            srcpath = self.find_source_file_for(fp)
            if srcpath:
                out[fp] = srcpath

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
    :prop nerdm_schema_dir str:  the path to the directory containing JSON schemas
                                 and related model data, including the NERDm 
                                 schema.  If not set, the directory will be 
                                 searched for in possible default locations
    :prop hard_link_data bool (True):  if True, copy data files into the bag 
                                 using a hard link whenever possible.
    :prop update_by_checksum_size_lim int (0):  a size limit in bytes for which 
                                 files less than this will be checked to see 
                                 if it has changed (not yet implemented).
    :prop component_merge_convention str ("dev"): the merge convention name to 
                                 use to merge MIDAS-provided component metadata
                                 with the PDR's initial component metadata.
    :prop id_minter       dict:  data for configuring the ID Minter module
    :prop enrich_refs bool (False):  if True, enhance the metadata describing 
                                 references
    :prop doi_resolver    dict:  data for configuring the DOI resolver client; 
                                 see bagit.tools.enhance.ReferenceEnhancer for 
                                 for info.
    """
    BGRMD_FILENAME = "__bagger-midas3.json"

    @classmethod
    def forMetadataBag(cls, bagdir, config=None, minter=None, for_pres=False):
        """
        create a MIDASMetadataBagger for a existing bag constructed by this 
        class.  The specified bag must include midas3-bagger metadata that has 
        the necessary constructor parameters saved to it.  

        :param bagdir  str:  the full path to the root directory of the bag
        :param config dict:  a dictionary providing configuration parameters; if 
                             not provided, the configuration stored in the 
                             bagger metadata will be used. 
        :param minter IDMinter:  a minter to use for minting new identifiers.
        """
        bag = NISTBag(bagdir)
        bgrmdf = os.path.join(bag.metadata_dir, cls.BGRMD_FILENAME)
        if not os.path.isfile(bgrmdf):
            raise SIPDirectoryError(bagdir, "Unable find midas3 bagger metadata; "
                                            "not a metadata bag?")
        try: 
            bgrmd = utils.read_json(bgrmdf)
        except ValueError as ex:
            raise SIPDirectoryError(bagdir, "Unable parse bagger metadata from "+
                                    os.path.join(os.path.basename(bagdir), "metadata",
                                                 cls.BGRMD_FILENAME)+": "+str(ex), ex)
        if config is None:
            config = bgrmd.get('bagger_config', {})
        upldir=None
        if not for_pres:
            upldir = bgrmd.get('upload_directory')

        resmd = bag.nerd_metadata_for('')
        return MIDASMetadataBagger(resmd.get['ediid'], bgrmd.get('bag_parent'),
                                   bgrmd.get('data_directory'), upldir, config, None, minter)


    @classmethod
    def fromMIDAS(cls, midasid, workdir, reviewparent, uploadparent=None, config={},
                  minter=None, replaces=None, recnum=None):
        """
        Find the data directories for a MIDAS submission and create a 
        MIDASMetadataBagger for it.  The output metadata bag from a previous session 
        may exist already; in this case, the returned bagger will simply wrap that
        previous bag; otherwise, it will be created from the input data (via prepare()).  

        :param midasid   str:  the identifier provided by MIDAS, used as the 
                               name of the directory containing the data.
        :param workdir   str:  the path to the directory that can contain the 
                               output bag
        :param reviewdir str:  the path to the parent directory containing MIDAS
                               submission directories
                               datasets in the review state.
        :param uploaddir str:  the path to the directory containing submitted
                               datasets not yet in the review state.
        :param config   dict:  a dictionary providing configuration parameters
        :param minter IDMinter: a minter to use for minting new identifiers.
        :param replaces  str:  the AIP identifier for a previous published resource 
                               that this SIP replaces.  This should be used if the 
                               EDI ID for a publication has changed because of the 
                               type of revision it is.  If None, the EDI ID has not 
                               changed (or the SIP has not been published before).
        :param recnum str:     the MIDAS record number for the submission, used 
                               to determine the submission directories.  If not 
                               provided, it is determined based on the provided 
                               MIDAS ID.  
        """
        if not recnum:
            recnum = _midadid_to_dirname(midasid, log)
        revdir = None
        upldir = None
        if reviewparent:
            revdir = os.path.join(reviewparent, recnum)
        if uploadparent:
            upldir = os.path.join(uploadparent, recnum)
        return MIDASMetadataBagger(midasid, workdir, revdir, upldir, config, replaces, minter)


    def __init__(self, midasid, bagparent, reviewdir, uploaddir=None, config={}, replaces=None, minter=None):
        """
        Create an SIPBagger to operate on data provided by MIDAS

        :param midasid   str:  the identifier provided by MIDAS, used as the 
                               name of the directory containing the data.
        :param bagparent str:  the path to the directory that can contain the 
                               output bag
        :param reviewdir str:  the path to the directory containing submitted
                               datasets in the review state.
        :param uploaddir str:  the path to the directory containing submitted
                               datasets not yet in the review state.
        :param config   dict:  a dictionary providing configuration parameters
        :param replaces  str:  the AIP identifier for a previous published resource 
                               that this SIP replaces.  This should be used if the 
                               EDI ID for a publication has changed because of the 
                               type of revision it is.  If None, the EDI ID has not 
                               changed (or the SIP has not been published before).
        :param minter IDMinter: a minter to use for minting new identifiers.
        """
        self.midasid = midasid
        self.previd = replaces
        self.name = midasid_to_bagname(midasid)

        usenm = self.name
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        self.log = log.getChild(usenm)
        
        # This will raise an exception if the expected input directories do not
        # exist.
        self.sip = MIDASSIP(midasid, reviewdir, uploaddir)

        super(MIDASMetadataBagger, self).__init__(bagparent, config)

        # If None, we'll create a ID minter if we need one (in self._mint_id)
        self._minter = minter

        self.bagbldr = BagBuilder(self.bagparent, self.name,
                                  self.cfg.get('bag_builder', {}),
                                  logger=self.log)
        if not os.path.exists(self.bagbldr.bagdir):
            self.bagbldr.disconnect_logfile()
        
        mergeetc = self.cfg.get('merge_etc', def_merge_etcdir)
        if not mergeetc:
            raise StateException("Unable to locate the merge configuration "+
                                 "directory")
        self._merger_factory = MergerFactory(mergeetc)

        self.schemadir = self.cfg.get('nerdm_schema_dir', pdr.def_schema_dir)
        self.hardlinkdata = self.cfg.get('hard_link_data', True)
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
            # support for updates requires access to the distribution and rmm services

            if 'store_dir' not in self.cfg['repo_access'] and 'store_dir' in self.cfg:
                self.cfg['repo_access']['store_dir'] = self.cfg['store_dir']
            if 'restricted_store_dir' not in self.cfg['repo_access'] and 'restricted_store_dir' in self.cfg:
                self.cfg['repo_access']['restricted_store_dir'] = self.cfg['restricted_store_dir']

            self.prepsvc = UpdatePrepService(self.cfg['repo_access'],
                                             os.path.join("metadata", self.BGRMD_FILENAME))
        else:
            self.log.warning("repo_access not configured; can't support updates!")

        # The file-examiner allows for ansynchronous examination of the data files
        self.fileExaminer = self._AsyncFileExaminer(self)
#        self.fileExaminer_mode = "none"
#        if examine_file_mode:
#            self.fileExaminer_mode = examine_file_mode

        self.ensure_bag_parent_dir()

    def done(self):
        """
        signal that no further updates will be made to the bag via this bagger.  

        Currently, this only disconnects the internal BagBuilder's log file inside
        the bag; thus, it's okay if further updates are made after calling this 
        function since the BagBuilder will reconnect the log file automatically.
        """
        self.bagbldr.disconnect_logfile()

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
        # if this bag is a revision to a previous publication with a different MIDAS ID,
        # determine the location of the metadata bag for the previous ID.
        prevbagdir = None
        if self.previd and self.previd != self.midasid:
            prevbagdir = os.path.join(self.bagparent, midasid_to_bagname(self.previd))
        
        if os.path.exists(self.bagdir):
            # We already have an established working bag
            self.bagbldr.ensure_bagdir()  # sets builders bag instance

            if not self.prepared:
                self.log.info("Refreshing previously established working bag")
            self.prepared = True
            return False

        elif prevbagdir and os.path.exists(prevbagdir):
            # We've already established a working bag under the previous EDI-ID; 
            # recast it with the new EDI-ID
            try:
                os.rename(prevbagdir, self.bagdir)
            except OSError as ex:
                raise PDRException("Failed to move bag dir, "+os.path.basename(prevbagdir)+
                                   " to new name, "+os.path.basename(self.bagdir), cause=ex)
            self.log.info("Recasting existing metadata bag to new EDI-ID: %s -> %s", 
                          self.previd, self.midasid)
            self.bagbldr.ensure_bagdir()  # sets builders bag instance
            resmd = self.bagbldr.bag.nerd_metadata_for("", True)
            oldediid = self.bagbldr.ediid
            self.bagbldr.ediid = self.midasid

            # add a replaces reference
            replaces = resmd.get('replaces', [])
            newid = resmd.get('doi', resmd.get('@id'))
            replaces.append(OrderedDict([
                ("@id", newid),
                ("ediid", oldediid),
                ("issued", resmd.get('issued', resmd.get('modified','')))
            ]))
            if 'title' in resmd:
                replaces[-1]['title'] = resmd['title']
            if 'version' in resmd:
                replaces[-1]['version'] = re.sub(r'\+\s*\([^\)]+\)', '', resmd['version'])
            self.bagbldr.update_annotations_for("", {"replaces": replaces}, message="adding replacing info")

            self.update_bagger_metadata_for('', {"replacedEDI": self.previd})

            self.prepared = True
            return False

        elif self.prepsvc:
            self.log.debug("Looking for previously published version of bag")
            prepper = self.get_prepper()

            if prepper.create_new_update(self.bagdir):
                self.log.info("Working bag initialized with metadata from previous "
                              "publication.")
                if self.previd:
                    # self.bagbldr.update_annotations_for("", {"replaces": replaces},
                    #                                     message="adding replacing info")
                    # self.update_bagger_metadata_for('', {"replacedEDI": self.previd})
                    pass

        if not os.path.exists(self.bagdir):
            self.bagbldr.ensure_bag_structure()

            if self.midasid.startswith("ark:/"+ark_naan+"/"):
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

            self.sip.nerd = None  # set by ensure_res_metadata()

        else:
            self.bagbldr.ensure_bagdir()

        if not os.path.isfile(self.baggermd_file_for('')):
            self.update_bagger_metadata_for('', {
                'data_directory': self.sip.revdatadir,
                'upload_directory': self.sip.upldatadir,
                'bag_parent': self.bagparent,
                'bagger_config':  self.cfg
            })

        return True

    def get_prepper(self):
        if not self.prepsvc:
            return None
        replaces = self.previd
        if replaces == self.midasid:
            replaces = None
        if replaces:
            replaces = re.sub(r'^ark:/\d+/', '', replaces)
        return self.prepsvc.prepper_for(self.name, replaces=replaces, log=self.log.getChild("prepper"))
                
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

        self.sip.nerd = self.bagbldr.bag.nerdm_record(True);

        # ensure an initial version
        if 'version' not in self.sip.nerd:
            self.sip.nerd['version'] = "1.0.0"
            self.bagbldr.update_annotations_for('',
                                            {'version': self.sip.nerd["version"]})

        self.datafiles = self.sip.registered_files()
        

    def apply_pod(self, pod, validate=True, force=False, lock=True):
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
        :param bool      force:  if True, apply POD regardless of whether the POD
                                 has changed.
        :param bool       lock:  if True (default), acquire a lock before applying
                                 the pod record.
        """
        if lock:
            self.ensure_filelock()
            with self.lock:
                self._apply_pod(pod, validate, force)

        else:
            self._apply_pod(pod, validate, force)

    def _apply_pod(self, pod, validate=True, force=False):
        if not isinstance(pod, (str, unicode, Mapping)):
            raise NERDTypeError("dict", type(pod), "POD Dataset")
        self.ensure_base_bag()

        log.debug("BagBuilder log has %s formatters:\n%s", len(self.bagbldr.log.handlers),
                  "\n".join([str(h.stream) for h in self.bagbldr.log.handlers]))

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
        else:
            self._add_minimal_pod_data(pod)

        # determine if the pod record has changed
        oldpod = self.bagbldr.bag.pod_record()
        if not force and pod == oldpod:
            self.log.info("No change detected in given POD; ignoring")
            return

        # updated will contain the filepaths for components that were updated
        updated = self.bagbldr.update_from_pod(pod, True, True, force)

        # set a default DOI.  For a default to be set, the dataset must use the new
        # EDI-ID ARK form and the dataset must not have been published, yet; that is,
        # this must be for version 1.0.0.  To turn setting the DOI off, do not include the
        # 'doi_minter' property in the configuration (or more precisely, 'doi_minter.naan').
        doi = None
        nerd = self.bagbldr.bag.nerdm_record(True)
        doi_prefix = self.cfg.get('doi_minter',{}).get('minting_naan')
        if doi_prefix and not nerd.get('doi') and nerd.get('ediid','').startswith("ark:/") and \
           ('version' not in nerd or nerd['version'] == "1.0.0"):
            doi = "doi:{0}/{1}".format(str(doi_prefix), self.name)
            nerd['doi'] = doi
            self.bagbldr.update_metadata_for('', {'doi': doi},
                                             message="added default DOI: "+doi)

        # check for use of the restricted public gateway
        if nerd['accessLevel'] == "restricted public":
            if self.cfg.get('restricted_access',{}).get('gateway_url'):
                self.log.info("Detected use of restricted access gateway; updating metadata accordingly")

                racfg = self.cfg['restricted_access']
                burl = racfg['gateway_url']
                disclaimer = racfg.get('disclaimer')

                nerdres = self.bagbldr.bag.nerd_metadata_for('', False)
                rpg = [c for c in nerdres.get('components', [])
                         if 'accessURL' in c and c['accessURL'].startswith(burl)]
                for c in rpg:
                    if not nerdutils.is_type(c, "RestrictedAccessPage"):
                        c['@type'] = ["nrdp:RestrictedAccessPage"] + c['@type']

                if len(rpg) > 0:
                    nerdres = {'components': nerdres['components']}
                    if disclaimer:
                        nerdres['disclaimer'] = disclaimer
                    self.bagbldr.update_metadata_for('', nerdres,
                                                     message="enhancing metadata for restricted access")
                    nerd = self.bagbldr.bag.nerdm_record(True)

            else:
                self.log.info("Note: SIP marked for restricted public access")
                    

        # we're done; update the cached NERDm metadata and the data file map
        if not self.sip.nerd or updated['updated'] or updated['added'] or updated['deleted']:
            self.sip.nerd = nerd
            self.datafiles = self.sip.registered_files()
      
    def _add_minimal_pod_data(self, pod):
        for key in _minimal_pod:
            if key not in pod:
                pod[key] = _minimal_pod[key]

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
        

    def ensure_data_files(self, nodata=True, force=False, examine="async", whendone=None):
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
        :param function whendone:  a function to run after examination finishes.  This 
                             is ignored if examine is False or None.  This is really 
                             intended for when examine="async", but it will be run 
                             if examine="sync", too.  
        """
        if not self.sip.nerd:
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
        if examine and len(self.fileExaminer.files) > 0:
            if examine == "async":
                self.log.info("Launching file examiner thread")
                self.fileExaminer.launch(whendone=whendone)
            else:
                # do it now!
                self.log.info("Running file examiner synchronously")
                self.fileExaminer.run(whendone=whendone)
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
                srcpath = self.sip.find_source_file_for(filepath)
                if srcpath and moddate_of(srcpath) > since:
                    self.fileExaminer.add(srcpath, filepath)
                    out.append(filepath)

        return out

    def enhance_metadata(self, nodata=True, force=False, examine="sync", whendone=None):
        """
        ensure that we have complete and updated metadata after applying a
        POD description.  This will look for updates to the submitted data
        file and, if necessary, extract updated metadata from the files.
        It will also ensure that all the subcollections are described with 
        metadata.  

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
        :param function whendone:  a function to run after examination finishes.  This 
                             is ignored if examine is False or None.  This is really 
                             intended for when examine="async", but it will be run 
                             if examine="sync", too.  
        """
        if self.cfg.get('enrich_refs', False):
            self.ensure_enhanced_references()
        self.ensure_subcoll_metadata()
        self.ensure_data_files(nodata, force, examine, whendone)  # may be partially async.

    def ensure_enhanced_references(self):
        """
        examine the references and, if necessary, enhance their descriptions from 
        metadata obtained by resolving their DOI metadata.
        """
        self.ensure_preparation()
        if 'references' in self.sip.nerd:
            self.log.debug("Will enrich references as able")
            synchronize_enhanced_refs(self.bagbldr, config=self.cfg.get('doi_resolver'),
                                      log=self.log)
            nerd = self.bagbldr.bag.nerd_metadata_for("", True)
            self.sip.nerd['references'] = nerd.get('references',[])

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
                md["__status"] = "in progress"
                
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
            if self.sip.nerd:
                cmps = self.sip.nerd.get('components',[])
                for i in range(len(cmps)):
                    if md['@id'] == cmps[i]['@id']:
                        cmps[i] = md
                        break
                if i >= len(cmps):
                    if len(cmps) == 0:
                        self.sip.nerd['components'] = [md]
                    else:
                        self.sip.nerd['components'].append(md)


    def _check_checksum_files(self):
        # This file will look all of the files that have been identified as
        # ChecksumFiles to see if the value they contain matches the value
        # stored in the metadata for the datafile it is associated with.  If
        # they do not match, the valid metadata flag for the checksum file
        # will be set to false.
        for comp in self.sip.nerd.get('components', []):
            if 'filepath' not in comp or \
               not any([":ChecksumFile" in t for t in comp.get('@type',[])]):
                continue

            srcpath = self.sip.find_source_file_for(comp['filepath'])
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
                    if comp.get('valid') is None or comp.get('valid') != bool(valid):
                        comp['valid'] = bool(valid)
                        msg="Updating valid=%s in metadata for ChecksumFile %s" % \
                            (comp['valid'], comp['filepath'])
                        self.bagbldr.update_metadata_for(comp['filepath'],
                                                         {'valid': comp['valid']},
                                                         "ChecksumFile", msg)

    def finalize_version(self, update_reason=None):
        """
        determine the version to assign to this dataset given the state of its update, 
        update the version metadata (including history), and return the revised nerdm record.
        """
        if self.datafiles is None:
            self.ensure_res_metadata()
        if not self.sip.nerd:
           self.sip.nerd = self.bagbldr.bag.nerdm_record(True)

        # determine the type of update under way
        uptype = _NO_UPDATE
        oldver = self.sip.nerd.setdefault('version', '1.0.0')
        ineditre = re.compile(r'^(\d+(.\d+)*)\+ \(.*\)')
        matched = ineditre.search(oldver)
        if matched:
            # the version is marked as "+ (in edit)", indicating that the
            # next published version should be based on the last published
            # version.  Note that the base version currently set is not necessarily
            # accurate: it may reflect the target version the last time
            # preservation was initiated; if that preservation failed, that version
            # would not be correct.  Thus, we must check for the last published
            # version.

            # get the last published version
            lastver = "0"
            prepr = self.get_prepper()
            if prepr:
                lastver = prepr.latest_version(["bag-cache", "bag-store", "repo"])
            if lastver == "0":
                self.log.info("finalizing version: dataset has never been published; setting version to 1.0.0")
                self.sip.nerd['version'] = "1.0.0"

            else:
                # it's been published before under version=lastver
                ver = [int(f) for f in lastver.split('.')]
                for i in range(len(ver), 3):
                    ver.append(0)

                bmd = self.baggermd_for('')
                if self.sip.nerd.get('status') != "removed" and \
                   (len(self.datafiles) > 0 or bmd.get('replacedEDI')):
                    # either there're data files waiting to be included; it's a data update
                    uptype = _DATA_UPDATE
                    ver[1] += 1
                    ver[2] = 0
                    umsg = "incrementing for change in EDI-ID"
                    if len(self.datafiles) > 0:
                        umsg = "incrementing for updated data files"
                        if bmd.get('replacedEDI'):
                            umsg += " (and change in EDI-ID)"
                    self.log.debug("data files being updated: %s", self.datafiles.keys())
                else:
                    # otherwise, this is a metadata update, which increments the
                    # third field.
                    uptype = _MDATA_UPDATE
                    ver[2] += 1
                    umsg = "incrementing metadata version field for updated metadata only"

                self.sip.nerd['version'] = ".".join([str(v) for v in ver])
                self.log.info("finalizing version: %s: %s", umsg, self.sip.nerd['version'])

        else:
            self.log.info("finalizing version: sticking with explicitly set value: %s",
                          self.sip.nerd['version'])

        # record the version in the annotations
        annotf = self.bagbldr.bag.annotations_file_for('')
        if os.path.exists(annotf):
            adata = utils.read_nerd(annotf)
        else:
            adata = OrderedDict()
        adata['version'] = self.sip.nerd['version']
        relhist = self.sip.nerd.get('releaseHistory')
        if relhist is None:
            relhist = bagutils.create_release_history_for(self.sip.nerd['@id'])
            relhist['hasRelease'] = self.sip.nerd.get('versionHistory', [])
        verhist = relhist['hasRelease']

        # set the version history
        if uptype != _NO_UPDATE and self.sip.nerd['version'] != lastver and \
           ('issued' in self.sip.nerd or 'modified' in self.sip.nerd) and \
           not any([h['version'] == self.sip.nerd['version'] for h in verhist]):
            issued = ('modified' in self.sip.nerd and self.sip.nerd['modified']) or \
                     self.sip.nerd['issued']
            relhist['hasRelease'].append(OrderedDict([
                ('version', self.sip.nerd['version']),
                ('issued', issued),
                ('@id', self.sip.nerd['@id']+".v"+re.sub(r'\.','_',self.sip.nerd['version'])),
                ('location', 'https://'+PDR_PUBLIC_SERVER+'/od/id/'+ \
                          re.sub(r'\.rel$',
                                 ".v"+re.sub(r'\.','_', self.sip.nerd['version']),
                                 relhist['@id']))
            ]))
            if self.sip.nerd.get('status', 'available') == 'removed':
                # need to deprecate all previous minor versions
                self._set_history_deactivated(relhist['hasRelease'])
            elif self.sip.nerd.get('status', 'available') != 'available':
                verhist[-1]['status'] = self.sip.nerd.get('status')
            if update_reason is None:
                if uptype == _MDATA_UPDATE:
                    update_reason = 'metadata update'
                elif uptype == _DATA_UPDATE:
                    update_reason = 'data update'
                else:
                    update_reason = ''
            verhist[-1]['description'] = update_reason
            adata['releaseHistory'] = relhist
            self.sip.nerd['releaseHistory'] = relhist
        
        utils.write_json(adata, annotf)
        self.bagbldr.record("Preparing for preservation of %s by setting version, "
                            "release history", self.sip.nerd['version'])
        return self.sip.nerd

    def _set_history_deactivated(self, relhist):
        # Note: possible error mode: if files were added without triggering an edi-id change,
        # those major versions will not get marked as removed.  
        lastver = relhist[-1].get('version','1.0.0')
        lastmaj = re.sub(r'\.\d+$', '', lastver)
        for rel in relhist:
            if rel.get('version', '').startswith(lastmaj):
                rel['status'] = 'removed'
        return relhist
        
    class _AsyncFileExaminer():
        """
        a class for extracting metadata from files asynchronously.  The files 
        to be examined should be added via the add() function.  When all 
        desired files have been added, executing launch() will launch the 
        examination in a separate thread. 
        """

        threads = OrderedDict()

        def __init__(self, bagger):
            self.bagger = bagger
            if not self.bagger.bagdir:
                raise ValueError("Bagger not prepped: no bag root dir set")
            self.id = self.bagger.bagdir
            self.files = OrderedDict()

        def add(self, location, filepath):
            if filepath not in self.files:
                self.files[filepath] = location

        def _createThread(self, stoplogging=False, whendone=None):
            if self.running():
                self.bagger.log.debug("File examiner thread is still running")
                return None
            self.threads[self.id] = self._Thread(self, stoplogging, whendone)
            return self.threads[self.id]

        def running(self):
            thread = self.threads.get(self.id)
            return thread and thread.is_alive()

        def launch(self, stoplogging=False, whendone=None):
            # run asynchronously
            thread = self._createThread(stoplogging, whendone)
            if thread:
                thread.start()

        def run(self, whendone=None):
            # run pseudo-synchronously
            thread = self._createThread(False, whendone)
            if thread:
                thread.start()
            self.waitForCompletion(None)
            if thread.exc:
                raise thread.exc

        def waitForCompletion(self, timeout):
            thread = self.threads.get(self.id)
            if not thread or not thread.is_alive():
                return True

            if thread is threading.current_thread():
                log.warn("Thread "+thread.getName()+" trying to wait on itself; ignoring")
                return False

            try:
                thread.join(timeout)
            except RuntimeError as ex:
                log.warn("Skipping wait for examiner thread, "+thread.getName()+
                         ", for deadlock danger")
                return False
            if thread.is_alive():
                log.warn("Thread waiting timed out: "+str(thread))
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
                if '__status' in md:
                    md['__status'] = "updated"

                # it's possible that this file has been deleted while this
                # thread was launched; make sure it still exists
                if not self.bagger.bagbldr.bag.comp_exists(filepath):
                    self.bagger.log.warning("Examiner thread detected that component no " +
                                            "longer exists; skipping update for bag="+
                                            self.bagger.name+", path="+filepath)
                    return

                md = self.bagger.bagbldr.update_metadata_for(filepath, md, ct,
                                   "async metadata update for file, "+filepath)
                if '__status' in md:
                    del md['__status']
                    self.bagger.bagbldr.replace_metadata_for(filepath, md, '')
                self.bagger._mark_filepath_synced(filepath)

            except Exception as ex:
                self.bagger.log.error("%s: Failed to extract file metadata: %s"
                                      % (location, str(ex)))

        @classmethod
        def wait_for_all(cls, timeout=10):
            log.info("Waiting for file examiner threads to finish")
            tids = list(cls.threads.keys())
            done = []
            for tid in tids:
                thread = cls.threads.get(tid)
                if not thread:
                    done.append(tid) 
                    continue
                if thread is threading.current_thread():
                    continue
                try:
                    exmnr.thread.join(timeout)
                    if thrd.is_alive():
                        log.warn("Thread waiting timed out: "+str(thrd))
                    else:
                        done.append(tid)
                except RuntimeError as ex:
                    log.warn("Skipping wait for thread, "+str(thrd)+
                             ", for deadlock danger")
            return len(done) == len(tids)

        class _Thread(threading.Thread):
            def __init__(self, exmnr, stoplogging=False, whendone=None):
                super(MIDASMetadataBagger._AsyncFileExaminer._Thread, self). \
                    __init__(name="Examiner-"+exmnr.id)
                self.exif = exmnr
                self.stop_logging = stoplogging
                self.on_finish = whendone
                self.exc = None

            def run(self):
                # time.sleep(0.1)
                while self.exif.files:
                    self.exif.examine_next()

                try:
                    if self.on_finish:
                        self.on_finish()
                except Exception as ex:
                    self.exif.bagger.log.exception("post-file-examine function failure: "+
                                                   str(ex))
                    self.exc = ex

                if self.stop_logging:
                    self.exif.bagger.bagbldr.disconnect_logfile()

                del self.exif.threads[self.exif.id]
        

class PreservationBagger(SIPBagger):
    """
    A bagger that creates an AIP--a preservation bag--from an SIP conforming to the 
    midas3 convention.

    In this convention, the Submission Information Package (SIP) is a so-called
    "metadata bag" produced by a midas3.MIDASMetadataBagger, driven by a MIDAS 
    user session.  This SIP is used as the basis for the output Archive Information
    Package (AIP): user-submitted data files are added in and the finalized bag 
    is split according to the multibag profile and serialized into zip files.  

    Note that, when possible, user-provided datafiles are added to the output 
    directory as a hard link: that is, no bytes are copied.  Metadata data files 
    are copied.

    Note that this bagger can be set explicitly in a AIP creation mode or an 
    update mode via the asupdate parameter to the constructor.  When one of 
    these modes is set, the repository will be queried to see if the dataset 
    with the same AIP identifier already exists; this state must agree with the 
    set mode, else an exception is thrown.  This parameter is provided to ensure 
    the state assumed by the caller--namely, whether the dataset already exists--
    is in sync with the state of the repository.  If the mode is not set by the 
    caller, the mode is determined implicitly by whether the AIP already exists 
    in the repository.

    This class takes as its input the location of the metadata bag and, optionally,
    the directory where the data files can be found.  If the latter is not provided,
    this bagger will consult the "data_directory" midas3 bagger metadata in the 
    metadata bag.  The data files must organized within the directory in the hierarchy 
    expressed in the NERDm metadata.  [Also, the metadata bag may contain a fetch.txt 
    file; if the config parameter "fetch_data_files" is True, then any file that 
    cannot be found in the data directory but which has a listing in the fetch.txt 
    file will retrieved from the given URL and placed in the output bag.]

    This class takes a configuration dictionary on construction; the 
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
    :prop conponent_merge_convention str ("dev"): the merge convention name to 
                                 use to merge MIDAS-provided component metadata
                                 with the PDR's initial component metadata.
    :prop relative_to_indir bool (False):  If True, the output bag directory 
       is expected to be under one of the input directories; this base class
       will then ensure that it has write permission to create the output 
       directory.  If False, the bagger may raise an exception if the 
       requested output bag directory is found within an input SIP directory,
       regardless of whether the process has permission to write there.  
    :prop bag_name_format str ("{0}.mbag{1}-{2}"):  a python format string 
       to use to form a name for the output bag.  The data required to turn
       the format string into a name are: (0) the dataset identifier, (1)
       a bag profile version string, and (2) a bag sequence number.
    :prop mbag_version str:  the version string for bag profile for output
       bags.  
    :prop fetch_data_files bool (False):  if True and a fetch.txt file is found 
       in the bag, any file with an entry in that file but which can not be 
       found in the data directory will be retrieved from the registered URL 
       given by its entry.  
    """
    BGRMD_FILENAME = MIDASMetadataBagger.BGRMD_FILENAME

    @classmethod
    def fromMetadataBagger(cls, mdbagger, bagparent, config=None, asupdate=None):
        """
        create a PreservationBagger to preserve the data described in a metadata bag
        that was constructed by a particular MetadataBagger instance.  

        :param MetadataBagger mdbagger:  the MetadataBagger that produced (or could have
                                produced) the source metadata bag to be preserved
        :param str bagparent:   the directory to contain the output preservation bag.
        :param dict config:     the configuration to use, if not provided, the configuration
                                embedded in the MetadataBagger will be used.  
        :param asupdate bool:   a flag indicating whether this is an update to an existing
                                AIP (see constructor documentation).
        """
        if not config:
            pcfg = mdbagger.cfg.get('preservation_service', {})
            if 'sip_type' in pcfg:
                config = pcfg['sip_type'].get('midas3', {}).get('preserv',{}).get('bagger', {})
            else:
                config = pcfg.get('bagger', {})
        datadir = mdbagger.sip.revdatadir
        return cls(mdbagger.bagdir, bagparent, datadir, config, asupdate=None)

    def __init__(self, sipdir, bagparent, datadir, config=None, asupdate=None):
        """
        Create an SIPBagger for preserving a dataset from a metadata bag constructed
        using the midas3 convention.

        :param sipdir    str:  the path to the directory that contains the input
                               metadata bag (SIP).  
        :param bagparent str:  the path to the directory where the preservation
                               bag should be written.  
        :param datadir   str:  the path to the directory containing user-submitted
                               datasets.  This location will be gleaned from the 
                               bagger metadata stored in the metadata bag.  
        :param config   dict:  a dictionary providing configuration parameters
        :param asupdate bool:  if set to true, the caller believes this bagger 
                               should be creating an update to an existing AIP;
                               if false, the caller believes this is a new AIP.
                               If this believe does not correspond with the 
                               actual contents of the repository, an exception 
                               is raised when the attempt to process the SIP is 
                               made.  If None (default), no check is done; if 
                               an AIP already exists in the repository, this 
                               bagger creates an update.  

        @raises SIPDirectoryNotFound  if the specified SIP directory does not 
                               exist or is not, in fact, a directory; or if 
                               the specified data directory cannot be found.  
        @raises SIPDirectoryError  if the specified SIP directory does not 
                               appear to be a midas3 metadata bag; in particular,
                               if it does not include a POD record file.  
        """
        self.sipdir = sipdir
        self.datadir = datadir     # can be None
        self.asupdate = asupdate   # can be None

        if not os.path.isdir(self.sipdir):
            raise SIPDirectoryNotFound(sipdir)
        bag = NISTBag(self.sipdir)
        if not os.path.isfile(bag.pod_file()):
            raise SIPDirectoryError(sipdir, "Missing POD file; SIP is not ready")
        if not os.path.isfile(bag.nerd_file_for('')):
            raise SIPDirectoryError(sipdir, "Missing NERDm file; SIP is not ready")

        if config is None:
            config = {}
        super(PreservationBagger, self).__init__(bagparent, config)

        resmd = bag.nerd_metadata_for("", True)
        self.midasid = resmd.get('ediid', resmd.get('@id'))
        if not self.midasid:
            raise PreservationStateError("EDI-ID is not set; SIP is not ready")
        self.name = midasid_to_bagname(self.midasid, log)

        self.sip = MIDASSIP(self.midasid, self.datadir, podrec=bag.pod_file())
        self.datafiles = self.sip.registered_files()

        usenm = self.name
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        self.aiplog = log.getChild(usenm)

        # check for needed configuration
        if self.cfg.get('check_data_files', True) and \
           not self.cfg.get('store_dir'):
            raise ConfigurationException("PreservationBagger: store_dir " +
                                         "config param needed")

        # do a sanity check on the bag parent directory
        if not self.cfg.get('relative_to_indir', False):
            datapath = os.path.abspath(self.datadir)
            if datapath[-1] != os.sep:
                datapath += os.sep
            if os.path.abspath(self.bagparent).startswith(datapath):
                if self.cfg.get('relative_to_indir') == False:
                    # you said it was not relative, but it sure looks that way
                    raise ConfigurationException("'relative_to_indir'=False but"
                                                 +" bag dir (" + self.bagparent+
                                                 ") appears to be below the "+
                                                 "data directory (" + self.datadir+")")

                # bagparent is inside sipdir
                self.bagparent = os.path.abspath(self.bagparent)[len(datapath):]
                self.cfg['relative_to_indir'] = True

        if self.cfg.get('relative_to_indir'):
            self.bagparent = os.path.join(self.datadir, self.bagparent)
                
        self.ensure_bag_parent_dir()
        self.bagbldr = None

    @property
    def bagdir(self):
        """
        The path to the output bag directory.
        """
        return (self.bagbldr and self.bagbldr.bagdir) or \
            os.path.join(self.bagparent, self.name)

    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """
        raise PODError("POD files not expected in midas3 SIPs: use apply_pod()")

    def ensure_preparation(self, nodata=False):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP, ready for annotation 
        and preservation.  

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.
        """
        if not self.bagbldr:
            self.establish_output_bag()
        if not self.sip.nerd:
            self.sip.nerd = self.bagbldr.bag.nerdm_record(True)
        if not nodata:
            self.add_data_files()

    def done(self):
        """
        signal that no further updates will be made to the bag via this bagger.  

        Currently, this only disconnects the internal BagBuilder's log file inside
        the bag; thus, it's okay if further updates are made after calling this 
        function since the BagBuilder will reconnect the log file automatically.
        """
        self.bagbldr.disconnect_logfile()

    def establish_output_bag(self):
        """
        set up preservation bag in the target output bag-parent directory.  If the 
        input SIP (metadata) bag is already in the output directory, it will be renamed
        (if necessary) to its proper name for the MIDAS3 convention; otherwise, it will 
        be copied to the output directory (to its conventional name).  The input bag will 
        determined to already be in its output directory if current (absolute) parent 
        directory lexically matches the bag-parent directory specified at construction time.
        """
        dest = os.path.join(self.bagparent, self.name)

        if os.path.dirname(os.path.normpath(os.path.abspath(self.sipdir))) != \
                    os.path.normpath(os.path.abspath(self.bagparent.rstrip('/'))):
            # source SIP directory is not under bagparent, the desired target directory
            # copy it there.
            if os.path.exists(dest):
                # it looks like there is an artifact from a previous preservation attempt;
                # remove it so we can try again.
                # SHOULD THIS HAPPEN?
                if os.path.exists(dest+".lock"):
                    # try locking the bag; if this works, the bag may disappear by the time
                    # we get access to it.
                    self.ensure_filelock()
                    with self.lock:
                        pass

                if os.path.exists(dest):
                    log.warn("Removing previous version of preservation bag, %s",
                             self.name)
                    if os.path.isdir(dest):
                        utils.rmtree(dest)
                    else:
                        shutil.remove(dest)
            shutil.copytree(self.sipdir , dest)

        elif os.path.basename(self.sipdir) != self.name:
            # the input bag is already under the bagparent directory; just make sure
            # it has the correct name
            os.rename(self.sipdir, dest)

        # create the bag builder we will use
        bldcfg = self.cfg.get('bag_builder', {})
        if 'ensure_component_metadata' not in bldcfg:
            # default True can mess with annotations
            bldcfg['ensure_component_metadata'] = False  
        self.bagbldr = BagBuilder(self.bagparent, self.name, bldcfg,
                                  logger=self.aiplog)
            


    def form_bag_name(self, dsid, bagseq=0, dsver="1.0"):
        """
        return the name to use for the working bag directory.  According to the
        NIST BagIt Profile, preservation bag names will follow the format
        AIPID.AIPVER.mbagMBVER-SEQ

        :param str  dsid:   the AIP identifier for the dataset
        :param int  bagseq: the multibag sequence number to assign (default: 0)
        :param str  dsver:  the dataset's release version string.  (default: 1.0)
        """
        fmt = self.cfg.get('bag_name_format')
        bver = self.cfg.get('mbag_version', DEF_MBAG_VERSION)
        dsid = _arkid_pfx_re.sub('', dsid)
        return bagutils.form_bag_name(dsid, bagseq, dsver, bver, namefmt=fmt)

    def add_data_files(self):
        """
        link in copies of the dataset's data files
        """
        self.bagbldr.ensure_bagdir()
        if not os.path.exists(self.bagbldr.bag.data_dir):
            os.mkdir(self.bagbldr.bag.data_dir);
        for dfile, srcpath in self.datafiles.items():
            # need to do a final re-examine of all files as the metadata building
            # stage may have been looking at files in upload that were never
            # accepted into review.
            md = self.bagbldr.describe_data_file(srcpath, dfile, True)
            ct = md.get('@type')
            if ct:
                ct = re.sub(r'^[^:]*:', '', ct[0])
            md = self.bagbldr.update_metadata_for(dfile, md, ct,
                        "final metadata update for file, "+dfile)

            # migrate the data file into the bag
            self.bagbldr.add_data_file(dfile, srcpath, False, True)

    def make_bag(self, lock=True):
        """
        convert the input SIP into a bag ready for preservation.  More 
        specifically, the result will be a bag directory with finalized 
        content, ready for serialization.  

        :param lock bool:   if True (default), acquire a lock before making
                            the preservation bag.
        :return str:  the path to the finalized bag directory
        """
        return self.finalize_bag(lock)
    
    def finalize_bag(self, lock=True):
        """
        convert the input SIP into a bag ready for preservation.  More 
        specifically, the result will be a bag directory with finalized 
        content, ready for serialization.  

        :param lock bool:   if True (default), acquire a lock before making
                            the preservation bag.
        :return str:  the path to the finalized bag directory
        """
        if lock:
            self.ensure_filelock()
            with self.lock:
                return self._finalize_bag_impl()

        else:
            return self._finalize_bag_impl()
    
    def _finalize_bag_impl(self):
        # this is intended to be called from finalize_bag(), with or with out
        # lock on the output bag.
        
        self.prepare(nodata=False)

        # update a few dates in the metadata
        firstpub = self.sip.nerd.get('version','1.0.0') == "1.0.0"
        now = datetime.fromtimestamp(time.time()).isoformat()
        bmd = self.baggermd_for('')
        dates = OrderedDict()
        dates['annotated'] = now
        if len(self.datafiles) > 0 or bmd.get('replacedEDI') or firstpub:
            dates['revised'] = now
        ## by default, keep the issued data passed in from MIDAS
        if not self.sip.nerd.get('issued'):
            dates['issued'] = now
        if firstpub:
            dates['firstIssued'] = self.sip.nerd.get('issued', now)
        self.bagbldr.update_annotations_for('', dates, message="setting publishing dates")

        # get rid of artifacts from the metadata bag construction process
        self.clean_bag()

        finalcfg = self.cfg.get('bag_builder', {}).get('finalize', {})
        if finalcfg.get('ensure_component_metadata') is None:
            finalcfg['ensure_component_metadata'] = False

        # finalization of the version (and history) was already done; assume version is
        # correct
        # ver = self.finalize_version()

        # rename the bag for a proper version and sequence number
        nerd = self.bagbldr.bag.nerd_metadata_for('', True)
        seq = self._determine_seq()
        newname = self.form_bag_name(self.name, seq, nerd.get('version', '1.0.0'))
        newdir = os.path.join(self.bagbldr._pdir, newname)
        if os.path.isdir(newdir):
            log.warn("Removing previously existing output bag, "+newname)
            shutil.rmtree(newdir)
            
        self.bagbldr.rename_bag(newname)

        # write final bag metadata and support files
        self.bagbldr.finalize_bag(finalcfg)

        # make sure we've got valid NIST preservation bag!
        if finalcfg.get('validate', True):
            # this will raise an exception if any issues are found
            self._validate(finalcfg.get('validator', {}))

        isrestricted = nerd.get('accessLevel', 'public') != 'public' and \
                       any([ nerdutils.is_type(c, 'RestrictedAccessPage') 
                             for c in nerd.get('components', []) if 'accessURL' in c ])
        if finalcfg.get('check_data_files', True):
            if isrestricted:
                log.warning("Must skip data availability check for restricted data")
            else:
                # this will raise an exception if any issues are found
                self._check_data_files(finalcfg.get('data_checker', {}))

        return self.bagbldr.bagdir

    def _determine_seq(self):
        depinfof = os.path.join(self.bagdir,"multibag","deprecated-info.txt")
        if not os.path.exists(depinfof):
            return 0
        
        info = self.bagbldr.bag.get_baginfo(depinfof)
        m = re.search(r'-(\d+)$',
                      info.get('Internal-Sender-Identifier', [''])[-1])
        if m:
            return int(m.group(1))+1
        return 0

    def _validate(self, config):
        """
        run a final validation on the output bag

        :param config dict:  a configuration to pass to the validator; see 
                             nistoar.pdr.preserv.bagit.validate for details.
                             If not provided, the configuration for this 
                             builder will be checked for the 'validator' 
                             property to use as the configuration.
        """
        ERR = "error"
        WARN= "warn"
        REC = "rec"
        raiseon_words = [ ERR, WARN, REC ]
        
        raiseon = config.get('raise_on', WARN)
        if raiseon and raiseon not in raiseon_words:
            raise ConfigurationException("raise_on property not one of "+
                                         str(raiseon) + ": " + raiseon)
        
        res = self.bagbldr.validate(config)

        itp = res.PROB
        if raiseon:
            itp = ((raiseon == ERR)  and res.ERR)  or \
                  ((raiseon == WARN) and res.PROB) or res.ALL
            
        issues = res.failed(itp)
        if len(issues):
            log.warn("Bag Validation issues detected for AIP id="+self.name)
            for iss in issues:
                if iss.type == iss.ERROR:
                    log.error(iss.description)
                elif iss.type == iss.WARN:
                    log.warn(iss.description)
                else:
                    log.info(iss.description)

            if raiseon:
                raise AIPValidationError("Bag Validation errors detected",
                                         errors=[i.description for i in issues])

        else:
            log.info("%s: bag validation completed without issues",
                     self.bagbldr.bagname)

    def _check_data_files(self, data_checker_config, viadistrib=True):
        """
        make sure all of the data files are accounted for.  The bag must 
        either contain all of the data files listed in the nerdm components
        or they must be available else where in the publishing pipeline:
        the output storage dir (possibly still avaiting migration to the 
        repository) or already published in the repository.
        """
        config = {
            "repo_access": self.cfg.get('repo_access', {}),
            "store_dir":  self.cfg.get('store_dir'),
            "restricted_store_dir":  self.cfg.get('restricted_store_dir')
        }
        config.update( deepcopy(data_checker_config) )

        chkr = DataChecker(self.bagbldr.bag, config,log.getChild("data_checker"))

        missing = chkr.unindexed_files(viadistrib=viadistrib)
        if len(missing) > 0:
            log.error("master bag for id=%s is missing the following "+
                      "files from the multibag file index:\n  %s",
                      self.name, "\n  ".join(missing))
            raise AIPValidationError("Bag data check failure: data files are " +
                                     "missing from the multibag file index")

        missing = chkr.unavailable_files(viadistrib=viadistrib)
        if len(missing) > 0:
            log.error("unable to locate the following files described " +
                      "in master bag for id=%s:\n  %s",
                      self.name, "\n  ".join(missing))
            raise AIPValidationError("Bag data check failure: unable to locate "+
                                     "some data files in any available bags")

    def clean_bag(self):
        """
        get rid of artifacts from the metadata bag construction process.  
        """
        # get rid of any administrative files at the top
        for bfile in [f for f in os.listdir(self.bagbldr.bagdir)
                              if f.startswith('_') and os.path.isfile(os.path.join(self.bagbldr.bagdir,f))]:
            os.remove(os.path.join(self.bagbldr.bagdir, bfile))

        # get rid of any administrative files at the top in the metadata directory
        for (root, dirs, files) in os.walk(self.bagbldr.bag.metadata_dir):
            for bfile in [os.path.join(root, f) for f in files if f.startswith('_')]:
                os.remove(bfile)

        # remove non-standard, administrative metadata from pod
        if os.path.exists(self.bagbldr.bag.pod_file()):
            md = self.bagbldr.bag.pod_record()
            rmkeys = [k for k in md.keys() if k.startswith('__')]
            if len(rmkeys) > 0:
                for key in rmkeys:
                    del md[key]
                utils.write_json(md, self.bagbldr.bag.pod_file())

        # remove non-standard, administrative metadata from nerdm
        for (root, dirs, files) in os.walk(self.bagbldr.bag.metadata_dir):
            for mdfile in ['nerdm.json', 'annot.json']:
                if mdfile in files:
                    nf = os.path.join(root, mdfile)
                    md = utils.read_json(nf)
                    rmkeys = [k for k in md.keys() if k.startswith('__')]
                    if len(rmkeys) > 0:
                        for key in rmkeys:
                            del md[key]
                        utils.write_json(md, nf)
    

