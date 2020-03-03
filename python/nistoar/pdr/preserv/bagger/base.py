"""
This module provides the base interface and implementation for the SIPBagger
infrastructure.  At the center is the SIPBagger class that serves as an 
abstract base for subclasses that understand different input sources.
"""
import os, json, filelock
from collections import OrderedDict
from abc import ABCMeta, abstractmethod, abstractproperty

from .. import PreservationSystem, sys, read_nerd, read_pod, read_json, write_json
from .. import (SIPDirectoryError, PDRException, NERDError, PODError,
                StateException)
from ..bagit.builder import checksum_of
from ...config import merge_config

def moddate_of(filepath):
    """
    return a file's modification time (as a float)
    """
    return os.stat(filepath).st_mtime

class SIPBagger(PreservationSystem):
    """
    This class will prepare an SIP organized in a particular form 
    by re-organizing its contents into a working bag.  Subclasses adapt 
    different SIP format.  This abstract class provides common code.  

    SIPBagger implementations should be written to be indepodent: running 
    it mutliple times on the same input and output directories should result
    in the same end state.  That is, if run a second time and nothing is 
    different in the input directory, nothing changes in the output directory.
    If a file is added in the input directory and the prepper is rerun, that
    new file will get added to the output directory.  

    SIPBagger implementations make use of a configuration dictionary to 
    control its behavior.  Most of the supported properties are defined by 
    the specific implementation class; however, this base class supports the 
    following properties:

    :prop relative_to_indir bool (False):  If True, the output bag directory 
       is expected to be under one of the input directories; this base class
       will then ensure that it has write permission to create the output 
       directory.  If False, the bagger may raise an exception if the 
       requested output bag directory is found within an input SIP directory,
       regardless of whether the process has permission to write there.  
    """
    __metaclass__ = ABCMeta
    BGRMD_FILENAME = "__bagger.json"   # default bagger metadata file; may be overridden

    def __init__(self, outdir, config):
        """
        initialize the class by setting the input SIP directory and the 
        output working directory where the root bag directory can be created.  
        """
        self.bagparent = outdir
        self.cfg = config
        self.lock = None

    @abstractproperty
    def bagdir(self):
        """
        The path to the output bag directory.
        """
        raise NotImplemented

    def ensure_bag_parent_dir(self):
        if not os.path.exists(self.bagparent):
            if self.cfg.get('relative_to_indir'):
                try:
                    os.makedirs(self.bagparent)
                except OSError, e:
                    bagparent = self.bagparent[len(self.sipdir):]
                    raise SIPDirectoryError("unable to create working bag ("+
                                            bagparent + ") under SIP "+
                                            "dir: " + str(e), cause=e)
            else:
                raise StateException("Bag Workspace dir does not exist: " +
                                     self.bagparent)

    @abstractmethod
    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """
        raise NotImplemented

    @abstractmethod
    def ensure_preparation(self, nodata=False):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP, ready for annotation 
        and preservation.  

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.
        """
        raise NotImplemented

    def ensure_filelock(self):
        """
        if necessary, create a file lock object that can be used to prevent 
        multiple processes from trying to bag the same SIP simultaneously.
        The lock object is saved to self.lock.  
        """
        if not self.lock:
            lockfile = self.bagdir + ".lock"
            self.ensure_bag_parent_dir()
            self.lock = filelock.FileLock(lockfile)

    def prepare(self, nodata=False, lock=True):
        """
        initialize the output working bag directory by calling 
        ensure_preparation().  This operation is wrapped in the acquisition
        of a file lock to prevent multiple processes from 

        :param nodata bool: if True, do not copy (or link) data files to the
                            output directory.
        :param lock bool:   if True (default), acquire a lock before executing
                            the preparation.
        """
        if lock:
            self.ensure_filelock()
            with self.lock:
                self.ensure_preparation(nodata)

        else:
            self.ensure_preparation(nodata)

    def baggermd_file_for(self, destpath):
        """
        return the full path within the bag for bagger metadata file for the 
        given component filepath 

        Bagger metadata is a metadata that an SIPBagger may temporarily cache 
        into files within the bag while building it up.  It is expected that 
        the files will be removed during the finalization phase.
        """
        return os.path.join(self.bagdir,"metadata",destpath,self.BGRMD_FILENAME)

    def baggermd_for(self, destpath):
        """
        return the bagger-specific metadata associated with the particular 
        component.  Resource-level metadata can be updated by providing an empty
        string as the component filepath.  
        """
        mdfile = self.baggermd_file_for(destpath)
        if os.path.exists(mdfile):
            return read_json(mdfile)
        return OrderedDict()

    def update_bagger_metadata_for(self, destpath, mdata):
        """
        update the bagger-specific metadata.  

        (Note that this metadata is expected to be removed from the bag during 
        the finalization phase.)

        Resource-level metadata can be updated by providing an empty
        string as the component filepath.  The given metadata will be 
        merged with the currently saved metadata.  If there are no metadata
        yet saved for the filepath, the given metadata will be merged 
        with default metadata.

        When the metadata is merged, note that whole array values will be 
        replaced with corresponding arrays from the input metadata; the 
        arrays are not combined in any way.
        
        :param str filepath:   the filepath to the component to update.  An
                               empty string ("") updates the resource-level
                               metadata.  
        :param dict   mdata:   the new metadata to merge in
        """
        mdfile = self.baggermd_file_for(destpath)
        if os.path.exists(mdfile):
            out = read_json(mdfile)
        else:
            out = OrderedDict()

        out = self._update_md(out, mdata)
        write_json(out, mdfile)
        return out

    def _update_md(self, orig, updates):
        # update the values of orig with the values in updates
        # this uses the same algorithm as used to merge config data
        return merge_config(updates, orig)




class PreservationStateError(StateException):
    """
    an exception that indicates the assumed state of an SIPs ingest and 
    preservation does not match its actual state.

    A key place this is used is when a bagger's caller requests either 
    the creation of a new AIP or an update to an existing AIP when the 
    AIPS does or does not (respectively) already exist.  
    """
    def __init__(self, message, aipexists=None):
        """
        :param bool aipexists:  true if the AIP already exists, false if it 
                                doesn't.  If this is set, it should be assumed 
                                thrower was set to assume the opposite.  
                                Set to None (default) if this fact is not 
                                relevent.
        """
        super(message)
        self.aipsexists = aipexists




