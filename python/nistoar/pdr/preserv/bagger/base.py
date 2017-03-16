"""
This module provides the base interface and implementation for the SIPBagger
infrastructure.  At the center is the SIPBagger class that serves as an 
abstract base for subclasses that understand different input sources.
"""
import os, json
from collections import OrderedDict
from abc import ABCMeta, abstractmethod, abstractproperty

from ..exceptions import (SIPDirectoryError, SIPDirectoryNotFound, 
                          ConfigurationException, StateException, PODError)
from ..bagit.builder import checksum_of

def moddate_of(filepath):
    """
    return a file's modification time (as a float)
    """
    return os.stat(filepath).st_mtime

class SIPBagger(object):
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

    def read_pod(self, podfile):
        try:
            with open(podfile) as fd:
                return json.load(fd, object_pairs_hook=OrderedDict)
        except IOError, ex:
            raise PODError("Unable to read POD file: "+str(ex), src=podfile)

    def read_nerd(self, nerdfile):
        try:
            with open(nerdfile) as fd:
                return json.load(fd, object_pairs_hook=OrderedDict)
        except IOError, ex:
            raise NERDError("Unable to read NERD file: "+str(ex), src=nerdfile)




