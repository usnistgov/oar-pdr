"""
Provide functionality for the Public Data Repository
"""
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
    
