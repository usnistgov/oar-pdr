"""
A client interface to the distributions service's cache manager.  
"""
from .client import (RESTServiceClient, DistribResourceNotFound, DistribServiceException,
                     DistribClientError, DistribServiceException)

class CacheManagerClient(object):
    """
    a client for managing the data cache used to hold files availabel for download.  It return 
    metadata about cache volumes as well as files in those volumes.  The client can also be used 
    to queue request to add files to hte cached as well as remove files from the cache.  
    """

    VOLS_EP = "volumes/"
    OBJS_EP = "objects/"
    QUEU_EP = "queue/"

    def __init__(self, baseurl):
        """
        initialize the client
        """
        self.svccli = RESTServiceClient(baseurl)

    def volumes(self):
        """
        return a list of summaries of the volumes that currently make up the cache.  Each summary is 
        a dictionary as returned by :py:meth:`summarize_volume`.
        :returns: a list of metadata dictionaries.
        """
        return self.svccli.get_json(self.VOLS_EP)

    def volume_names(self):
        """
        return a list of volume names that can be used as input to :py:method:`summarize_volume`.
        """
        return [v['name'] for v in self.volumes()]

    def summarize_volume(self, name):
        """
        return a summary of the state of a partiuclar volume in the form of a metadata dictionary
        with the at least following properties:

        name
           the name assigned to the volume
        capacity
           the maximum number of bytes this volume is allowed to hold
        status
           a flag indicating allowed operations on the volume
        filecount
           the number of files currently stored in the volume
        totalsize
           the total number of bytes currently in the folume
        since, sinceDate
           the date-time (in epoch seconds and as an ISO string, respectively) of the last time a file
           was accessed or added to the volume
        checked, checkedDate
           the oldest date-time (in epoch seconds and as an ISO string, respectively) that a file in 
           the volume was checked for integrity.
        """
        return self.svccli.get_json(self.VOLS_EP+name)

    def summarize_contents(self):
        """
        return a list of summaries of datasets being managed in the cache.  Each element represents
        a PDR dataset whose files are at least partially cached.
        """
        return self.svccli.get_json(self.OBJS_EP)

    def dataset_ids(self):
        """
        return the list of (AIP) identifiers for the datasets being managed in the cacche.
        These can be used to list file statuses via :py:meth:`summary_dataset`
        """
        return [d['aipid'] for d in self.summarize_contents() if 'aipid' in d]

    def summarize_dataset(self, aipid):
        """
        return a summary of the status of a dataset in the cache.  The summary is in the form of 
        a metadata dictionary that inludes at least the following properties:

        aipid
           the AIP ID for the dataset
        ediid
           the EDI ID for the dataset
        pdrid
           the PDR ID for the dataset
        filecount
           the number of files from this dataset (across all volumes) currently cached
        totalsize
           the total number of bytes stored for this dataset (across all volumes)
        checked, checkedDate
           the oldest date-time (in epoch seconds and as an ISO string, respectively) that a file from
           this dataset was checked for integrity.
        files
           an array of file descriptions, each a dictionary with contents as what is returned by 
           :py:meth:`describe_datafile`
        """
        return self.svccli.get_json(self.OBJS_EP+aipid)

    def describe_datafile(self, aipid, filepath):
        """
        return a metadata description of a file stored in the cache.  
        """
        return self.svccli.get_json(self.OBJS_EP+aipid+'/'+filepath)

    def is_cached(self, aipid, filepath):
        """
        return True if the given file currently exists in the cache.
        """
        try:
            return self.describe_datafile(aipid, filepath).get('cached')
        except DistribResourceNotFound:
            return False

    def request_caching(self, aipid, filepath=None, force=False):
        """
        request that a particular file or all the files in a dataset be cached.  Returned is 
        the state of the cache (as returned by :py:meth:`get_cache_queue`) after the request. 
        :param str    aipid:  the AIP ID of the dataset
        :param str filepath:  the filepath for the file to be cached; if None, all the files
                              from the dataset will be cached.
        :param str    force:  if False (default) only those files not currently cached will 
                              be added; already-cached files will be untouched.  If True, 
                              all requested files will be recached regardless of their current 
                              status.  
        """
        ep = self.QUEU_EP + aipid
        if filepath:
            ep += '/' + filepath.strip('/')

        params = None
        if force:
            params = {'recache': '1'}

        return self.svccli.put_json(ep, params=params)

    def get_cache_queue(self):
        """
        return a dictionary describing the state of the cache queue.
        """
        return self.get_json(self.QUEU_EP)

    def uncache(self, aipid, filepath=None):
        """
        request that data be removed from the cache.  Nothing is done (and not exceptions are
        raised) if the dataset or particular files are not currently in the cache.  
        :param str    aipid:  the AIP ID of the dataset
        :param str filepath:  the filepath for the file to be cached; if None, all the files
                              from the dataset will be cached.
        """
        ep = self.OBJS_EP + aipid
        if filepath:
            ep += '/' + filepath.strip('/')
        ep += "/:cached"
        
        self.svccli.del_json(ep)

