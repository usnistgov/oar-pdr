"""
This module provides the business logic for the Preservation Service.

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
the creation a preservation (AIP) bag to a "bagger" class (see
:mod:`nistoar.preserv.bagger`).  Once the base bag (a single bag directory) is 
created, the SIP handler may serialize it, deliver it long term storage, and
submit the metadata to the PDR metadata database.  
"""
from __future__ import print_function
from copy import deepcopy
from abc import ABCMeta, abstractmethod, abstractproperty
import os, sys, logging, threading, multiprocessing, time, errno, re

from .. import (PDRException, StateException, IDNotFound, 
                ConfigurationException, SIPDirectoryNotFound, AIPValidationError,
                PreservationStateError)
from ....id import PDRMinter
from . import status
from . import siphandler as hndlr
from ...notify import NotificationService
from ..bagger.prepupd import UpdatePrepService
from ..bagger.midas3 import midasid_to_bagname
from ... import config as configmod
from ... import utils

from .. import PreservationException, sys as _sys
log = logging.getLogger(_sys.system_abbrev)   \
             .getChild(_sys.subsystem_abbrev) \
             .getChild('service')

# this is used during testing to run preservation processing syncronously within
# MultiprocPreservationService
mp_sync = False

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

        # setup the notification system, if requested
        self._notifier = None
        if self.cfg.get('notifier'):
            self._notifier = NotificationService(self.cfg['notifier'])

        # ensure the environemnt is set up
        for tp in self.siptypes:
            self.status("_noid", tp)

        # setup a service used to prepare for updates to existing AIPs
        # If the 'repo_access' config parameter, the service is not able to
        # check if the input SIP represents a dataset that has been published
        # before (and thus is an update) nor can submit an update as a
        # multibag addendum/errata.  
        self._prepsvc = None
        if 'repo_access' in self.cfg:
            self._prepsvc = UpdatePrepService(self.cfg['repo_access'])
        else:
            log.warning("repo_access not configured; can't support updates!")

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

        # create a Handler object that will be launched asynchronously
        try:
            hdlr = self._make_handler(sipid, siptype, asupdate=False)
            log.info("Initial preservation requested for SIP=%s", sipid)
        except (IDNotFound, SIPDirectoryNotFound) as ex:
            log.warn("SIP=%s not available for preservation: %s", sipid, str(ex))
            return self._not_found_state(sipid, siptype)
        except Exception as ex:
            log.error("Problem getting SIP status for preservation: %s", str(ex))
            return self._internal_error_state(sipid, siptype)

        # check for the existence of an AIP corresponding to the input SIP ID:
        # if one exists, fail because the user should have called update()
        if self._prepsvc:
            aipid = re.sub(r'^ark:/\d+/','', sipid)
            if self._prepsvc.prepper_for(aipid, log=log).aip_exists():
                hdlr.set_state(status.CONFLICT,
                               "requested initial preservation of existing AIP")
                msg = "AIP with ID already exists (need to request update?): "
                raise PreservationStateError(msg + sipid, True)

        # React to the current state. This state reflects the state prior to
        # the current request.  Make sure it is in a state that allows the
        # current request to proceed.
        if hdlr.state == status.FORGOTTEN:
            # lay claim to this SIP by updating the state (to PENDING)
            hdlr._status.reset()

        elif hdlr.state == status.FAILED or hdlr.state == status.CONFLICT:
            # restarting a previously failed attempt
            log.warn("%s: Retrying previously failed preservation attempt",
                     sipid)
            # FIX: did it fail previously on an update?
            hdlr._status.reset()

        elif hdlr.state == status.SUCCESSFUL:
            # shouldn't happen now that we are independently checking the
            # existence of the AIP above
            log.warn("%s: Non-update request for previously preserved SIP",
                     sipid)
            raise RerequestException(hdlr.state,
                            "initial preservation already completed for "+sipid)

        elif hdlr.state == status.IN_PROGRESS or hdlr.state == status.PENDING:
            log.warn("%s: requested preservation is already in progress", sipid)
            raise RerequestException(hdlr.state,
                                     "preservation already underway for "+sipid)

        # A final check for readiness:  this call allows the handler to carry
        # out additional SIP-type-specific checks of the SIP's state.
        if not hdlr.isready():
            raise PreservationException("Requested SIP cannot be preserved: " +
                                        hdlr.status.message)

        # we're good to go; launch the handler asynchronously
        return self._launch_handler(hdlr, timeout)[0]

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
        if siptype not in self.siptypes:
            raise ConfigurationException("No support configured for SIP type: "+
                                         siptype)

        # create a Handler object that will be launched asynchronously
        try:
            hdlr = self._make_handler(sipid, siptype, asupdate=True)
            log.info("Preservation update requested for SIP=%s", sipid)
        except (IDNotFound, SIPDirectoryNotFound) as ex:
            log.warn("SIP=%s not available for preservation: %s", sipid, str(ex))
            return self._not_found_state(sipid, siptype)
        except Exception as ex:
            log.error("Problem getting SIP status for preservation: %s", str(ex))
            return self._internal_error_state(sipid, siptype)

        # check for the existence of an AIP corresponding to the input SIP ID:
        # if one does not exists, fail because the user should have called
        # preserve()
        if self._prepsvc:
            aipid = re.sub(r'^ark:/\d+/','', sipid)
            if not self._prepsvc.prepper_for(aipid, log=log).aip_exists():
                hdlr.set_state(status.CONFLICT,
                               "requested update to non-existing AIP")
                msg = "AIP with ID does not exist (unable to update): "
                raise PreservationStateError(msg + sipid, False)
        
        # React to the current state. This state reflects the state prior to
        # the current request.  Make sure it is in a state that allows the
        # current request to proceed.
        if hdlr.state == status.FORGOTTEN or hdlr.state == status.READY:
            # lay claim to this SIP by updating the state (to PENDING)
            hdlr._status.reset()

        elif hdlr.state == status.FAILED or hdlr.state == status.CONFLICT:
            # restarting a previously failed attempt
            log.warn("%s: Retrying previously failed preservation attempt",
                     sipid)
            # FIX: did it fail previously on an update?
            hdlr._status.reset()

        elif hdlr.state == status.SUCCESSFUL:
            log.info("%s: Update request for previously preserved SIP",
                     sipid)
            hdlr._status.reset()

        elif hdlr.state == status.IN_PROGRESS or hdlr.state == status.PENDING:
            log.warn("%s: preservation is already in progress", sipid)
            raise RerequestException(hdlr.state,
                                     "preservation already underway for "+sipid)

        # A final check for readiness:  this call allows the handler to carry
        # out additional SIP-type-specific checks of the SIP's state.
        if not hdlr.isready():
            raise PreservationException("Requested SIP cannot be preserved: " +
                                        hdlr.status.message)

        # we're good to go; launch the handler asynchronously
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
        log.debug("Checking status of SIP=%s by request", sipid)
        try:
            hdlr = self._make_handler(sipid, siptype)
            if hdlr.state == status.FORGOTTEN or hdlr.state == status.NOT_READY:
                hdlr.isready()

            return hdlr.status

        except (IDNotFound, SIPDirectoryNotFound) as ex:
            log.debug("Requested status on SIP=%s that is complete: %s", sipid, str(ex))
            return self._not_found_state(sipid, siptype)
        except Exception as ex:
            log.error("Problem getting SIP status: %s", str(ex))
            return self._internal_error_state(sipid, siptype)

    def _not_found_state(self, sipid, siptype, message=None):
        if not message:
            message = status.user_message[status.NOT_FOUND]
        return {
            "id": sipid,
            "state": status.NOT_FOUND,
            "message": message,
            "history": []
        }

    def _internal_error_state(self, sipid, siptype):
        log.exception("Failed to create a handler for siptype=%s, "+
                      "sipid=%s while checking status", sipid, siptype)
        return {
            "id": sipid,
            "state": status.NOT_READY,
            "message": "Internal Error: Unable to get status as siptype={0}" \
                       .format(siptype),
            "history": []
        }

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
            cfg = hndlrcfg.get('status_manager',{})
            if 'cachedir' not in cfg:
                cfg['cachedir'] = os.path.join(self.workdir, 'preserv_status')
            ids = status.SIPStatus.requests(cfg)
            for id in ids:
                out[id] = tp

        return out


    def _make_handler(self, sipid, siptype=None, asupdate=False):
        """
        create an SIPHandler of the given type for the given ID.
        """
        if not siptype:
            siptype = 'midas3'
        cls = None
        if siptype == hndlr.MIDASSIPHandler.key or siptype == hndlr.MIDASSIPHandler.name:
            # key = "midas"
            cls = hndlr.MIDASSIPHandler
        elif siptype == hndlr.MIDAS3SIPHandler.key or siptype == hndlr.MIDAS3SIPHandler.name:
            # key = "midas3"
            cls = hndlr.MIDAS3SIPHandler
        else:
            raise PDRException("SIP type not supported: "+siptype, sys=_sys)

        pcfg = self._get_handler_config(cls.key)
            
        # get an IDMinter we can use
        if siptype not in self.minters:
            mntrdir = pcfg.get('id_registry_dir',
                               self.cfg.get('id_registry_dir',
                                            os.path.join(self.workdir, 'idreg')))
            cfg = pcfg.get('id_minter', {})
            self.minters[siptype] = PDRMinter(mntrdir, cfg)

        return cls(sipid, pcfg, self.minters[siptype], notifier=self._notifier)

    def _get_handler_config(self, siptype):
        # from our service configuration, build a configuration object that
        # can be used to preserve an SIP of a particular type
        
        cfg4type = self.cfg.get('sip_type', {}).get(siptype, {})

        # fold the common parameters into the preserv parameters
        pcfg = deepcopy(cfg4type.get('common', {}))
        pcfg.update(cfg4type.get('preserv', {}))
                    
        if 'working_dir' not in pcfg:
            pcfg['working_dir'] = self.workdir
        if 'store_dir' not in pcfg:
            pcfg['store_dir'] = self.storedir
        if 'id_registry_dir' not in pcfg:
            pcfg['id_registry_dir'] = self.idregdir
        if 'mdbag_dir' not in pcfg:
            if siptype == 'midas3':
                pcfg['mdbag_dir'] = cfg4type.get('pubserv',{}).get('working_dir',
                                        os.path.join(self.workdir, 'mdbags'))
            else:
                pcfg['mdbag_dir'] = cfg4type.get('mdserv',{}).get('working_dir',
                                        os.path.join(self.workdir, 'mdserv'))
        if 'repo_access' not in pcfg and 'repo_access' in self.cfg:
            pcfg['repo_access'] = deepcopy(self.cfg['repo_access'])

        return pcfg

class ThreadedPreservationService(PreservationService):
    """
    A class that asynchronously handles requests to ingest and preserve 
    Submission Information Packages (SIPs).  This single class can handle 
    multiple types of SIPs.  Because requests are handled asynchronously 
    (i.e. in separate Python threads), multiple requests can be managed 
    simultaneously. 
    """
    def __init__(self, config):
        """
        initialize the service based on the given configuration.
        """
        super(ThreadedPreservationService, self).__init__(config)

    class _HandlerThread(threading.Thread):
        def __init__(self, handler, serialtype, params=None, destdir=None):
            if params is None:
                params = {}
            tname = params.get('worker_name')
            threading.Thread.__init__(self, name=tname)
            self._hdlr = handler
            self._stype = serialtype
            self._dest = destdir
            self._params = params
        def run(self):
            try:
                time.sleep(0)
                self._hdlr.bagit(self._stype, self._dest, self._params)
            except Exception, ex:
                if isinstance(ex, PreservationStateError):
                    log.exception("Incorrect state for client's request: "+
                                  str(ex))
                    if ex.aipexists:
                        reason = "requested initial preservation of existing AIP"
                    else:
                        reason = "requested update to non-existing AIP"
                    self._hdlr.set_state(status.CONFLICT, reason)
                else:
                    self._hdlr.set_state(status.FAILED, "Unexpected failure")
                log.exception("Bagging failure: %s", str(ex))

                # alert a human!
                if self._hdlr.notifier:
                    fmtd = False
                    if isinstance(ex, PreservationException):
                        msg = [str(ex)] + ex.errors
                        fmtd = True
                    else:
                        msg = str(ex)
                    self._hdlr.notifier.alert("preserve.failure",
                                              origin=self._hdlr.name,
                      summary="Preservation failed for SIP="+self._hdlr._sipid,
                                              desc=msg, formatted=fmtd,
                                              id=self._hdlr._sipid)

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
            t = self._HandlerThread(handler, 'zip', {'worker-name': handler._sipid})
            t.start()

            if timeout is None:
                timeout = float(self.cfg.get('sync_timeout', 5))
            t.join(timeout)

            # the thread either finished or we timed-out waiting for it
            if not t.is_alive():
                log.info("%s: preservation completed synchronously",
                         handler._sipid)
                if handler.state == status.IN_PROGRESS:
                    handler.set_state(status.FAILED,
                                 "preservation thread died for unknown reasons")
                elif handler.state == status.READY:
                    handler.set_state(status.FAILED,
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
        self._oldlogfile = None
        self.combinedlog = os.path.join(self.cfg.get('logdir', configmod.global_logdir),
                                        self.cfg.get('logfile', 'preservation.log'))

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

    def _fork(self, sync=False):
        # fork this process so that work can be done in the child.
        if sync:
            # synchronous execution requested; don't really fork
            log.info("Launching preservation synchronously")
            return 0
        log.info("Launching preservation in subprocess")
        return os.fork()

    def _in_child_handle(self, handler, sync=False):
        # for child process:
        try:
            log.info("Preserving %s SIP id=%s", handler.name, handler._sipid)
            handler.bagit('zip', self.storedir)
        except Exception, e:
            if isinstance(e, PreservationStateError):
                log.exception("Incorrect state for client's request: "+str(e))
                if e.aipexists:
                    reason = "requested initial preservation of existing AIP"
                else:
                    reason = "requested update to non-existing AIP"
                handler.set_state(status.CONFLICT, reason)
            elif isinstance(e, AIPValidationError):
                log.exception("Preservation validation failure: %s", str(e))
                handler.set_state(status.FAILED, "Preservation validation failure")
            else:
                log.exception("Preservation handler failed: %s", str(e))
                handler.set_state(status.FAILED, "Unexpected failure")

            # alert a human!
            if handler.notifier:
                handler.notifier.alert("preserve.failure",
                                       origin=handler.name,
                                       summary="Preservation failed for SIP="+handler.sipid,
                                       desc=str(e), id=handler.sipid)


    def _launch_handler(self, handler, timeout=None, sync=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        if sync is None:
            sync = mp_sync

        if timeout is None:
            timeout = self.cfg.get('sync_timeout', 5)

        proc = None
        if not sync:
            try:
                # work out where the log in the subprocess will go
                hlog = os.path.join(handler.name, midasid_to_bagname(handler.sipid) + ".log")
                hlogd = handler.cfg.get('logdir')
                if hlogd:
                    if not os.path.exists(os.path.join(hlogd, handler.name)):
                        os.makedirs(os.path.join(hlogd, handler.name))
                    hlog = os.path.join(hlogd, hlog)
            
                # launch a subprocess
                proc = multiprocessing.Process(target=_subprocess_handle,
                                               args=(self.cfg, hlog, handler.sipid, handler.name,
                                                     handler._asupdate, timeout))
                proc.start()
                proc.join(timeout)
                    
                if not proc.is_alive():
                    handler.refresh_state()
                    origstate = handler.state
                    if handler.state == status.IN_PROGRESS:
                        handler.set_state(status.FAILED,
                                     "preservation thread died for unknown reasons")
                    elif handler.state == status.READY:
                        handler.set_state(status.FAILED,
                                 "preservation failed to start for unknown reasons")
                    if handler.state == FAILED:
                        log.error("%s: preservation process completed synchronously (%s)",
                                  handler._sipid, origstate)
                    else:
                        log.info("%s: preservation completed synchronously (%s)",
                                 handler._sipid, origstate)
                else:
                    log.info("%s: preservation running asynchronously",
                             handler._sipid)
                return (handler.status, proc)

            except Exception, e:
                if proc is None:
                    log.exception("Failed to launch preservation process: %s",str(e))
                    handler.set_state(status.FAILED, "Failed to launch preservation process")
                    return (handler.status, None)
                else:
                    log.exception("Unexpected failure while monitoring "+
                                  "preservation process: %s", str(e))
                    return (handler.status, proc)
        else:
            # this is the child
            self._in_child_handle(handler, sync=True)  # (handles exceptions)
            return (handler.status, None)
                

    def _save_preserv_log(self, sipid, forlog=None):
        mylog = forlog
        if not mylog:
            mylog = configmod.global_logfile
        emsg = None
        try:
            with utils.LockedFile(self.combinedlog, 'a') as dfd:
                with open(mylog) as sfd:
                    dfd.write("----------- Preserving %s --------------\n" % sipid)
                    txt = sfd.read(10240)
                    while txt:
                        dfd.write(txt)
                        txt = sfd.read(10240)
        except Exception as ex:
            emsg = "Trouble saving sublog, %s, to combined log, %s: %s" % \
                   (mylog, self.combinedlog, str(ex))
            if not forlog:
                log.error(emsg)
                print("Warning: "+emsg)

        if not forlog:
            try:
                os.remove(mylog)
            except Exception as ex:
                log.exception("Trouble removing sublog, %s: %s", mylog, str(ex))

        return emsg

    def _teardown_child(self, handler, sync=False):
        mylog = configmod.global_logfile
        emsg = self._save_preserv_log(handler.sipid, mylog)

        if sync and self._oldlogfile:
            try:
                configmod.configure_log(self._oldlogfile, config=handler.cfg)
            except Exception as ex:
                lmsg = "Problem switching back logging: " + str(ex)
                log.error(lmsg)
                print("Warning: "+lmsg)

        if emsg:
            log.error(emsg)
            print("Warning: "+emsg)
        else:
            try:
                os.remove(mylog)
            except Exception as ex:
                log.exception("Trouble removing sublog, %s: %s", mylog, str(ex))
                

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

def _subprocess_handle(config, logfile, sipid, siptype, asupdate, timeout):
    svc = None
    shout = config.get('announce_subproc', True)
    try:
        if shout:
            print("{0} preservation process for {1} started".format(siptype, sipid))
        configmod.configure_log(logfile, config=config)
        svc = MultiprocPreservationService(config)
        handler = svc._make_handler(sipid, siptype, asupdate)
        svc._launch_handler(handler, timeout, sync=True)
    except Exception as ex:
        if svc:
            log.exception("{0} Failure while handling preservation: {1}".format(siptype, str(ex)))
        if shout:
            print("{0} Preservation process failed with error: {1}".format(siptype, str(ex)))
    else:
        if shout:
            print("{0} Preservation process completed successfully".format(siptype))
    finally:
        if svc:
            svc._save_preserv_log(sipid)


