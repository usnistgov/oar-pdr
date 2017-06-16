"""
The implementation for creating and managing data preservation packages
"""
from collections import OrderedDict
import json

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

sys = PreservationSystem()

def read_nerd(nerdfile):
    """
    read the JSON-formatted NERDm metadata in the given file

    :return OrderedDict:  the dictionary containing the data
    """
    try:
        with open(nerdfile) as fd:
            return json.load(fd, object_pairs_hook=OrderedDict)
    except IOError, ex:
        raise NERDError("Unable to read NERD file: "+str(ex),
                        cause=ex, src=nerdfile, sys=self)

def read_pod(podfile):
    """
    read the JSON-formatted POD metadata in the given file

    :return OrderedDict:  the dictionary containing the data
    """
    try:
        with open(podfile) as fd:
            return json.load(fd, object_pairs_hook=OrderedDict)
    except IOError, ex:
        raise PODError("Unable to read POD file: "+str(ex),
                       cause=ex, src=podfile, sys=self)

def write_json(jsdata, destfile, indent=4):
    """
    write out the given JSON data into a file with pretty print formatting
    """
    try:
        with open(destfile, 'w') as fd:
            json.dump(jsdata, fd, indent=indent, separators=(',', ': '))
    except Exception, ex:
        raise StateException("{0}: Failed to write JSON data to file: {1}"
                             .format(destfile, str(ex)), cause=ex)

