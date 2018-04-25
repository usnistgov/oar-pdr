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
import os, errno, logging, re, json, shutil
from abc import ABCMeta, abstractmethod, abstractproperty

from .base import SIPBagger, moddate_of, checksum_of, read_nerd, read_pod
from .base import sys as _sys
from ..bagit.builder import BagBuilder, NERDMD_FILENAME, FILEMD_FILENAME
from ... import def_merge_etcdir, utils
from .. import (SIPDirectoryError, SIPDirectoryNotFound, AIPValidationError,
                ConfigurationException, StateException, PODError)
from nistoar.nerdm.merge import MergerFactory

# _sys = PreservationSystem()
log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)

DEF_MBAG_VERSION = "0.3"
DEF_MIDAS_POD_FILE = "_pod.json"
SUPPORTED_CHECKSUM_ALGS = [ "sha256" ];
DEF_CHECKSUM_ALG = "sha256"

def _midadid_to_dirname(midasid, log=None):
    out = midasid
    if len(midasid) > 32:
        # MIDAS drops the first 32 chars. of the ediid for the data
        # directory names
        out = midasid[32:]
    elif log:
        log.warn("Unexpected MIDAS ID (too short): "+midasid)
    return out

class MIDASMetadataBagger(SIPBagger):
    """
    This class will migrate metadata provided by MIDAS into a working bag
    
    application by re-organizing its contents into a working bag

    Note that user-provided datafiles are added to the output directory as a 
    hard link.  That is, no bytes are copied.  Metadata data files are copied.

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
    :prop conponent_merge_convention str ("dev"): the merge convention name to 
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
                 minter=None):
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
        """
        self.name = midasid
        self.state = 'upload'
        self._indirs = []

        # ensure we have at least one readable input directory
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
                log.debug("Found input dir: %s", indir)
            else:
                log.debug("Candidate dir does not exist: %s", indir)    

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

        self.bagbldr = BagBuilder(self.bagparent, self.name,
                                  self.cfg.get('bag_builder', {}),
                                  minter=minter,
                                  logger=log.getChild(self.name[:8]+'...'))
        mergeetc = self.cfg.get('merge_etc', def_merge_etcdir)
        if not mergeetc:
            raise StateException("Unable to locate the merge configuration "+
                                 "directory")
        self._merger_factory = MergerFactory(mergeetc)

        self.hardlinkdata = self.cfg.get('hard_link_data', True)
        self.inpodfile = None
        self.resmd = None
        self.datafiles = None

        self.ensure_bag_parent_dir()

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

    def ensure_res_metadata(self):
        """
        copy over, if necessary, the latest version of the POD metadata to 
        the output bag and convert it to NERDm.
        """
        if not self.inpodfile:
            self._set_pod_file()
        outpod = self.bagbldr.pod_file()
        outnerd = self.bagbldr.nerdm_file_for("")
        
        instamp = moddate_of(self.inpodfile)
        update = not os.path.exists(outpod)
        if not update:
            # mod dates; input is newer, we'll update
            update = instamp > moddate_of(outpod)
            if update:
                log.info("Detected change in POD file (by date); updating.")
        if not update:
            # we'll double check with the checksum in case mod dates are
            # not accurate
            update = checksum_of(self.inpodfile) != checksum_of(outpod)
            if update:
                log.info("Detected change in POD file (by checksum); updating.")

        if update:
            # Note: setting savefilemd=True because there may be files that are
            # part of the data set but don't exist in the input directories.
            # These could be files available via external URLs or files preserved
            # as part of a previous version.  
            self.resmd = self.bagbldr.add_ds_pod(self.inpodfile, convert=True,
                                                 savefilemd=True)
        else:
            self.resmd = read_nerd(outnerd)

    def data_file_inventory(self):
        """
        get a list of the data files available to be part of this dataset.
        This will include any accompanying hash files.

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

    def ensure_file_metadata(self, inpath, destpath, resmd=None,
                             disttype="DataFile"):
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
        :param resmd Mapping:  the NERDm resource metadata, which may include
                               a component entry for this file.  
        :param disttype str:  the default file distribution type to assign to 
                              the file (with the default default being 
                              "DataFile"); if examine is True, the type may 
                              change based on inspection of the file.  
        """
        nerdfile = self.bagbldr.nerdm_file_for(destpath)

        update = False
        if not os.path.exists(nerdfile):
            update = True
            log.info("Initializing metadata for datafile, %s", destpath)
        elif moddate_of(inpath) > moddate_of(nerdfile):
            # data file is newer; update its metadata
            update = True
            log.info("Detected change in data file (by date); updating %s",
                     destpath)
        elif os.stat(inpath).st_size \
             < self.cfg.get('update_by_checksum_size_lim', 0):
            # not implemented yet
            pass

        nerd = None
        if resmd:
            # look for applicable metadata in the resource metadata
            comps = resmd.get('components', [])
            match = [c for c in comps if 'filepath' in c and
                                         c['filepath'] == destpath]
            if match:
                nerd = match[0]
                missing = [k for k in "size mediaType checksum".split()
                             if k not in nerd.keys()]
                if missing:
                    update = True
                    log.info("Extending file metadata for %s", destpath)
        
        if update:
            init = self.bagbldr.init_filemd_for(destpath, examine=inpath,
                                                disttype=disttype)
            if nerd:
                conv = self.cfg.get('component_merge_convention', 'dev')
                merger = self._merger_for(conv, "DataFile")
                nerd = merger.merge(nerd, init)
            else:
                nerd = init

            self.bagbldr.add_metadata_for_file(destpath, nerd, disttype=disttype)

    def _merger_for(self, convention, objtype):
        return self._merger_factory.make_merger(convention, objtype)

    def ensure_subcoll_metadata(self):
        if not self.datafiles:
            self.ensure_data_files(nodata=True)

        colls = set()
        for filepath in self.datafiles:
            collpath = os.path.dirname(filepath)
            if collpath and collpath not in colls:
                collnerd = self.bagbldr.nerdm_file_for(collpath)
                filenerd = self.bagbldr.nerdm_file_for(filepath)
                if not os.path.exists(collnerd) or \
                   (os.path.exists(filenerd) and 
                    moddate_of(collnerd) < moddate_of(filenerd)):
                      log.debug("Adding metadata for collection: %s", collpath)
                      self.bagbldr.init_collmd_for(collpath, write=True)
                      colls.add(collpath)
        

    def ensure_preparation(self, nodata=True):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP, ready for annotation 
        and preservation.  

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.  In this implementation, the 
                            default is True.
        """
        self.ensure_res_metadata()
        self.ensure_data_files(nodata)
        self.ensure_subcoll_metadata()

    def ensure_data_files(self, nodata=True):
        """
        ensure that all data files are described in the output bag as well as
        (if nodata=False) copied over.  
        """
        self.bagbldr.ensure_bag_structure()

        # get the list of data files found in the input directories
        self.datafiles = self.data_file_inventory()

        # Now clean-up files that have effectively been removed.
        #
        # for this we need a list of data files described in the POD record;
        # distribution records have not necessarily been created for files
        # currently in the input directories (i.e. those in self.datafiles)
        fdists = self.pod_file_distribs()

        # what files are in the bag now but not in the input area and
        # were not enumerated in the input POD file?
        remove = set()
        mdatadir = os.path.join(self.bagdir,"metadata")
        for dir, subdirs, files in os.walk(mdatadir):
            if dir == mdatadir:
                continue
            if NERDMD_FILENAME in files:
                filepath = dir[len(mdatadir)+1:]
                if filepath not in self.datafiles and \
                   filepath not in fdists:
                    # found a component with this filepath, but is it a datafile?
                    mdata = read_nerd(os.path.join(dir,NERDMD_FILENAME))
                    comptypes = mdata.get("@type", [])
                    if any([":DownloadableFile" in t for t in comptypes]):
                        # yes, it is a data file
                        log.debug("Will remove dropped data file: %s", filepath)
                        remove.add(filepath)

        # add all the files from the input area
        for destpath, inpath in self.datafiles.items():
            disttype = "DataFile"
            if destpath.endswith('.'+DEF_CHECKSUM_ALG) and \
               os.path.splitext(destpath)[0] in self.datafiles:
                # this looks like a checksum file for one of the data files
                if not self.cfg.get('checksum_files', True):
                    continue
                # save as a ChecksumFile distribution
                disttype = "ChecksumFile"
                log.debug("Adding checksum file: %s", destpath)
            else:
                log.debug("Adding submitted data file: %s", destpath)

            self.ensure_file_metadata(inpath, destpath, self.resmd, disttype)

            if not nodata:
                self.bagbldr.add_data_file(destpath, inpath,
                                           self.hardlinkdata, initmd=False)

        # and remove the removed files (and trim emptied subcollections)
        for filepath in remove:
            self.bagbldr.remove_component(filepath, True)

        self._check_checksum_files()

    def _check_checksum_files(self):
        # This file will look all of the files that have been identified as
        # ChecksumFiles to see if the value they contain matches the value
        # stored in the metadata for the datafile it is associated with.  If
        # they do not match, the valid metadata flag for the checksum file
        # will be set to false.
        for df in self.datafiles:
            csnerdf = self.bagbldr.nerdm_file_for(df)
            csnerd = read_nerd(csnerdf)
            if any([":ChecksumFile" in t for t in csnerd.get("@type",[])]):
                dfpath = self.datafiles[df]
                try:
                    with open(dfpath) as fd:
                        cs = fd.readline().split()[0]
                except Exception as ex:
                    log.warn(df+": unexpected contents in checksum file (%s)" % \
                             str(ex))
                    continue

                # this data file is a checksum file
                described = csnerd.get("describes","cmps/")[5:]
                if described in self.datafiles:
                    nerdf = self.bagbldr.nerdm_file_for(described)
                    nerd = read_nerd(nerdf)

                    if nerd.get('checksum',{}).get('hash','') == cs:
                        log.debug(df+": hash value looks valid")
                        csnerd['valid'] = True
                    else:
                        log.warn(df+": hash value in file looks invalid")
                        csnerd['valid'] = False
                    self.bagbldr._write_json(csnerd, csnerdf)

    def pod_file_distribs(self):
        """
        return a list of filepaths for files described in the POD record.
        This list may include files not in one of the input disks but is 
        available from an external URL.  This may include MIDAS-generated
        checksum (sha256) files.  
        """
        out = []
        if self.bagbldr and self.bagbldr._bag:
            podf = self.bagbldr._bag.pod_file()
            if os.path.exists(podf):
                pod = self.bagbldr._bag.read_pod(podf)
                nerd = self.bagbldr.pod2nrd.convert_data(pod, "ZZZ")
                if 'components' in nerd:
                    out = [c['filepath'] for c in nerd['components']
                                         if 'filepath' in c]
        return out

        
class PreservationBagger(SIPBagger):
    """
    This class finalizes the bagging of data provided by MIDAS into the final 
    bag for preservation.  

    This class uses the MIDASMetadataBagger to update the NERDm metadata to 
    latest copies of the files provided through MIDAS.  It then builds the 
    final bag, including the data files and all required ancillary files.  

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
                 config=None, minter=None):
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
        """
        self.name = midasid
        self.mddir = mddir
        self.minter = minter
        self.reviewdir = reviewdir

        self.indir = os.path.join(self.reviewdir,
                                  _midadid_to_dirname(midasid, log))
        if not os.path.exists(self.indir):
            raise SIPDirectoryNotFound(self.indir)

        if config is None:
            config = {}
        super(PreservationBagger, self).__init__(bagparent, config)

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

        self.bagbldr = BagBuilder(self.bagparent,
                                  self.form_bag_name(self.name),
                                  self.cfg.get('bag_builder', {}),
                                  minter=minter,
                                  logger=log.getChild(self.name[:8]+'...'))
        

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
        mdbagger = MIDASMetadataBagger(self.name, self.mddir, self.reviewdir,
                                       config=self.cfg, minter=self.minter)
        mdbagger.prepare(nodata=True)
        self.datafiles = mdbagger.datafiles

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
        
        # by ensuring the output preservation bag directory, we set up loggning
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

    def form_bag_name(self, dsid, bagseq=0):
        """
        return the name to use for the working bag directory
        """
        fmt = self.cfg.get('bag_name_format', "{0}.mbag{1}-{2}")
        bver = self.cfg.get('mbag_version', DEF_MBAG_VERSION)
        bver = re.sub(r'\.', '_', bver)
        return fmt.format(dsid, bver, bagseq)

    def add_data_files(self):
        """
        link in copies of the dataset's data files
        """
        for dfile, srcpath in self.datafiles.items():
            self.bagbldr.add_data_file(dfile, srcpath, True, False)

    
    def make_bag(self):
        """
        convert the input SIP into a bag ready for preservation.  More 
        specifically, the result will be a bag directory with finalized 
        content, ready for serialization.  

        :return str:  the path to the finalized bag directory
        """
        self.prepare(nodata=False)

        finalcfg = self.cfg.get('bag_builder', {}).get('finalize', {})
        if finalcfg.get('ensure_component_metadata') is None:
            finalcfg['ensure_component_metadata'] = False

        self.bagbldr.finalize_bag(finalcfg)
        if finalcfg.get('validate', True):
            # this will raise an exception if any issues are found
            self._validate(finalcfg.get('validator', {}))

        return self.bagbldr.bagdir

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
            log.warn("Bag Validation issues detected for id="+self.name)
            for iss in issues:
                if iss.type == iss.ERROR:
                    log.error(str(iss))
                    for comm in iss.comments:
                        log.error(comm)
                elif iss.type == iss.WARN:
                    log.warn(str(iss))
                else:
                    log.info(str(iss))

            if raiseon:
                raise AIPValidationError("Bag Validation errors detected",
                                         errors=[str(i) for i in issues])

        else:
            log.info("%s: bag validation completed without issues",
                     self.bagbldr.bagname)
