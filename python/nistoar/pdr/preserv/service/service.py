"""
This module provides the business logic for the Preservation Service.
"""
from copy import deepcopy
from abc import ABCMeta, abstractmethod, abstractproperty
import os, logging, threading, time, errno

from detach import Detach

from ...exceptions import (PDRException, StateException,
                           ConfigurationException, SIPDirectoryNotFound)
from ....id import PDRMinter
from . import status
from . import siphandler as hndlr

from .. import PreservationException, sys as _sys
log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)



class PreservationService(object):
    """
    A class that asynchronously handles requests to ingest and preserve 
    Submission Information Packages (SIPs).  This single class can handle 
    multiple types of SIPs.  Because requests are handled asynchronously 
    (i.e. either via Python threads or subprocesses, depending on the 
    implementation), multiple requests can be managed simultaneously. 
    """
    __metaclass__ = ABCMeta

    def __init__(self, config):
        """
        initialize the service based on the given configuration.
        """
        self.cfg = deepcopy(config)

        workdir = self.cfg.get('working_dir')
        if not workdir:
            raise ConfigurationException("Missing required config parameter: "+
                                         "working_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir

        storedir = self.cfg.get('store_dir')
        if not storedir:
            raise ConfigurationException("Missing required config parameter: "+
                                         "store_dir", sys=self)
        if not os.path.isdir(storedir):
            raise StateException("Store directory does not exist as a " +
                                 "directory: " + storedir, sys=self)
        self.storedir = storedir

        if not self.cfg.get('sip_type'):
            raise ConfigurationException("Missing required config parameter: "+
                                         "sip_type", sys=self)
        try:
            self.siptypes = self.cfg.get('sip_type').keys()
        except AttributeError, e:
            raise ConfigurationException("Wrong type for config parameter, "+
                                         "'sip_type': need dict, got ",
                                         type(self.cfg.get('sip_type')))

        self.idregdir = self.cfg.get('id_registry_dir')
        if not self.idregdir:
            self.idregdir = os.path.join(self.workdir, 'idreg')
        if not os.path.exists(self.idregdir):
            os.mkdir(self.idregdir)

        self.minters = {}

        # ensure the environemnt is set up
        for tp in self.siptypes:
            self.status("_noid", tp)

    def preserve(self, sipid, siptype=None, timeout=None):
        """
        request that an SIP with a given ID is preserved into long-term 
        storage and ingested into the target repository.  The SIP-ID implies 
        a location to look for data associated with that ID.  Returned 
        is a dictionary containing information information about the status
        of the request, including, upon successful completion, a list of the 
        Bag files created and their checksums. 

        :param sipid   str:  the ID for the dataset to be preserved.  
        :param siptype str:  the name of the type of SIP the ID refers to.
                             If not provided, a default is assumed, based on 
                             the configuration.  
        :param timeout int:  The maximum number of seconds to wait for the 
                             preservation process to complete before returning
                             with an interim status dictionary.  (The
                             preservation process will continue in another 
                             thread.)
        :return dict:  a dictionary with metadata describing the status of 
                       preservation effort.
        """
        if siptype not in self.siptypes:
            raise ConfigurationException("No support configured for SIP type: "+
                                         siptype)
        
        hdlr = self._make_handler(sipid, siptype)
        if hdlr.state == status.FORGOTTEN:
            # lay claim to this SIP by updating the state
            hdlr._status.reset()

        elif hdlr.state == status.FAILED:
            # restarting a previously failed attempt
            log.warn("%s: Retrying previously failed preservation attempt",
                     sipid)
            # FIX: did it fail previously on an update?
            hdlr._status.reset()

        elif hdlr.state == status.SUCCESSFUL:
            log.warn("%s: Non-update request for previously preserved SIP",
                     sipid)
            raise RerequestException(hdlr.state,
                            "initial preservation already completed for "+sipid)

        elif hdlr.state == status.IN_PROGRESS:
            log.warn("%s: requested preservation is already in progress", sipid)
            raise RerequestException(hdlr.state,
                                     "preservation already underway for "+sipid)

        if not hdlr.isready():
            raise PreservationException("Requested SIP cannot be preserved: " +
                                        hdlr.status.message)
            
        return self._launch_handler(hdlr, timeout)[0]

    @abstractmethod
    def _launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        raise NotImplementedError()
        
    def status(self, sipid, siptype=None):
        """
        report on the current status of the preservation of a dataset with
        the given SIP identifier.  Returned is a dictionary containing
        information information about the status of the request,
        including, upon successful completion, a list of the Bag files
        created and their checksum (this is the same type of object as 
        returned by preserve()).

        :param sipid   str:  the ID for the dataset to be preserved.  
        :param siptype str:  the name of the type of SIP the ID refers to.
                             If not provided, a default is assumed.
        :return dict:  a dictionary wiht metadata describing the status of 
                       preservation effort.
        """
        try:
            hdlr = self._make_handler(sipid, siptype)
            if hdlr.state == status.FORGOTTEN or hdlr.state == status.NOT_READY:
                hdlr.isready()
            return hdlr.status
        except SIPDirectoryNotFound, ex:
            out = { "id": sipid,
                    "state": status.NOT_FOUND,
                    "message": status.user_message[status.NOT_FOUND],
                    "history": [] }
            return out
        except Exception, ex:
            log.exception("Failed to create a handler for siptype=%s, "+
                          "sipid=%s while checking status", sipid, siptype)
            out = { "id": sipid,
                    "state": status.NOT_READY,
                    "message":
                         "Internal Error: Unable to get status as siptype={0}".format(siptype),
                    "history": [] }
            return out

    def requests(self, siptype=None):
        """
        return the known SIP identifiers for which preservation requests 
        have been made.  These values can be used to return status information 
        via the status() method.  

        :param siptype str: return IDs only of the given type.  If None, all 
             types are returned.
        :return dict:  a dictionary where the keys are identifiers and the values
             are their corresponding SIP type names.  
        """
        out = {}
        stcfg = self.cfg.get('sip_type', {})
        for tp in stcfg.keys():
            if siptype and siptype != tp:
                continue
            hndlrcfg = self._get_handler_config(tp)
            ids = status.SIPStatus.requests(hndlrcfg.get('status_manager',{}))
            for id in ids:
                out[id] = tp

        return out

    @abstractmethod
    def update(self, sipid, siptype=None, timeout=None):
        """
        request that an updating SIP with a given ID is preserved into long-term 
        storage and ingested into the target repository.  The SIP-ID implies 
        a location to look for data associated with that ID.  Returned 
        is a dictionary containing information information about the status
        of the request, including, upon successful completion, a list of the 
        Bag files created and their checksums. 

        :param sipid   str:  the ID for the dataset to be preserved.  
        :param siptype str:  the name of the type of SIP the ID refers to.
                             If not provided, a default is assumed, based on 
                             the configuration.  
        :param timeout int:  The maximum number of seconds to wait for the 
                             preservation process to complete before returning
                             with an interim status dictionary.  (The
                             preservation process will continue in another 
                             thread.)
        :return dict:  a dictionary wiht metadata describing the status of 
                       preservation effort.
        """
        raise NotImplemented()
        

    def _make_handler(self, sipid, siptype=None):
        """
        create an SIPHandler of the given type for the given ID.
        """
        if not siptype:
            siptype = 'midas'

        pcfg = self._get_handler_config(siptype)
            
        # get an IDMinter we can use
        if siptype not in self.minters:
            mntrdir = pcfg.get('id_registry_dir',
                               self.cfg.get('id_registry_dir',
                                            os.path.join(self.workdir, 'idreg')))
            cfg = pcfg.get('id_minter', {})
            self.minters[siptype] = PDRMinter(mntrdir, cfg)

        if siptype == 'midas':
            return hndlr.MIDASSIPHandler(sipid, pcfg, self.minters[siptype])
        else:
            raise PDRException("SIP type not supported: "+siptype, sys=_sys)

    def _get_handler_config(self, siptype):
        # from our service configuration, build a configuration object that
        # can be used to preserve an SIP of a particular type
        
        cfg4type = self.cfg.get('sip_type', {}).get(siptype, {})

        # fold the common parameters into the preserv parameters
        pcfg = deepcopy(cfg4type.get('common', {}))
        pcfg.update(cfg4type.get('preserv', {}))
                    
        if 'working_dir' not in pcfg:
            pcfg['working_dir'] = os.path.join(self.workdir, 'preserv')
        if 'store_dir' not in pcfg:
            pcfg['store_dir'] = self.storedir
        if 'id_registry_dir' not in pcfg:
            pcfg['id_registry_dir'] = self.idregdir
        if 'mdbag_dir' not in pcfg:
            pcfg['mdbag_dir'] = cfg4type.get('mdserv',{}).get('working_dir',
                                        os.path.join(self.workdir, 'mdserv'))

        return pcfg

class ThreadedPreservationService(PreservationService):
    """
    A class that asynchronously handles requests to ingest and preserve 
    Submission Information Packages (SIPs).  This single class can handle 
    multiple types of SIPs.  Because requests are handled asynchronously 
    (i.e. in separate Python threads), multiple requests can be managed 
    simultaneously. 

    NOTE:  This implementation is currently not being used.  The production
    system uses MultiprocPreservationService.  
    """
    def __init__(self, config):
        """
        initialize the service based on the given configuration.
        """
        super(ThreadedPreservationService, self).__init__(config)

    class _HandlerThread(threading.Thread):
        def __init__(self, handler, serialtype, destdir, params=None):
            if params is None:
                params = {}
            tname = params.get('worker_name')
            threading.Thread.__init__(self, name=tname)
            self._hdlr = handler
            self._stype = serialtype
            self._dest = destdir
            self._params = params
        def run(self):
            time.sleep(0)
            self._hdlr.bagit(self._stype, self._dest, self._params)

    def _launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  If not provided, the configured value of 
        'sync_timeout' will be used.  

        :param handler SIPHandler:  the handler to launch
        :param timeout        int:  the time in seconds to wait for the 
                                      handler to finish before returning an 
                                      asynchronous response.
        """
        t = None
        try: 
            t = self._HandlerThread(handler, 'zip', self.storedir,
                                    {'worker-name': handler._sipid})
            t.start()

            if timeout is None:
                timeout = self.cfg.get('sync_timeout', 5)
            t.join(timeout)

            # the thread either finished or we timed-out waiting for it
            if not t.is_alive():
                log.info("%s: preservation completed synchronously",
                         handler._sipid)
                if handler.state == status.IN_PROGRESS:
                    handler.status.update(status.FAILED,
                                 "preservation thread died for unknown reasons")
                elif handler.state == status.READY:
                    handler.status.update(status.FAILED,
                             "preservation failed to start for unknown reasons")
            else:
                log.info("%s: preservation running asynchronously",
                         handler._sipid)

        except Exception, ex:
            log.exception("Failed to launch handler for sipid=%s",
                          handler._sipid)
            handler.set_state(status.FAILED,
                        "Failed to launch preservation due to internal error")

        return (handler.status, t)

    def update(self, sipid, siptype=None, timeout=None):
        # Unimplemented: simulating asynchronous response
        
        if siptype not in self.siptypes:
            raise ConfigurationException("No support configured for SIP type: "+
                                         siptype)
        
        hdlr = self._make_handler(sipid, siptype)
        if hdlr.state == status.FORGOTTEN or hdlr.state == status.READY:
            # lay claim to this SIP by updating the state
            hdlr._status.reset()

        elif hdlr.state == status.FAILED:
            # restarting a previously failed attempt
            log.warn("%s: Retrying previously failed preservation attempt",
                     sipid)
            # FIX: did it fail previously on an update?
            hdlr._status.reset()

        elif hdlr.state == status.SUCCESSFUL:
            log.info("%s: Update request for previously preserved SIP",
                     sipid)
            hdlr._status.reset()

        elif hdlr.state == status.IN_PROGRESS:
            log.warn("%s: preservation is already in progress", sipid)
            raise RerequestException(hdlr.state,
                                     "preservation already underway for "+sipid)

        if not hdlr.isready():
            raise PreservationException("Requested SIP cannot be preserved: " +
                                        hdlr.status.message)

        log.warn("Update is unimplemented! (Pretending to work asynchronously)")
        hdlr.set_state(status.IN_PROGRESS)
        return hdlr.status


# NOT WORKING (use ThreadedPreservationService)

class MultiprocPreservationService(PreservationService):
    """
    A class that asynchronously handles requests to ingest and preserve 
    Submission Information Packages (SIPs).  This single class can handle 
    multiple types of SIPs.  Because requests are handled asynchronously 
    (i.e. in separate standalone processes), multiple requests can be managed 
    simultaneously. 

    This implementation launches preservation requests via a child process
    (running a standalone bagging script).  
    """
    def __init__(self, config):
        """
        initialize the service based on the given configuration.
        """
        super(MultiprocPreservationService, self).__init__(config)

    def _pid_is_alive(self, pid):
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError, e:
            if e.errno == errno.ESRCH:
                return False
            elif e.errno == errno.EPERM:
                return True
            else:
                raise
        return True

    def _launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        cpid = None
        try:
          with Detach() as d:
            if d.pid:
                # parent process: wait a short bit to see if the child finishes
                # quickly
                cpid = d.pid

                if timeout is None:
                    timeout = self.cfg.get('sync_timeout', 5)
                starttime = time.time()
                since = time.time() - starttime
                while since < timeout:
                    if not self._pid_is_alive(d.pid):
                        break
                    time.sleep(1)
                    since = time.time() - starttime

                if not self._pid_is_alive(d.pid):
                    if handler.state == status.IN_PROGRESS:
                        handler.set_state(status.FAILED,
                                 "preservation thread died for unknown reasons")
                    elif handler.state == status.READY:
                        handler.set_state(status.FAILED,
                             "preservation failed to start for unknown reasons")

                return (handler.status, d.pid)
            else:
                # child
                try:
                    handler.bagit('zip', self.storedir)
                except Exception, e:
                    log.exception("Preservation handler failed: %s", str(e))
                finally:
                    ex = ((handler.state != status.SUCCESSFUL) and 1) or 0
                    sys.exit(ex)

        except Exception, e:
            if cpid is None:
                log.exception("Failed to launch preservation process: %s",str(e))
                handler.set_state(status.FAILED,
                                  "Failed to launch preservation process")
                return (handler.status, None)
            else:
                log.exception("Unexpected failure while monitoring "+
                              "preservation process: %s", str(e))
                return (handler.status, cpid)

    def update(self, sipid, siptype=None, timeout=None):
        raise NotImplemented()

class RerequestException(PreservationException):
    """
    User has requested to preserve an SIP that has already been requested.  
    Providing the status state will reflect whether the original request was 
    successful, in progress, or otherwise failed.  
    """
    def __init__(self, request_state, msg=None):
        if not msg:
            "SIP preservation has already been requested ({0})".\
                format(request_state)
        super(RerequestException, self).__init__(msg)
        self.state = request_state

