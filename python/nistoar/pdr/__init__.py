"""
Provide functionality for the Public Data Repository
"""
import os
from abc import ABCMeta, abstractmethod, abstractproperty

from .version import __version__

class SystemInfoMixin(object):
    """
    a mixin for getting information about the current system that a class is 
    a part of.  
    """
    __metaclass__ = ABCMeta

    @property
    def system_name(self):
        return ""

    @property
    def system_abbrev(self):
        return ""

    @property
    def subsystem_name(self):
        return ""

    @property
    def subsystem_abbrev(self):
        return ""

    @abstractproperty
    def system_version(self):
        return __version__

_PDRSYSNAME = "Public Data Repository"
_PDRSYSABBREV = "PDR"
_PDRSUBSYSNAME = _PDRSYSNAME
_PDRSUBSYSABBREV = _PDRSYSABBREV

class PDRSystem(SystemInfoMixin):
    """
    a mixin providing static information about the PDR system.  

    In addition to providing system information, one can determine if a class 
    instance--namely, an Exception--is part of a particular system by calling 
    `isinstance(inst, PDRSystem)`.
    """

    @property 
    def system_version(self):
        return __version__

    @property
    def system_name(self): return _PDRSYSNAME
    @property
    def system_abbrev(self): return _PDRSYSABBREV
    @property
    def subsystem_name(self): return _PDRSUBSYSNAME
    @property
    def subsystem_abbrev(self): return _PDRSUBSYSABBREV
    
def find_jq_lib(config=None):
    """
    return the directory containing the jq libraries
    """
    def assert_exists(dir, ctxt=""):
        if not os.path.exists(dir):
            "{0}directory does not exist: {1}".format(ctxt, dir)
            raise ConfigurationException(msg, sys=self)

    # check local configuration
    if config and 'jq_lib' in config:
        assert_exists(config['jq_lib'], "config param 'jq_lib' ")
        return config['jq_lib']
            
    # check environment variable
    if 'OAR_JQ_LIB' in os.environ:
        assert_exists(os.environ['OAR_JQ_LIB'], "env var OAR_JQ_LIB ")
        return os.environ['OAR_JQ_LIB']

    # look relative to a base directory
    if 'OAR_HOME' in os.environ:
        # this is normally an installation directory (where lib/jq is our
        # directory) but we also allow it to be the source directory
        assert_exists(os.environ['OAR_HOME'], "env var OAR_HOME ")
        basedir = os.environ['OAR_HOME']
        candidates = [os.path.join(basedir, 'lib', 'jq'),
                      os.path.join(basedir, 'jq')]
    else:
        # guess some locations based on the location of the executing code.
        # The code might be coming from an installation, build, or source
        # directory.
        import nistoar
        basedir = os.path.dirname(os.path.dirname(os.path.dirname(
                                            os.path.abspath(nistoar.__file__))))
        candidates = [os.path.join(basedir, 'jq')]
        basedir = os.path.dirname(os.path.dirname(basedir))
        candidates.append(os.path.join(basedir, 'jq'))
        candidates.append(os.path.join(basedir, 'oar-metadata', 'jq'))
        
    for dir in candidates:
        if os.path.exists(dir):
            return dir
        
    return None

def_jq_libdir = find_jq_lib()

def find_merge_etc(config=None):
    """
    return the directory containing the merge rules
    """
    def assert_exists(dir, ctxt=""):
        if not os.path.exists(dir):
            "{0}directory does not exist: {1}".format(ctxt, dir)
            raise ConfigurationException(msg, sys=self)

    # check local configuration
    if config and 'merge_rules_lib' in config:
        assert_exists(config['merge_rules_lib'],
                      "config param 'merge_rules_lib' ")
        return config['merge_rules_lib']
            
    # check environment variable
    if 'OAR_MERGE_ETC' in os.environ:
        assert_exists(os.environ['OAR_MERGE_ETC'], "env var OAR_MERGE_ETC ")
        return os.environ['OAR_MERGE_ETC']

    # look relative to a base directory
    if 'OAR_HOME' in os.environ:
        # this is normally an installation directory (where lib/jq is our
        # directory) but we also allow it to be the source directory
        assert_exists(os.environ['OAR_HOME'], "env var OAR_HOME ")
        basedir = os.environ['OAR_HOME']
        candidates = [os.path.join(basedir, 'etc', 'merge')]

    else:
        # guess some locations based on the location of the executing code.
        # The code might be coming from an installation, build, or source
        # directory.
        import nistoar
        basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                                            os.path.abspath(nistoar.__file__)))))
        candidates = [os.path.join(basedir, 'etc', 'merge')]
        candidates.append(os.path.join(basedir, 'oar-metadata', 'etc', 'merge'))
        basedir = os.path.dirname(basedir)
        candidates.append(os.path.join(basedir, 'oar-metadata', 'etc', 'merge'))
        candidates.append(os.path.join(basedir, 'etc', 'merge'))

    for dir in candidates:
        if os.path.exists(dir):
            return dir
        
    return None

def_merge_etcdir = find_merge_etc()

