"""
This module provides the base interface and implementation for the SIPBagger
infrastructure.  At the center is the SIPBagger class that serves as an 
abstract base for subclasses that understand different input sources.
"""
import os, json, filelock
from collections import OrderedDict
from abc import ABCMeta, abstractmethod, abstractproperty

from .. import PreservationSystem, read_nerd, read_pod
from .. import SIPDirectoryError, NERDError, PODError, StateException
from ..bagit.builder import checksum_of

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

    SIPPrepper implementations should be written to be indepodent: running 
    it mutliple times on the same input and output directories should result
    in the same end state.  That is, if run a second time and nothing is 
    different in the input directory, nothing changes in the output directory.
    If a file is added in the input directory and the prepper is rerun, that
    new file will get added to the output directory.  
    """
    __metaclass__ = ABCMeta

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

    def prepare(self, nodata=False, lock=True):
        """
        initialize the output working bag directory by calling 
        ensure_preparation().  This operation is wrapped in the acquisition
        of a file lock.
        """
        if lock:
            if not self.lock:
                self.ensure_bag_parent_dir()
                lockfile = self.bagdir + ".lock"
                self.lock = filelock.FileLock(lockfile)
            
            with self.lock:
                self.ensure_preparation(nodata)
        else:
            self.ensure_preparation(nodata)





