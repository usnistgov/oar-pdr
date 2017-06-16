"""
This module provides the business logic for the Preservation Service.
"""
from copy import deepcopy
import threading

_sys = PreservationSystem()
log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)

class PreservationService(object):
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
        self.cfg = deepcopy(config)

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
        pass

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
        pass

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
        pass

    def _launch_handler(self, handler, timeout=None):
        """
        launch the given handler in a separate thread.  After launching, 
        this function will join with the thread for a maximum time given by 
        the timeout value.  
        """
        pass
    
    
