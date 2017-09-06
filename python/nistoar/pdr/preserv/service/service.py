"""
This module provides the business logic for the Preservation Service.
"""
from copy import deepcopy
from abc import ABCMeta, abstractmethod, abstractproperty
import threading, time, errno

from detach import Detach

from ...exceptions import PDRException, StateException, ConfigurationException
from . import status

from .. import sys as _sys
log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)



class PreservationService(object):
    """
    A class that asynchronously handles requests to ingest and preserve 
    Submission Information Packages (SIPs).  This single class can handle 
    multiple types of SIPs.  Because requests are handled asynchronously 
    (i.e. either via Python threads or subprocesses, depending on the 
    implementation), multiple requests can be managed simultaneously. 
    """

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
        self.minters = {}

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
        if hdlr.status.state == status.FORGOTTEN:
            # lay claim to this SIP by updating the state
            hdlr.reset()

        elif hdlr.status.state == status.FAILED:
            # restarting a previously failed attempt
            log.warn("%s: Retrying previously failed preservation attempt",
                     sipid)
            hdlr.reset()

        elif hdlr.status.state == status.SUCCESSFUL:
            log.warn("%s: Non-update request for previously preserved SIP",
                     sipid)
            raise StateException("initial preservation already completed " +
                                 "for "+sipid)
        else:
            log.warn("%s: requested preservation is already in progress", sipid)
            raise StateException("preservation already underway for "+sipid)

        if not hdlr.confirm_ready():
            raise StateException("Requested SIP cannot be preserved: " +
                                 hdlr.status.message)
            
        self.launch_handler(hdlr)
        return hdlr.status

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
        hdlr = self._make_handler(sipid, siptype)
        return hdlr.status


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
        raise NotImplementedError()

    def _make_handler(self, sipid, siptype=None):
        """
        create an SIPHandler of the given type for the given ID.
        """
        if not siptype:
            siptype = 'midas'
            
        cfg4type = self.cfg.get('sip_type', {}).get(siptype, {})

        # fold the common parameters into the preserv parameters
        pcfg = deepcopy(cfg4type.get('common', {}))
        pcfg.update(cfg4type.get('preserv', {}))
                    
        if 'working_dir' not in pcfg:
            pcfg['working_dir'] = os.path.join(self.workdir, 'preserv')
        if 'store_dir' not in pcfg:
            pcfg['store_dir'] = self.storedir
        if 'mdbag_dir' not in pcfg:
            pcfg['mdbag_dir'] = cfg4type.get('mdserv',{}).get('working_dir',
                                        os.path.join(self.workdir, 'mdserv'))
        if 'status_manager' not in pcfg:
            pcfg['status_manager'] = self.cfg.get('status_manager', {})

        # get an IDMinter we can use
        if siptype not in self.minters:
            mntrdir = pcfg.get('id_registry_dir',
                               self.cfg.get('id_registry_dir',
                                            os.path.join(self.workdir, 'idreg')))
            cfg = pcfg.get('id_minter', {})
            self.minters[siptype] = PDRMinter(mntrdir, cfg)

        if siptype == 'midas':
            return MIDASSIPHandler(sipid, pcfg, self.minters[siptype])
        else:
            raise PDRException("SIP type not supported: "+siptype, sys=_sys)

    
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
        def __init__(self, handler, serialtype, destdir, params):
            self._hdlr = handler
            self._stype = serialtype
            self._dest = destdir
            self._params = parems
        def run(self):
            time.sleep(0)
            self._hdlr.bagit(self._stype, self._dest, self._params)

    def launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        t = _HandlerThread('zip', self.store_dir, None)
        t.start()

        syncto = self.cfg.get('sync_timeout', 5)
        t.join(syncto)

        # the thread either finished or we timed-out waiting for it
        if not t.is_alive():
            if handler.state == status.IN_PROGRESS:
                handler.status.update(status.FAILED,
                                 "preservation thread died for unknown reasons")
            elif handler.state == status.READY:
                handler.status.update(status.FAILED,
                             "preservation failed to start for unknown reasons")

        return handler.status.user_export()


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

    def launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        with Detach() as d:
            if d.pid:
                # parent process: wait a short bit to see if the child finishes
                # quickly
                syncto = self.cfg.get('sync_timeout', 5)
                starttime = time.time()
                since = time.time() - starttime
                while since < syncto:
                    if not self._pid_is_alive(d.pid):
                        break
                    time.sleep(1)
                    since = time.time() - starttime

                if not self._pid_is_alive(d.pid):
                    if handler.state == status.IN_PROGRESS:
                        handler.status.update(status.FAILED,
                                 "preservation thread died for unknown reasons")
                    elif handler.state == status.READY:
                        handler.status.update(status.FAILED,
                             "preservation failed to start for unknown reasons")

                return handler.status.user_export()
            else:
                # child
                handler.bagit('zip', self.store_dir)

