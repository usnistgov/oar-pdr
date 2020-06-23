"""
The package responsible for creating and managing data preservation packages.

In general, data to be ingested into the PDR is provided as a *submission
information package* (SIP).  The PDR design allows for different types SIPs; 
a primary example is a submission from the MIDAS application.  An SIP is 
ingested by submitting it the Preservation Service, which converts it to an
*archive information package* (AIP), stores it in long-term storage, and submits 
its metadata to the PDR's metadata database.  Currently, an OAR-PDR AIP takes 
the form of a BagIt data package--referred to as a *bag*--that complies with 
the NIST BagIt Profile.

The 
:class:`service.PreservationService <nistoar.pdr.preserv.service.PreservationService>`
provides the main API for creating preservation packages (AIPs).  It can be, 
in principle, be called from a command-line program, a web service, etc.  The 
preservation process can take a bit of time for large submissions; consequently,
the :class:`~nistoar.pdr.preserv.service.PreservationService` has built-in 
support for asynchronous processing.  

This package is organized into subpackages
* :mod:`service` -- the primary interface creating a 
  preseravation package (AIP).  It includes the 
  :class:`~service.PreservationService` and a web service front-end.
* :mod:`bagger` -- modules that understand how to turn SIPs of different types 
  into an AIP.
* :mod:`bagit` -- modules for creating and examining bags that conform to the 
  NIST BagIt Profile.  
* :mod:`validate` -- modules for validating that a bag is compliant with the 
  NIST BagIt Profile.  
"""
from ..exceptions import *
from ... import pdr as _pdr
from .. import PDRSystem
from ..utils import read_nerd, read_pod, write_json, read_json

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


class PreservationStateError(PreservationException):
    """
    An indication that the client's preservation request does not match the 
    state of the SIP/AIP.  In particular, the client either requested an initial
    preservation on an SIP that has already been preserved, or the client 
    requested an update on an SIP that has yet to be preserved initially.

    The aipexists property indicates the actual state of the AIP.  If it 
    is True, then the AIP already exists (i.e. SIP has already been preserved
    once already).  
    """
    def __init__(self, message, aipexists=None):
        """
        create the exception
        :param str message:     the message describing mismatched state
        :param bool aipexists:  the true current state of the AIP where True
                                indicates that the AIP already exists.
        """
        super(PreservationStateError, self).__init__(message)
        self.aipexists = aipexists

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

