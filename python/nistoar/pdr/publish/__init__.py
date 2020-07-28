"""
Provide tools creating and updating PDR data publications
"""
from ..exceptions import *
from ... import pdr as _pdr
from .. import PDRSystem

_PRESSYSNAME = _pdr._PDRSYSNAME
_PRESSYSABBREV = _pdr._PDRSYSABBREV
_PRESSUBSYSNAME = "Publishing"
_PRESSUBSYSABBREV = "Pub"

class PublishSystem(PDRSystem):
    """
    a mixin providing static information about the publishing system
    """
    @property
    def system_name(self): return _PRESSYSNAME
    @property
    def system_abbrev(self): return _PRESSYSABBREV
    @property
    def subsystem_name(self): return _PRESSUBSYSNAME
    @property
    def subsystem_abbrev(self): return _PRESSUBSYSABBREV

sys = PublishSystem()

