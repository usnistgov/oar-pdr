"""
The implementation for creating and managing data preservation packages
"""
from ..exceptions import *
from ... import pdr as _pdr
from .. import PDRSystem

_PRESSYSNAME = _pdr._PDRSYSNAME
_PRESSYSABBREV = _pdr._PDRSYSABBREV
_PRESSUBSYSNAME = "Preservation"
_PRESSUBSYSABBREV = _PRESSUBSYSNAME

class PreservationSystem(PDRSystem):
    """
    a mixin providing static information about the Preservation system
    """
    @property
    def system_name(self): return _PRESSYSNAME
    @property
    def system_abbrev(self): return _PRESSYSABBREV
    @property
    def subsystem_name(self): return _PRESSUBSYSNAME
    @property
    def subsystem_abbrev(self): return _PRESSUBSYSABBREV
