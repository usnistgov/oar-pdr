"""
The primary interface for creating preservation bags.  (See the 
:mod:`parent package <nistoar.pdr.preserv>` for an overview of the preservation 
architecture.

The 
:class:`service.PreservationService <nistoar.pdr.preserv.service.PreservationService>`
provides the main API for creating preservation packages (AIPs).  It can be, 
in principle, be called from a command-line program, a web service, etc.  The 
preservation process can take a bit of time for large submissions; consequently,
the :class:`~nistoar.pdr.preserv.service.PreservationService` has built-in 
support for asynchronous processing.  

(Currently, the only working implementation of the 
:class:`~service.PreservationService` interface is the 
:class:`~service.ThreadedPreservationService`, which implements asynchronous 
execution via python threads.)

Asynchronous processing is by delegating the work to an 
:class:`~siphandler.SIPHandler`.  An implementation of this class understands
a particular SIP type; e.g. :class:`~siphandler.MIDASSIPHandler` understands 
SIPs created by the MIDAS application.  An SIP handler typically delegates 
the creation a preservation (AIP) bag to a "bagger" class (also customized 
for the SIP type; see :mod:`nistoar.preserv.bagger`).  Once the base bag (a 
single bag directory) is created, the SIP handler may serialize it, deliver 
it long term storage, and submit the metadata to the PDR metadata database.  

This package provides several modules:
* :mod:`service` -- provides implementations of the 
  :class:`~service.PreservationService` class.
* :mod:`siphandler` -- defines the :class:`~service.SIPHandler` class and 
  implementations appropriate for different SIP types.  
* :mod:`status` -- manages persistance state for asynchronous preservation tasks
* :mod:`wsgi` -- a REST web service front-end to the preservation service 
  implemented using the Web Service Gateway Interface (WSGI) framework.
"""
from service import (PreservationService, ThreadedPreservationService, 
                     RerequestException)
