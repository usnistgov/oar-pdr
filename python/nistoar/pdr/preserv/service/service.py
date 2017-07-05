"""
This module provides the business logic for the Preservation Service.
"""
from copy import deepcopy
from abc import ABCMeta, abstractmethod, abstractproperty
import threading

from ...exceptions import PDRException, StateException, ConfigurationException
from . import status

_sys = PreservationSystem()
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
            raise ConfigurationException("Missing required config parameters: "+
                                         "working_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir

        storedir = self.cfg.get('store_dir')
        if not workdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "store_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Store directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir


    @abstractmethod
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
        :return dict:  a dictionary wiht metadata describing the status of 
                       preservation effort.
        """
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()

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

        if not idregdir:
            idregdir = self.cfg.get('id_registry_dir', self.workdir)
        if not os.path.isdir(idregdir):
            raise StateException("ID Registry directory does not exist as a " +
                                 "directory: " + idregdir, sys=self)

        self._minter = self._create_minter(idregdir)

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
        :return dict:  a dictionary wiht metadata describing the status of 
                       preservation effort.
        """
        hdlr = self._make_handler(sipid, siptype)
        if hdlr.status.state != status.PENDING:
            if hdlr.status.state == status.IN_PROGRESS:
                raise StateException("preservation already underway for "+sipid)
            else:
                # need to handle FAILED attempts
                raise StateException("initial preservation already completed " +
                                     "for "+sipid)
                                     
        self._launch_handler(hdlr)
        return hdlr.status

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

    def _create_minter(self, parentdir):
        cfg = self.cfg.get('id_minter', {})
        out = PDRMinter(parentdir, cfg)
        if not os.path.exists(out.registry.store):
            self.log.warn("Creating new ID minter")
        return out

    class _HandlerThread(threading.Thread):
        def __init__(self, handler, serialtype, destdir, params):
            self._hdlr = handler
            self._stype = serialtype
            self._dest = destdir
            self._params = parems
        def run(self):
            self._hdlr.bagit(self._stype, self._dest, self._params)

    def _launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        t = _HandlerThread('zip', self.store_dir, None)
        t.start()
        handler.bagit('zip', self.store_dir)

    def _make_handler(self, sipid, siptype=None):
        """
        create an SIPHandler of the given type for the given ID.
        """
        cfg4type = self.cfg.get('siptypes', {}).get(siptype, {})
        if 'working_dir' not in cfg4type:
            cfg4type['working_dir'] = self.workdir
        if 'working_dir' not in cfg4type:
            cfg4type['working_dir'] = self.workdir
        if 'status_manager' not in cfg4type:
            cfg4type['status_manager'] = self.cfg.get('status_manager', {})

        if not siptype:
            siptype = 'midas'    
        if siptype == 'midas':
            return MIDASSIPHandler(sipid, cfg4type, self.minter)
        else:
            raise PDRException("SIP type not supported: "+siptype, sys=_sys)


class MultiprocPreservationService(PreservationService):
    """
    A class that asynchronously handles requests to ingest and preserve 
    Submission Information Packages (SIPs).  This single class can handle 
    multiple types of SIPs.  Because requests are handled asynchronously 
    (i.e. in separate standalone processes), multiple requests can be managed 
    simultaneously. 
    """
    def __init__(self, config):
        """
        initialize the service based on the given configuration.
        """
        super(MultiprocPreservationService, self).__init__(config)

