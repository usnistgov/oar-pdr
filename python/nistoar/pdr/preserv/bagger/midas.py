"""
This module creates bags from MIDAS input data via the SIPBagger interface.
It specifically provides two implementations: MIDASMetadataBagger and 
MIDASFinalBagger.  The former is used by the pre-publication landing page 
service to prepare the NERDm metadata to be displayed as a data publication
is being previewed as well as by the PDR publication tools that will collect
additional metadata.  The latter implementation is used complete the bagging 
process for the preservation service.

The implementations use the BagBuilder class to populate the output bag.   
"""
import os, errno, logging, re, json, shutil, threading, time
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict
from copy import deepcopy

from .base import SIPBagger, moddate_of, checksum_of, read_pod
from .base import sys as _sys
from . import utils as bagutils
from ..bagit.builder import BagBuilder, NERDMD_FILENAME, FILEMD_FILENAME
from ..bagit import NISTBag
from ..bagit.tools import synchronize_enhanced_refs
from ....id import PDRMinter
from ... import def_merge_etcdir, utils
from .. import (SIPDirectoryError, SIPDirectoryNotFound, AIPValidationError,
                ConfigurationException, StateException, PODError,
                PreservationStateError)
from .prepupd import UpdatePrepService
from .datachecker import DataChecker
from nistoar.nerdm.merge import MergerFactory

from .... import pdr
ARK_NAAN = pdr.ARK_NAAN

# _sys = PreservationSystem()
log = logging.getLogger(_sys.system_abbrev)   \
             .getChild(_sys.subsystem_abbrev) \
             .getChild("midas") 

DEF_MBAG_VERSION = bagutils.DEF_MBAG_VERSION
DEF_MIDAS_POD_FILE = "_pod.json"
SUPPORTED_CHECKSUM_ALGS = [ "sha256" ]
DEF_CHECKSUM_ALG = "sha256"
DEF_MERGE_CONV = "initdef"  # For merging MIDAS-generated metadata with
                            # initial defaults
UNSYNCED_FILE = "_unsynced"

# type of update (see determine_update_version())
_NO_UPDATE    = 0
_MDATA_UPDATE = 1
_DATA_UPDATE  = 2

def _midadid_to_dirname(midasid, log=None):
    out = midasid

    if midasid.startswith("ark:/"+ARK_NAAN+"/"):
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
    This class will migrate metadata provided by MIDAS into a working bag
    that only contains metadata and generated ancillary data.  This data 
    should be sufficient for generating a working landing page.
    
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
    :prop hard_link_data boo (True)l:  if True, copy data files into the bag 
                                 using a hard link whenever possible.
    :prop pod_locations  list of str (["_pod.json"]):  a list of relative file 
                                 paths where the POD dataset file might be 
                                 found, in order of preference.  
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

    def __init__(self, midasid, workdir, reviewdir, uploaddir=None, config={},
                 minter=None, sipdirname=None, asyncexamine=False):
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
        :param asyncexamine bool:  if True, examine and extract file metadata 
                               asynchronously.  This will cause a separate 
                               thread to be launch to do the extraction which,
                               for large SIPs, can take a while.  This occurs,
                               specifically, within ensure_data_files() 
                               (which is called within ensure_preparation()).
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

        # make sure the ID provided matches the one in the pod file
        podfile = self.find_pod_file()
        if podfile:
            # this will raise a PODError if the file is not valid
            pod = read_pod(podfile)
            if pod.get('identifier') != midasid:
                raise SIPDirectoryNotFound(msg="No matching SIP available",
                                           sys=self)

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

        self.hardlinkdata = self.cfg.get('hard_link_data', True)
        self.inpodfile = None
        self.resmd = None

        # this will contain a mapping of files that currently appear in the
        # MIDAS submission area; the keys are filepath values (in the NERDm
        # sense--i.e. relative to the dataset root), and values are the full
        # path to its location on disk.
        self.datafiles = None

        self.prepsvc = None
        if 'repo_access' in self.cfg:
            # support for updates requires access to the distribution and
            # rmm services
            self.prepsvc = UpdatePrepService(self.cfg['repo_access'])
        else:
            self.log.warning("repo_access not configured; can't support updates!")

        self.fileExaminer = None
        self.fileExaminer_autolaunch = False
        if asyncexamine:
            self.fileExaminer = self._AsyncFileExaminer(self)
            self.fileExaminer_autolaunch = True

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
        locs = self.cfg.get('pod_locations', [ DEF_MIDAS_POD_FILE ])
        for loc in locs:
            for indir in reversed(self._indirs):
                path = os.path.join(indir, loc)
                if os.path.exists(path):
                    return path
        raise PODError("POD file not found in expected locations: "+str(locs),
                       sys=self)

    def _set_pod_file(self):
        self.inpodfile = self.find_pod_file()

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
        podlocs = self.cfg.get('pod_locations', [ DEF_MIDAS_POD_FILE ])
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
                    
                    if f.startswith('.') or f.startswith('_') or \
                       os.path.join(reldir,f) in podlocs:
                        # skip dot-files and pod files written by MIDAS
                        continue

                    datafiles[os.path.join(reldir, f)] = os.path.join(dir, f)

        return datafiles

    def _merger_for(self, convention, objtype):
        return self._merger_factory.make_merger(convention, objtype)

    def ensure_preparation(self, nodata=True):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP, ready for annotation 
        and preservation.  

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.  In this implementation, the 
                            default is True.
        """
        updateneeded = self.ensure_base_bag()
        self.ensure_res_metadata(updateneeded)
        self.ensure_data_files(nodata, updateneeded)
        self.ensure_subcoll_metadata()
        if self.fileExaminer and self.fileExaminer_autolaunch == "sync":
            self.log.info("autolaunch=sync; running examiner syncronously")
            self.fileExaminer.run()
        self.resmd = self.bagbldr.bag.nerdm_record(True)

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
            self.log.info("Refreshing previously established working bag")
            return False

        elif self.prepsvc:
            self.log.debug("Looking for previously published version of bag")

            prepper = self.prepsvc.prepper_for(self.name,
                                               log=self.log.getChild("prepper"))

            if prepper.create_new_update(self.bagdir):
                self.log.info("Working bag initialized with metadata from previous "+
                         "publication.")

        if not os.path.exists(self.bagdir):
            self.bagbldr.ensure_bag_structure()

            if self.midasid.startswith("ark:/"+ARK_NAAN+"/"):
                # new-style EDI ID is a NIST ARK identifier; use it as our SIP id
                id = self.midasid
            else:
                # support deprecated 32+-character EDI ID: convert to ARK ID
                log.warn("Minting ID for (deprecated) Non-ARK EDI-ID: "+
                         self.name)
                id = self._mint_id(self.midasid)

            self.bagbldr.assign_id( id )

        return True
                
    def ensure_res_metadata(self, force=False):
        """
        copy over, if necessary, the latest version of the POD metadata to 
        the output bag and convert it to NERDm.  This method will attempt to 
        determine if the POD metadata from the SIP directory has been updated
        since resource metadata was last set; if not, the resource metadata 
        will not be updated unless force=True.
        """
        if not self.inpodfile:
            self._set_pod_file()
        self.bagbldr.ensure_bagdir()
        outpod = self.bagbldr.bag.pod_file()
        outnerd = self.bagbldr.bag.nerd_file_for("")

        update = force
        if not update:
            update = not os.path.exists(outpod) or not os.path.exists(outnerd)
        
        if not update:
            # mod dates; input is newer, we'll update
            instamp = moddate_of(self.inpodfile)
            update = instamp > moddate_of(outpod)
            if update:
                self.log.info("Detected change in POD file (by date); updating.")

        if not update:
            # we'll double check with the checksum in case mod dates are
            # not accurate
            update = checksum_of(self.inpodfile) != checksum_of(outpod)
            if update:
                self.log.info("Detected change in POD file (by checksum); updating.")

        if update:
            podnerd = self.bagbldr.add_ds_pod(self.inpodfile, convert=True,
                                              savefilemd=False)
            for cmp in podnerd.get('components', []):
                if cmp.get('filepath'):
                    # Before we update the metadata file, let's check to see
                    # if the previous one is older than the input file it
                    # describes
                    fileupdated = False
                    srcpath = self.find_source_file_for(cmp['filepath'])
                    if srcpath:
                        nf = self.bagbldr.bag.nerd_file_for(cmp['filepath'])
                        if not os.path.exists(nf) or \
                           moddate_of(srcpath) > moddate_of(nf):
                            fileupdated = True
                    
                    # FIX: what if someone tries to change a file to a
                    # subcollection or vice versa?
                    self.bagbldr.update_metadata_for(cmp['filepath'], cmp)
                    if fileupdated:
                        self._mark_filepath_unsynced(cmp['filepath'])

            # Now delete distributions that are no longer in the resource
            def has_cmp_with_path(comps, path):
                for c in comps:
                    if c.get('filepath','') == path:
                        return True
                return False
                
            resmd = self.bagbldr.bag.nerdm_record(False)
            for cmp in resmd.get('components', []):
                if any([(':DataFile' in t or ':ChecksumFile' in t)
                        for t in cmp.get('@type',[])]) and \
                   cmp.get('filepath') and \
                   not has_cmp_with_path(podnerd.get('components', []),
                                         cmp['filepath']):
                    self.bagbldr.remove_component(cmp['filepath'], True)

            # enhance references (if desired)
            if self.cfg.get('enrich_refs', False):
                self.log.debug("Will enrich references as able")
                synchronize_enhanced_refs(self.bagbldr,
                                          config=self.cfg.get('doi_resolver'),
                                          log=self.log)

        self.resmd = self.bagbldr.bag.nerdm_record(True)

        # ensure an initial version
        if 'version' not in self.resmd:
            self.resmd['version'] = "1.0.0"
            self.bagbldr.update_annotations_for('',
                                            {'version': self.resmd["version"]})

        self.datafiles = self.registered_files()


    def ensure_data_files(self, nodata=True, force=False):
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
        """
        if not self.resmd:
            # We need to have processed the POD file to know which
            # data files from the SIP directory to process
            self.ensure_res_metadata()

        for destpath, srcpath in self.datafiles.items():
            fforce = force
            if not fforce:
                dfmd = self.bagbldr.bag.nerd_metadata_for(destpath)
                fforce = 'size' not in dfmd or 'checksum' not in dfmd
            self.ensure_file_metadata(srcpath, destpath, fforce)

            if not nodata:
                self.bagbldr.add_data_file(destpath, srcpath, False,
                                           self.hardlinkdata)

        if self.fileExaminer and self.fileExaminer_autolaunch:
            self.log.info("Launching file examiner thread")
            self.fileExaminer.launch()
        else:
            self._check_checksum_files()

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
        
    def ensure_file_metadata(self, inpath, destpath, force=False):
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
        elif moddate_of(inpath) > moddate_of(nerdfile):
            # data file is newer; update its metadata
            update = True
            self.log.info("Detected change in data file (by date); updating %s",
                     destpath)
        elif os.stat(inpath).st_size \
             < self.cfg.get('update_by_checksum_size_lim', 0):
            # not implemented yet
            pass

        if update:
            md = self.bagbldr.describe_data_file(inpath, destpath,
                                                 not self.fileExaminer)

            if self.fileExaminer:
                md["__status"] = "in progress"
                
                # the file examiner will calculate the file's checksum
                # asynchronously; for now though, see if there is an associated
                # checksum file provided by midas.  
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
            if self.fileExaminer:
                # asyncronously examine the files for additional, extracted
                # metadata (and checksum)
                self.fileExaminer.add(inpath, destpath)
            else:
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
        threads = set()

        def __init__(self, bagger):
            self.bagger = bagger
            self.files = OrderedDict()
            self.thread = None
            self.stop_logging = False

        def add(self, location, filepath):
            self.files[filepath] = location

        def _prep(self):
            if self.running():
                log.debug("File examiner thread is still running")
                return False
            self._unregister()
            self.thread = self._Thread(self)
            self._register()
            return True

        def _register(self):
            self.threads.add(self.thread)
        def _unregister(self):
            if self.running() and self.thread in self.threads:
                self.threads.remove(self.thread)
            self.thread = None
        def __del__(self):
            self._unregister(self.thread)

        def running(self):
            return self.thread and self.thread.is_alive()

        def launch(self, stop_logging=False):
            if self._prep():
                self.stop_logging = stop_logging
                self.thread.start()

        def run(self):
            if self._prep():
                self.stop_logging = False
                self.thread.run()

        def finish(self):
            if self.stop_logging:
                self.bagger.bagbldr.disconnect_logfile()

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
                md = self.bagger.bagbldr.update_metadata_for(filepath, md, ct,
                                   "async metadata update for file, "+filepath)
                if '__status' in md:
                    del md['__status']
                    self.bagger.bagbldr.replace_metadata_for(filepath, md, '')
                self.bagger._mark_filepath_synced(filepath)

            except Exception as ex:
                log.error("%s: Failed to extract file metadata: %s"
                          % (location, str(ex)))

        @classmethod
        def wait_for_all(cls, timeout=10):
            log.info("Waiting for file examiner threads to finish")
            done = set(cls.threads)
            for thrd in cls.threads:
                try:
                    thrd.join(timeout)
                    if thrd.is_alive():
                        log.warn("Thread waiting timed out: "+str(thrd))
                    else:
                        done.add(thrd)
                except RuntimeError as ex:
                    log.warn("Skipping wait for thread, "+str(thrd)+
                             ", for deadlock danger")
            for thrd in done:
                try:
                    cls.threads.remove(thrd)
                except KeyError:
                    pass
            return len(cls.threads) == 0

        class _Thread(threading.Thread):
            def __init__(self, exmnr):
                super(MIDASMetadataBagger._AsyncFileExaminer._Thread, self). \
                    __init__()
                self.exif = exmnr
            def run(self):
                # time.sleep(0.1)
                while self.exif.files:
                    self.exif.examine_next()
                self.exif.finish()
        

        
class PreservationBagger(SIPBagger):
    """
    This class finalizes the bagging of data provided by MIDAS into the final 
    bag for preservation.  

    This class uses the MIDASMetadataBagger to create/update the initial bag 
    containing the NERDm metadata and ancillary data to reflect the latest 
    copies of the files provided through MIDAS.  This class then completes
    the bag by including the data files and all remaining, required ancillary 
    files.  

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
    :prop pod_locations  list of str (["_pod.json"]):  a list of relative file 
                                 paths where the POD dataset file might be 
                                 found, in order of preference.  
    :prop update_by_checksum_size_lim int (0):  a size limit in bytes for which 
                                 files less than this will be checked to see 
                                 if it has changed (not yet implemented).
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
    """

    def __init__(self, midasid, bagparent, reviewdir, mddir,
                 config=None, minter=None, asupdate=None, sipdirname=None):
        """
        Create an SIPBagger to operate on data provided by MIDAS.

        :param midasid   str:  the identifier provided by MIDAS, used as the 
                               name of the directory containing the data.
        :param bagparent str:  the path to the directory where the preservation
                               bag should be written.  
        :param reviewdir str:  the path to the directory containing submitted
                               datasets in the review state.
        :param mddir     str:  the path to the directory that may contain a
                               metadata bag prepared for previewing or updating
                               the landing page.
        :param config   dict:  a dictionary providing configuration parameters
        :param minter IDMinter: a minter to use for minting new identifiers.
        :param asupdate bool:  if set to true, the caller believes this bagger 
                               should be creating an update to an existing AIP;
                               if false, the caller believes this is a new AIP.
                               If this believe does not correspond with the 
                               actual contents of the repository, an exception 
                               is raised when the attempt to process the SIP is 
                               made.  If None (default), no check is done; if 
                               an AIP already exists in the repository, this 
                               bagger creates an update.  
        :param sipdirname str: a relative directory name to look for that 
                               represents the SIP's directory.  If not provided,
                               the directory is determined based on the provided
                               MIDAS ID.  
        """
        self.midasid = midasid
        self.name = midasid_to_bagname(midasid)
        self.mddir = mddir
        self.reviewdir = reviewdir
        self.asupdate = asupdate   # can be None
        self._minter = minter      # can be None

        indirname = sipdirname
        if not indirname:
            indirname = _midadid_to_dirname(midasid, log)
        self.indir = os.path.join(self.reviewdir, indirname)

        if not os.path.exists(self.indir):
            raise SIPDirectoryNotFound(self.indir)

        if config is None:
            config = {}
        super(PreservationBagger, self).__init__(bagparent, config)

        # check for needed configuration
        if self.cfg.get('check_data_files', True) and \
           not self.cfg.get('store_dir'):
            raise ConfigurationException("PreservationBagger: store_dir " +
                                         "config param needed")

        # do a sanity check on the bag parent directory
        if not self.cfg.get('relative_to_indir', False):
            sipdir = os.path.abspath(self.indir)
            if sipdir[-1] != os.sep:
                sipdir += '/'
            if os.path.abspath(self.bagparent).startswith(sipdir):
                if self.cfg.get('relative_to_indir') == False:
                    # you said it was not relative, but it sure looks that way
                    raise ConfigurationException("'relative_to_indir'=False but"
                                                 +" bag dir (" + self.bagparent+
                                                 ") appears to be below "+
                                                 "submitted directory (" +
                                                 self.sipdir+")")
                # bagparent is inside sipdir
                self.bagparent = os.path.abspath(self.bagparent)[len(sipdir):]
                self.cfg['relative_to_indir'] = True

        if self.cfg.get('relative_to_indir'):
            self.bagparent = os.path.join(self.indir, self.bagparent)
                
        self.ensure_bag_parent_dir()

        usenm = self.name
        if len(usenm) > 11:
            usenm = usenm[:4]+"..."+usenm[-4:]
        self.siplog = log.getChild(usenm)

        bldcfg = self.cfg.get('bag_builder', {})
        if 'ensure_component_metadata' not in bldcfg:
            # default True can mess with annotations
            bldcfg['ensure_component_metadata'] = False  
        self.bagbldr = BagBuilder(self.bagparent,
                                  self.form_bag_name(self.name), bldcfg,
                                  logger=self.siplog)

    @property
    def bagdir(self):
        """
        The path to the output bag directory.
        """
        return self.bagbldr.bagdir

    def ensure_metadata_preparation(self):
        """
        prepare the NERDm metadata.  

        This uses the MIDASMetadataBagger class to convert the MIDA POD data 
        into NERDm and to extract metadata from the uploaded files.  
        """
        # start by bagging up the metadata.  If this was done before (prior to
        # final preservation time), the previous metadata bag will be updated.
        parent = os.path.dirname(self.indir)
        sipdir = os.path.basename(self.indir)
        mdbagger = MIDASMetadataBagger(self.midasid, self.mddir, parent,
                                       config=self.cfg, minter=self._minter,
                                       sipdirname=sipdir)

        if self.asupdate is not None and mdbagger.prepsvc:
            prepper = mdbagger.prepsvc.prepper_for(self.name, log=self.siplog)

            # if asupdate is set (to true or false), check for the existance 
            # of the target AIP:
            if prepper.aip_exists() != bool(self.asupdate):
                # actual state does not match caller's expected state
                if self.asupdate:
                    msg = self.name + \
                          ": AIP with this ID does not exist in repository"
                else:
                    msg = self.name + \
                          ": AIP with this ID already exists in repository"
                raise PreservationStateError(msg, not self.asupdate)

        mdbagger.prepare(nodata=True)
        self.datafiles = mdbagger.datafiles
        mdbagger._clear_all_unsynced_marks()
        mdbagger.bagbldr._unset_logfile()

        # copy the contents of the metadata bag into the final preservation bag
        if os.path.exists(self.bagdir):
            # note: caller should be responsible for locking the preservation
            # of the SIP and cleaning up afterward.  Thus, this case should
            # not really occur
            log.warn("Removing previous version of preservation bag, %s",
                     self.bagbldr.bagname)
            if os.path.isdir(self.bagdir):
                utils.rmtree(self.bagdir)
            else:
                shutil.remove(self.bagdir)
        shutil.copytree(mdbagger.bagdir, self.bagdir)
        
        # by ensuring the output preservation bag directory, we set up logging
        self.bagbldr.ensure_bagdir()
        self.bagbldr.log.info("Preparing final bag for preservation as %s",
                              os.path.basename(self.bagdir))

    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """
        locs = self.cfg.get('pod_locations', [ DEF_MIDAS_POD_FILE ])
        for loc in locs:
            path = os.path.join(self.indir, loc)
            if os.path.exists(path):
                return path
        raise PODError("POD file not found in expected locations: "+str(locs),
                       sys=self)

    def ensure_preparation(self, nodata=False):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP, ready for annotation 
        and preservation.  

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.
        """
        self.ensure_metadata_preparation()
        if not nodata:
            self.add_data_files()
        

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
        return bagutils.form_bag_name(dsid, bagseq, dsver, bver, namefmt=fmt)

    def add_data_files(self):
        """
        link in copies of the dataset's data files
        """
        for dfile, srcpath in self.datafiles.items():
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
        if lock:
            self.ensure_filelock()
            with self.lock:
                return self._make_bag_impl()

        else:
            return self._make_bag_impl()
    
    def _make_bag_impl(self):
        # this is intended to be called from make_bag(), with or with out
        # lock on the output bag.
        
        self.prepare(nodata=False)

        finalcfg = self.cfg.get('bag_builder', {}).get('finalize', {})
        if finalcfg.get('ensure_component_metadata') is None:
            finalcfg['ensure_component_metadata'] = False

        ver = self.finalize_version()

        # rename the bag for a proper version and sequence number
        seq = self._determine_seq()
        newname = self.form_bag_name(self.name, seq, ver)
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
        if finalcfg.get('check_data_files', True):
            # this will raise an exception if any issues are found
            self._check_data_files(finalcfg.get('data_checker', {}))

        return self.bagbldr.bagdir

    def finalize_version(self, update_reason=None):
        """
        update the NERDm version metadatum to reflect the changes set by this
        SIP.  If this SIP represents the initial submission for a dataset, the
        version is set to "1.0.0"; if it represents an update to a previously 
        published dataset, the version will be incremented based on the 
        contents included in the SIP and PDR policy.
        """
        bag = self.bagbldr.bag
        mdata = self.bagbldr.bag.nerdm_record(True)
        (newver, uptype) = self._determine_updated_version(mdata, bag)
        self.siplog.debug('Setting final version to "%s"', newver)
        
        annotf = self.bagbldr.bag.annotations_file_for('')
        if os.path.exists(annotf):
            adata = utils.read_nerd(annotf)
        else:
            adata = OrderedDict()
        adata['version'] = newver
        relhist = mdata.get('releaseHistory')
        if relhist is None:
            relhist = bagutils.create_release_history_for(mdata['@id'])
            relhist['hasRelease'] = mdata.get('versionHistory', [])
        verhist = relhist['hasRelease']

        if uptype != _NO_UPDATE and newver != mdata['version'] and \
           ('issued' in mdata or 'modified' in mdata) and \
           not any([h['version'] == newver for h in verhist]):
            issued = ('modified' in mdata and mdata['modified']) or \
                     mdata['issued']
            verhist.append(OrderedDict([
                ('version', newver),
                ('issued', issued),
                ('@id', mdata['@id']),
                ('location', 'https://'+pdr.PDR_PUBLIC_SERVER+ \
                             re.sub(r'\.rel$', ".v"+re.sub(r'\.','_', adata['version']), relhist['@id']))
            ]))
            if update_reason is None:
                if uptype == _MDATA_UPDATE:
                    update_reason = 'metadata update'
                elif uptype == _DATA_UPDATE:
                    update_reason = 'data update'
                else:
                    update_reason = ''
            verhist[-1]['description'] = update_reason
            adata['releaseHistory'] = relhist
        
        utils.write_json(adata, annotf)

        return newver

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

    def determine_updated_version(self, mdrec=None, bag=None):
        """
        determine the proper policy-specified version for this SIP based on
        the given NERD metadata record for the SIP and the current contents 
        of the AIP bag.  

        :param dict mdrec:  the NERDm metadata for the entire dataset to consider
                            when determining the new version;  if not provided,
                            the current stored NERDm data will be read in.
        :param NISTBag bag: the NISTBag instance for the bag to examine; if 
                            not provided, the current pending AIP bag will be 
                            examined.
        """
        return self._determine_updated_version(mdrec, bag)[0]

    def _determine_updated_version(self, mdrec=None, bag=None):
        if not bag:
            bag = NISTBag(self.bagbldr.bagdir)
        if not mdrec:
            mdrec = bag.nerdm_record(True)
        
        oldver = mdrec.get('version', "1.0.0")
        ineditre = re.compile(r'^(\d+(.\d+)*)\+ \(.*\)')
        matched = ineditre.search(oldver)
        if matched:
            # the version is marked as "in edit", indicating that this
            # is an update to a previously published version.
            oldver = matched.group(1)
            ver = [int(f) for f in oldver.split('.')]
            for i in range(len(ver), 3):
                ver.append(0)

            # if there are files under the data directory, consider this a
            # data update, which increments the second field.
            for dir, subdirs, files in os.walk(bag.data_dir):
                if len(files) > 0:
                    # found a file
                    ver[1] += 1
                    ver[2] = 0
                    return (".".join([str(v) for v in ver]), _DATA_UPDATE)

            # otherwise, this is a metadata update, which increments the
            # third field.
            ver[2] += 1
            return (".".join([str(v) for v in ver]), _MDATA_UPDATE)

        # otherwise, this looks like a first-time SIP submission; take the
        # version string as is.
        return (oldver, _NO_UPDATE)
            

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
            "store_dir":  self.cfg.get('store_dir')
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

        
