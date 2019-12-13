"""
a module for utilizing the MIDAS API for interacting with the NIST EDI.
"""
import os, re, logging, json
from collections import OrderedDict

import urllib
import requests

from ...exceptions import (PDRException, PDRServiceException, PDRServerError,
                           ConfigurationException)

_arkpre = re.compile(r'^ark:/\d+/')
def _stripark(id):
    return _arkpre.sub('', id)
_mdsshldr = re.compile(r'^mds\d+\-')

def midasid2recnum(midasid):
    midasid = _stripark(midasid)
    mdsmatch = _mdsshldr.search(midasid)
    if mdsmatch:
        return midasid[mdsmatch.start():]
    if len(midasid) > 32:
        return midasid[32:]
    return midasid

class MIDASClient(object):
    """
    a class for interacting with the MIDAS API
    """

    def __init__(self, config, baseurl=None, logger=None):
        """
        initialize the client.  

        :param dict config:   configuration data for the client.
        :param str  baseurl:  the base URL for the MIDAS API to connect to.  If 
                              not provided, the base URL will be pulled from the 
                              configuration data (via "service_endpoint")
        """
        self.cfg = config
        if not baseurl:
            baseurl = self.cfg.get('service_endpoint')
        if not baseurl:
            raise ConfigurationException("Missing required config paramter: " +
                                         "service_endpoint")
        self.baseurl = baseurl
        if not self.baseurl.endswith('/'):
            self.baseurl += '/'
        self._authkey = self.cfg.get('update_auth_key')
        if not logger:
            logger = logging.getLogger("MIDASClient")
        self.log = logger

    def _get_json(self, relurl, resp):
        try:
            if resp.status_code >= 500:
                raise MIDASServerError(relurl, resp.status_code, resp.reason)
            elif resp.status_code == 404:
                raise MIDASRecordNotFound(relurl, resp.reason)
            elif resp.status_code == 406:
                raise MIDASClientError(relurl, resp.status_code, resp.reason,
                                         message="JSON data not available from"+
                                         " this URL (is URL correct?)")
            elif resp.status_code >= 400:
                raise MIDASClientError(relurl, resp.status_code, resp.reason)
            elif resp.status_code != 200:
                raise MIDASServerError(relurl, resp.status_code, resp.reason,
                               message="Unexpected response from server: {0} {1}"
                                        .format(resp.status_code, resp.reason))

            return resp.json(object_pairs_hook=OrderedDict)
        except ValueError as ex:
            if resp and resp.text and \
               ("<body" in resp.text or "<BODY" in resp.text):
                raise MIDASServerError(midasid,
                                       message="HTML returned where JSON "+
                                       "expected (is service URL correct?)",
                                       cause=ex)
            else:
                raise MIDASServerError(midasid,
                                       message="Unable to parse response as "+
                                       "JSON (is service URL correct?)",
                                       cause=ex)

    def _extract_pod(self, data, id):
        if 'dataset' not in data:
            raise MIDASServerError(id, message="Unexpected Serivce response: "+
                                   "data is missing 'dataset' property")
        return data['dataset']
        
    def get_pod(self, midasid):
        """
        return the POD record associated with the given MIDAS identifier.
        """
        hdrs = { "Accept": "application/json" }
        if self._authkey:
            hdrs['Authorization'] = "Bearer " + self._authkey

        resp = None
        midasrecn = midasid2recnum(midasid)
        try:
            self.log.debug("Retrieving latest POD record from MIDAS for rec="
                           +midasrecn);
            resp = requests.get(self.baseurl + midasrecn, headers=hdrs)
            return self._extract_pod(self._get_json(midasrecn, resp), midasrecn)
        except requests.RequestException as ex:
            raise MIDASServerError(midasrecn, cause=ex)
        
    def put_pod(self, pod, midasid=None):
        """
        update the POD record associated with the given MIDAS identifier.  
        
        :param dict pod:  the new POD record to save under the given ID
        :param str midasid:  the identifier for the record.  If not provided,
                             the value of the 'identifier' parameter will be 
                             assumed.  
        """
        if 'identifier' not in pod:
            raise ValueError("'identifier' not in input data " +
                             "(is this a POD record?)")
        if pod['identifier'] != midasid:
            raise ValueError("pod['identifier'] does not match id="+midasid)
            
        hdrs = { "Accept": "application/json" }
        if self._authkey:
            hdrs['Authorization'] = "Bearer " + self._authkey

        midasrecn = midasid2recnum(midasid)
        try:
            self.log.debug("Submitting POD record update to MIDAS for rec="
                           +midasrecn);
            data = {"dataset": pod}
            resp = requests.put(self.baseurl+midasrecn, json=data,
                                headers=hdrs)
            return self._extract_pod(self._get_json(midasrecn, resp), midasrecn)
        except requests.RequestException as ex:
            raise MIDASServerError(midasrecn, cause=ex)

    def authorized(self, userid, midasid):
        """
        return True if the user with the given identifier is authorized to 
        update the record with the given ID.
        """
        midasrecn = midasid2recnum(midasid);
        relurl = "{0}/{1}".format(midasrecn, userid)
        url = self.baseurl + relurl
        hdrs = {}
        if self._authkey:
            hdrs['Authorization'] = "Bearer " + self._authkey

        msg = "Edit authorization check for user=" + userid + \
              " on record no.=" + midasrecn
        self.log.info(msg+"...")
        if 'Authorization' not in hdrs:
            self.log.warn("No Authorization header included!")
        
        try:
            resp = requests.get(url, headers=hdrs)
            if resp.status_code == 200:
                body = resp.json()
                if ("editable" in body):
                    self.log.info("MIDAS says: %sauthorized",
                                  (not body['editable'] and "not ") or "")
                    return body['editable'];
                else:
                    raise MIDASServerError(relurl, resp.status_code,
                                           "Unexpected content from MIDAS: "+
                                           json.dumps(body))

            elif resp.status_code == 403:
                raise MIDASClientError(relurl, resp.status_code,
                                       "Bad service authorization key")
            elif resp.status_code >= 500:
                raise MIDASServerError(relurl, resp.status_code, resp.reason)
            elif resp.status_code == 404:
                raise MIDASRecordNotFound(relurl, resp.reason,
                                          "ID not found: "+midasid)
            elif resp.status_code >= 400:
                raise MIDASClientError(relurl, resp.status_code, resp.reason)
            else:
                raise MIDASServerError(relurl, resp.status_code, resp.reason,
                               message="Unexpected response from server: {0} {1}"
                                        .format(resp.status_code, resp.reason))
        except requests.RequestException as ex:
            raise MIDASServerError(relurl,
                                   message="HTTP client request failure: "
                                           +str(ex),
                                   cause=ex)

        except ValueError as ex:
            raise MIDASServerError(relurl, 
                                   message="Trouble parsing JSON response body: "
                                           +str(ex),
                                   cause=ex)




    
class MIDASServiceException(PDRServiceException):
    """
    an exception indicating a problem using the MIDAS service.
    """

    def __init__(self, message, resource=None, http_code=None, http_reason=None, 
                 cause=None):
        super(MIDASServiceException, self).__init__("MIDAS", resource, http_code,
                                                    http_status, message, cause)

class MIDASServerError(PDRServerError):
    """
    an exception indicating an error occurred on the server-side while 
    trying to access the MIDAS service.  

    This exception includes three extra public properties, `status`, `reason`, 
    and `resource` which capture the HTTP response status code, the associated 
    HTTP response message, and (optionally) a name for the record being 
    submitted to it.  
    """

    def __init__(self, resource=None, http_code=None, http_reason=None, 
                 message=None, cause=None):
        super(MIDASServerError, self).__init__("MIDAS", resource, http_code, 
                                               http_reason, message, cause)
                                                 

class MIDASClientError(PDRServiceException):
    """
    an exception indicating an error occurred on the client-side while 
    trying to access the MIDAS service.  

    This exception includes three extra public properties, `status`, `reason`, 
    and `resource` which capture the HTTP response status code, the associated 
    HTTP response message, and (optionally) a name for the record being 
    submitted to it.  
    """

    def __init__(self, resource, http_code, http_reason, message=None,
                 cause=None):
        if not message:
            message = "client-side MIDAS error occurred"
            if resource:
                message += " while processing " + resource
            message += ": {0} {1}".format(http_code, http_reason)
          
        super(MIDASClientError, self).__init__("MIDAS", resource, http_code, 
                                               http_reason, message, cause)
                                                 

class MIDASRecordNotFound(MIDASClientError):
    """
    An error indicating that a requested resource is not available via the
    MIDAS service.
    """
    def __init__(self, resource, http_reason=None, message=None,
                 cause=None):
        if not message:
            message = "Requested MIDAS resource not found"
            if resource:
                message += ": "+resource
        
        super(MIDASClientError, self).__init__(resource, 404, http_reason, 
                                               message, cause)




