"""
The implementation for creating and managing data preservation packages
"""
from ..exceptions import *
from ... import pdr as _pdr
from .. import PDRSystem
from ..utils import read_nerd, read_pod, write_json 

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

class PreservationException(PDRException):
    """
    An exception indicating that an attempt to create and save a preservation 
    bundle failed.
    """
    def __init__(self, msg=None, errors=None, cause=None):
        """
        create an exception, optionally listing things that went wrong

        :param msg     str:  a general message describing the failure
        :param errors list:  a list of specific error messages indicating 
                               multiple errors that occurred.
        :param cause Exception:  an underlying cause in the form of an 
                             Exception instance.
        """
        super(PreservationException, self).__init__(msg, cause, sys=sys)
        self.errors = []
        if errors:
            self.errors.extend(errors)

    @property
    def description(self):
        """
        a longer explanation of the error or errors that occurred.  This is
        potentially multi-line (i.e. has embedded newlines) text constructed 
        from the list of errors attached to this exception.  If there are no
        errors, this is equivalent to str(self).  The last line will not 
        end in a newline character.
        """
        out = str(self)
        if len(self.errors) > 0:
            out += ":\n  * "
            out += "\n  * ".join(self.errors)
        return out
        

class AIPValidationError(PreservationException):
    """
    An indication that the an Archive Information Package (AIP) (usually,
    the preservation bag) is not valid.
    """
    pass

class CorruptedBagError(PDRException):
    """
    an exception indicating that a preservation bag appears to be corrupted
    or otherwise does not contain expected content.  This can include problems
    transfering the bag via a service.
    """
    def __init__(self, bagname=None, message=None, cause=None):
        if not message:
            message = "Unexpected content detected in bag"
            if bagname:
                message += ", " + bagname
        super(PDRException, self).__init__(message, cause)
        self.resource = bagname

