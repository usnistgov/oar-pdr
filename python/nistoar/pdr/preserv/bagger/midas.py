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
import os, errno, logging, re, json
from abc import ABCMeta, abstractmethod, abstractproperty

from .base import SIPBagger, moddate_of, checksum_of, read_nerd, read_pod
from .base import PreservationSystem
from ..bagit.builder import BagBuilder, NERDMD_FILENAME
from ... import def_merge_etcdir
from .. import (SIPDirectoryError, SIPDirectoryNotFound, 
                ConfigurationException, StateException, PODError)
from nistoar.nerdm.merge import MergerFactory

_sys = PreservationSystem()
log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)

DEF_MBAG_VERSION = "0.2"
DEF_MIDAS_POD_FILE = "_pod.json"

class MIDASMetadataBagger(SIPBagger):
    """
    This class will migrate metadata provided by MIDAS into a working bag
    
    application by re-organizing its contents into a working bag

    Note that user-provided datafiles are added to the output directory as a 
    hard link.  That is, no bytes are copied.  Metadata data files are copied.

    This class can take a configuration dictionary on construction; the 
    following parameters are supported:
    :param bag_builder     dict: a set of parameters to pass to the BagBuilder
                                 object used to populate the output bag (see
                                 BagBuilder class documentation for supported
                                 parameters).
    :param merge_etc       str:  the path to the directory containing the 
                                 metadata merge rule configurations.  If not
                                 set, the directory will be searched for in 
                                 some possible default locations.
    :param hard_link_data bool:  if True, copy data files into the bag using
                                 a hard link whenever possible (default: True)
    :param pod_locations  list of str:  a list of relative file paths where 
                                 the POD dataset file might be found, in 
                                 order of preference.  (Default: ["_pod.json"])
    :param update_by_checksum_size_lim int:  a size limit in bytes for which 
                                 files less than this will be checked to see 
                                 if it has changed (not yet implemented).
    :param conponent_merge_convention str: the merge convention name to use to
                                 merge MIDAS-provided component metadata with 
                                 the PDR's initial component metadata (default:
                                 'dev').
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
        for dir in (reviewdir, uploaddir):
            if not dir:
                continue
            indir = os.path.join(dir, midasid)
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
            self.resmd = self.bagbldr.add_ds_pod(self.inpodfile, convert=True,
                                                 savefilemd=False)
        else:
            self.resmd = read_nerd(outnerd)

    def data_file_inventory(self):
        """
        get a list of the data files available to be part 
        of this dataset.

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
                    if f.startswith('.') or \
                       os.path.join(reldir,f) in podlocs:
                        # skip dot-files and pod files written by MIDAS
                        continue
                    datafiles[os.path.join(reldir, f)] = os.path.join(dir, f)

        return datafiles

    def ensure_file_metadata(self, inpath, destpath, resmd=None):
        """
        examine the given file and update the file metadata if necessary.

        If the file has an file modication time later than the corresponding 
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
        """
        nerdfile = self.bagbldr.nerdm_file_for(destpath)

        update = False
        if not os.path.exists(nerdfile) or \
           moddate_of(inpath) > moddate_of(nerdfile):
            # data file is newer; update its metadata
            update = True
            log.info("Detected change in data file (by date); updating " +
                     destpath)
        elif os.stat(inpath).st_size \
             < self.cfg.get('update_by_checksum_size_lim', 0):
            # not implemented yet
            pass
        
        if update:
            nerd = self.bagbldr.init_filemd_for(destpath, examine=inpath)

            if resmd:
                # look for applicable metadata in the resource metadata
                comps = resmd.get('components', [])
                match = [c for c in comps if c['@id'] == nerd['@id']]
                if match:
                    conv = self.cfg.get('component_merge_convention', 'dev')
                    merger = self._merger_for(conv, "DataFile")
                    nerd = merger.merge(match[0], nerd)

            self.bagbldr.add_metadata_for_file(destpath, nerd)

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
        self.datafiles = self.data_file_inventory();

        # what files are in the bag now but not in the input area?
        remove = set()
        mdatadir = os.path.join(self.bagdir,"metadata")
        for dir, subdirs, files in os.walk(mdatadir):
            if dir == mdatadir:
                continue
            if NERDMD_FILENAME in files:
                filepath = dir[len(mdatadir)+1:]
                if filepath not in self.datafiles:
                    # found a component with this filepath, but is it a datafile?
                    mdata = read_nerd(os.path.join(dir,NERDMD_FILENAME))
                    if any([":DataFile" in t for t in mdata.get("@type", [])]):
                        # yes, it is a data file
                        log.debug("Will remove dropped data file: %s", filepath)
                        remove.add(filepath)

        # now make sure have all the files from the input area
        for destpath, inpath in self.datafiles.items():
            log.debug("Adding submitted data file: %s", destpath)
            self.ensure_file_metadata(inpath, destpath, self.resmd)

            if not nodata:
                self.bagbldr.add_data_file(destpath, inpath,
                                           self.hardlinkdata, initmd=False)

        # and remove the removed files (and trim emptied subcollections)
        for filepath in remove:
            self.bagbldr.remove_component(filepath, True)

        
class PreservationBagger(SIPBagger):
    """
    This class finalizes the bagging of data provided by MIDAS into the final 
    bag for preservation.  

    This class uses the MIDASMetadataBagger to update the NERDm metadata to 
    latest copies of the files provided through MIDAS.  It then builds the 
    final bag, including the data files and all required ancillary files.  
    """

    def __init__(self, midasid, bagparent, reviewdir, mddir,
                 config={}, minter=None):
                 
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
        self.indir = reviewdir
        self.mddir = mddir
        self.minter = minter

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

        self.bagbldr = BagBuilder(self.bagparent,
                                  self.form_bag_name(self.midasid),
                                  self.cfg.get('bag_builder', {}),
                                  minter=minter,
                                  logger=log.getChild(self.name[:8]+'...'))
        

        self.ensure_bag_parent_dir()

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
        mdbagger = MIDASMetadataBagger(self.midasid, self.mddir, self.indir,
                                       config=self.cfg, self.minter)
        mdbagger.prepare()
        self.datafiles = mdbagger.datafiles

        # copy the contents of the metadata bag into the final preservation bag
        if os.path.exists(self.bagdir):
            # note: caller should be responsible for locking the preservation
            # of the SIP and cleaning up afterward.  Thus, this case should
            # not really occur
            log.warn("Removing previous version of preservation bag, %s",
                     self.bagbldr.bagname)
            if os.path.isdir(self.bagdir):
                shutil.rmtree(self.bagdir)
            else:
                shutil.remove(self.bagdir)
        shutil.copytree(mdbagger.bagdir, self.bagdir)
        
        # by ensuring the output preservation bag directory, we set up loggning
        self.bagbldr.ensure_bagdir()

    def form_bagdir_name(self, dsid, bagseq=0):
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

    
