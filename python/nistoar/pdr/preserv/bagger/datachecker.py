"""
tools for checking the availability of distributions described in a NIST bag.
"""
import os, re
from collections import Mapping

import multibag as mb
import requests

from .utils import parse_bag_name
from ...exceptions import ConfigurationException, StateException
from ...distrib import (RESTServiceClient, BagDistribClient, DistribServerError,
                        DistribServiceException, DistribResourceNotFound)

class DataChecker(object):
    """
    a class that will run checks to ensure all data distributions are accounted
    for and available.

    A distribution that is listed as a downloadable component in the NERDm 
    metadata must be available from one of the following sources:
    1) under the bag's data payload directory (at the location given by 
       the component's filepath property)
    2) from the URL given by the downloadURL property (tested via a HEAD request)
    3) in a multibag member bag as indicated in the multibag/file-lookup.tsv 
       file found in either,
       a) a cached copy of the specified member bag
       b) in a remote copy of the specified member bag available via the 
          distribution service.
    """

    AVAIL_NOT = "not available"
    AVAIL_IN_BAG = "available in current bag"
    AVAIL_IN_CACHED_BAG = "available in cached bag"
    AVAIL_VIA_URL = "available via download URL"
    AVAIL_IN_REMOTE_BAG = "available in remote bag via service"

    def __init__(self, bag, config=None, log=None):
        """
        initialize the checker around the bag to be checked
        """
        self.bag = bag
        if not config:
            config = {}
        self.cfg = config
        self.log = log
        
        self._store = config.get('store_dir')
        self._mbag = mb.open_headbag(bag.dir)
        self._disturlpat = self.cfg.get('pdr_dist_url_pattern',
                                        r'^https?://[^/]+/od/ds/(.+)')
        try:
            self._disturlpat = re.compile(self._disturlpat)
            if self._disturlpat.groups < 1:
                raise ConfigurationException("pdr_dist_url_pattern: regex is " +
                                          "missing group to capture filepath: "+
                                             self._disturlpat.pattern)
        except re.error as ex:
            raise ConfigurationException("pdr_dist_url_pattern: regex does " +
                                         "not compile: " + self._disturlpat)

        self._distsvc = None
        svcurl = self.cfg.get('repo_access',{}).get('distrib_service',{}) \
                         .get('service_endpoint')
        if svcurl:
            self._distsvc = RESTServiceClient(svcurl)

    def available_in_bag(self, cmp):
        """
        return True if the specified data is found in the bag.  

        The file can be specified either via its component metadata (as a 
        dict) or directly by its filepath property (as a string).  False is 
        returned if either the filepath is not found in the bag or the filepath 
        property is not included in the input metadata.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's filepath.
        """
        if isinstance(cmp, Mapping):
            if 'filepath' not in cmp:
                return False
            cmp = cmp['filepath']

        path = os.path.join(self.bag.data_dir, cmp)
        return os.path.isfile(path)

    def bag_location(self, cmp):
        """
        return the name of the member bag that contains specified the data file
        or None if a member bag is not specified.

        The file can be specified either via its component metadata (as a 
        dict) or directly by its filepath property (as a string).  None is 
        returned if either the filepath is not found in the bag or the filepath 
        property is not included in the input metadata.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's filepath.
        """
        if isinstance(cmp, Mapping):
            if 'filepath' not in cmp:
                return None
            cmp = cmp['filepath']

        path = '/'.join(['data', cmp])
        return self._mbag.lookup_file(path)

    def located_here(self, cmp):
        """
        return True if the the downloadable file should be located in the 
        current bag.

        The file can be specified either via its component metadata (as a 
        dict) or directly by its filepath property (as a string).  False is 
        returned if either the filepath is not found in the bag or the filepath 
        property is not included in the input metadata.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's filepath.
        """
        loc = self.bag_location(cmp)
        return loc == self.bag.name

    def available_in_cached_bag(self, cmp, inbag=None):
        """
        return true if the specified data file can be found in a cached
        member bag.

        The file can be specified either via its component metadata (as a 
        dict) or directly by its filepath property (as a string).  False is 
        returned if either the filepath is not found in a cached bag, if 
        the location of the bag cache directory is not known, or if the 
        filepath property is not included in the given component metadata.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's filepath.
        :param str inbag:  the name of the bag that should contain the file.  
                      If None, this path will be looked up in the current bag's 
                      file lookup list.
        """
        if isinstance(cmp, Mapping):
            if 'filepath' not in cmp:
                return False
            cmp = cmp['filepath']

        if not inbag:
            inbag = self.bag_location(cmp)
        if not inbag:
            return False

        locs = [ os.path.join(self._store, inbag) ]
        if not os.path.isdir(locs[0]):
            locs = [os.path.join(self._store, f) for f in os.listdir(self._store)
                                                 if f.startswith(inbag+".")]
            if len(locs) == 0:
                return False

        for loc in locs:
            if not os.path.isfile(loc):
                continue
            try:
                mbag = mb.open_bag(loc)
            except Exception as ex:
                continue
            if mbag.isfile('/'.join(['data', cmp])):
                return True

        return False

    def has_pdr_url(self, cmp):
        """
        return True if the specified data file is downloadable via the PDR's
        distribution service.  

        The data file can either be specified via its component metadata (as a 
        dict) or directly by its downloadURL property (as a string).  False 
        is returned if the property is not included in the component metadata
        or if the URL does not match the base associated with the distribution
        service.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's download URL.
        """
        if isinstance(cmp, Mapping):
            if 'downloadURL' not in cmp:
                return False
            cmp = cmp['downloadURL']

        return bool(self._disturlpat.match(cmp))

    @classmethod
    def head_url(cls, url):
        """
        make a HEAD request on the given URL and return the status code
        and associated message as a tuple.  

        This raises a requests.RequestsException if a connection cannot be 
        made.
        """
        resp = None
        try:
            resp = requests.head(url, allow_redirects=True)
            return (resp.status_code, resp.reason)
        finally:
            if resp is not None:
                resp.close()
        

    def available_via_url(self, cmp):
        """
        return True if the specified data file appears available via its 
        download URL.  A HEAD request is conducted on the download URL; True 
        is returned if the request returns a 2XX status.

        The data file can either be specified via its component metadata (as a 
        dict) or directly by its downloadURL property (as a string).  False 
        is returned if the property is not included in the component metadata
        or if the URL does not match the base associated with the distribution
        service.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's download URL.
        """
        dlurl = cmp
        if isinstance(cmp, Mapping):
            if 'downloadURL' not in cmp:
                return False
            dlurl = cmp['downloadURL']
            cmp = cmp.get('filepath', dlurl)

        try:
            (stat, msg) = self.head_url(dlurl)
            ok = stat >= 200 and stat < 300
            if not ok and self.log:
                self.log.debug("HEAD on %s: %s (%i)", cmp, msg, stat)
            return ok
        except requests.RequestException as ex:
            if self.log:
                self.log.warn("Trouble accessing download URL: " + str(ex) +
                              "\n  ({0})".format(cmp))
            return False

    def available_as(self, cmp, strict=False, viadistrib=True):
        """
        return an enumeration value indicating how the specified data file is 
        found to be available.  

        :param dict cmp:     a dict containing the component metadata describing 
                             the data file
        :param bool strict:  if True, don't assume if remote bag containing the
                             file is available that the file is actually in the
                             bag.  Currently, this implementation will return
                             False if the file is not available from any other
                             source.  
        :param bool viadistrib:  if True, only check to see if the file is 
                             available via its downloadURL if the URL points
                             to the PDR's distribution service. 
        """
        if self.available_in_bag(cmp):
            return self.AVAIL_IN_BAG
        if self.available_in_cached_bag(cmp):
            return self.AVAIL_IN_CACHED_BAG
        if (not viadistrib or self.has_pdr_url(cmp.get('downloadURL',''))) and \
           self.available_via_url(cmp):
            return self.AVAIL_VIA_URL
        if not strict and self._distsvc and self.containing_bag_available(cmp):
            return self.AVAIL_IN_REMOTE_BAG
        return self.AVAIL_NOT

    def available(self, cmp, strict=False, viadistrib=True):
        """
        return True if the specified data file is currently available somewhere.
        This function (using available_as()) will cycle through possible 
        locations of the file, searching until it finds it.  This includes:
          1. the current bag
          2. in a bag located in a local cache
          3. at its download URL
          4. in a remote bag available via the distribution service*

        When the file is found, True is returned; otherwise, False is returned.

        *in this implementation with location (4), the remote bag's contents 
        are not examined; only the availability of that bag is checked.  
        """
        return self.available_as(cmp, strict, viadistrib) is not self.AVAIL_NOT
                                        
    def containing_bag_available(self, cmp):
        """
        return True if the member bag that contains the specified component
        is available via the distribution service.  An exception is raised 
        if this checker was not configured with the distribution service 
        endpoint configured or if the service is not available.  

        The file can be specified either via its component metadata (as a 
        dict) or directly by its filepath property (as a string).  False is 
        returned if either the filepath is not found in a cached bag, if 
        the location of the bag cache directory is not known, or if the 
        filepath property is not included in the given component metadata.

        :param cmp:   either a dict containing the component metadata describing 
                      the data file or a string giving the file's filepath.
        """
        if isinstance(cmp, Mapping):
            if 'filepath' not in cmp:
                return False
            cmp = cmp['filepath']

        mbagname = self.bag_location(cmp)
        if not mbagname:
            return False
        try:
            parts = parse_bag_name(mbagname)
        except ValueError as ex:
            if self.log:
                self.log.warn("data file listed as in bag with illegal name: "+
                              mbagname)
            return False
        parts[1] = parts[1] or "0"
        parts[1] = re.sub(r'_','.',parts[1])
        
        if not self._distsvc:
            raise StateException("Distribution service not configured")
        bagsvc = BagDistribClient(parts[0], self._distsvc)

        try:
            matches = [f for f in bagsvc.list_for_version(parts[1])
                         if f.startswith(mbagname+".")]
            return len(matches) > 0

        except DistribResourceNotFound as ex:
            if self.log:
                self.log.debug("No bags for %s found via bag service", parts[0])
            return False

        except DistribServerError as ex:
            if self.log:
                self.log.error("query on %s: service connect error: %s",
                               mbagname, str(ex))
            return False

        except DistribServiceError as ex:
            if self.log:
                self.log.error("unexpected error while querying on %s: %s",
                               mbagname, str(ex))
            

    def unavailable_files(self, strict=False, viadistrib=True):
        """
        return a list of the data file component filepaths that appear to 
        be unavailable via any means.  This is a check to make sure that all
        of the distributions listed in the NERDm record are either in the 
        present bag or otherwise previously preserved and available; in this
        case, the returned list will be empty.

        :param bool strict:  if True, don't assume if remote bag containing the
                             file is available that the file is actually in the
                             bag.  Currently, this implementation will return
                             False if the file is not available from any other
                             source.  
        :param bool viadistrib:  if True, check a file's availability only if
                             its download URL points to the PDR's 
                             distribution service. 
        """
        missing = []
        nerd = self.bag.nerdm_record(False)
        for cmp in nerd.get('components',[]):
            if "dcat:Distribution" not in cmp.get('@type',[]) or \
               'downloadURL' not in cmp:
                continue
            if viadistrib and 'downloadURL' in cmp and \
               not self.has_pdr_url(cmp['downloadURL']):
                continue
            if not self.available(cmp, strict, False):
                missing.append(cmp.get('filepath') or cmp.get('downloadURL'))

        return missing

    def all_files_available(self, strict=False, viadistrib=True):
        """
        return True if all of the data file components are available in some
        form.  This is a check to make sure that all
        of the distributions listed in the NERDm record are either in the 
        present bag or otherwise previously preserved and available; in this
        case, the returned list will be empty.

        :param bool viadistrib:  if True, check only those files if its
                                 downloadURL if the URL points to the PDR's 
                                 distribution service. 
        """
        return len(self.unavailable_files(strict, viadistrib)) == 0

    def unindexed_files(self, viadistrib=True):
        """
        return the data file component filepaths that are missing from the 
        mulitbag file lookup list.  This is a check to make sure that all
        of the distributions listed in the NERDm record are findable either in 
        the present bag or other member bags; in this case, the returned list 
        will be empty.

        :param bool viadistrib:  if True, check only those files if its
                                 downloadURL if the URL points to the PDR's 
                                 distribution service. 
        """
        missing = []
        nerd = self.bag.nerdm_record(False)
        for cmp in nerd.get('components',[]):
            if "dcat:Distribution" not in cmp.get('@type',[]) or \
               'filepath' not in cmp:
                continue
            if viadistrib and 'downloadURL' in cmp and \
               not self.has_pdr_url(cmp['downloadURL']):
                continue
            if not self.bag_location(cmp):
                missing.append(cmp.get('filepath') or cmp.get('downloadURL'))

        return missing

    def all_files_indexed(self, viadistrib=True):
        """
        return True if all the data file components given in the NERDm metadata
        are included in the multibag file lookup list.  This is a check to make 
        sure that all of the distributions listed in the NERDm record are 
        findable either in the present bag or other member bags.

        :param bool viadistrib:  if True, check only those files if its
                                 downloadURL if the URL points to the PDR's 
                                 distribution service. 
        """
        return len(self.unindexed_files(viadistrib)) == 0

    def check_all_data_files(self, strict=False, viadistrib=True):
        """
        return True if all the data files described in the NERDm metadata are
        findable and available.  This returns False if either 
        all_files_indexed() or all_files_available() return False.

        :param bool viadistrib:  if True, check only those files if its
                                 downloadURL if the URL points to the PDR's 
                                 distribution service. 
        """
        return self.all_files_indexed(viadistrib) and \
               self.all_files_available(strict, viadistrib)

