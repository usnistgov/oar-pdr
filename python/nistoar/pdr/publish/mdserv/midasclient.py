"""
a module for utilizing the MIDAS API for interacting with the NIST EDI.
"""
import os
from collections import OrderedDict

import urllib
import requests

from ...exceptions import (PDRException, PDRServiceException, PDRServerError,
                           ConfigurationException)

class MIDASClient(object):
    """
    a class for interacting with the MIDAS API
    """

    def __init__(self, config, baseurl=None):
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

    def get_pod(self, midasid):
        """
        return the POD record associated with the given MIDAS identifier.
        """
        hdrs = { "Accept": "application/json" }
        if self._authkey:
            hdrs['Authorization'] = "Bearer " + self._authkey

        resp = None
        try:
            resp = requests.get(self.baseurl + midasid, headers=hdrs)
            return self._get_json(midasid, resp)
        except requests.RequestException as ex:
            raise MIDASServerError(midasid, cause=ex)
        
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

        try:
            resp = requests.put(self.baseurl+midasid, json=pod)
            return self._get_json(midasid, resp)
        except requests.RequestException as ex:
            raise MIDASServerError(midasid, cause=ex)
        
    def authorized(self, userid, midasid):
        """
        return True if the user with the given identifier is authorized to 
        update the record with the given ID.
        """
        return False


    
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




