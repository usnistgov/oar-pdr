"""
a module for accessing public metadata about PDR objects via the Resource 
Metadata Manager (RMM).  
"""
import os, sys, shutil, logging, json
from collections import OrderedDict

import requests

from ..exceptions import PDRServiceException, PDRServerError

class MetadataClient(object):
    """
    a client interface for retrieving metadata from the RMM
    """
    def __init__(self, baseurl):
        self.baseurl = baseurl
        if not self.baseurl.endswith('/'):
            self.baseurl += '/'

    def describe(self, id):
        """
        return the NERDm metadata describing the data entity with the given
        ID.  
        """
        url = None
        if id.startswith("ark:"):
            url = self._url_for_pdr_id(id)
        else:
            url = self._url_for_ediid(id)
        out = self._retrieve(url, id)
        if "ResultData" in out:
            out = out["ResultData"]
            if len(out) == 0:
                raise IDNotFound(id)
            out = out[0]
        if "_id" in out:
            del out['_id']
        return out

    def _url_for_pdr_id(self, id):
        return self.baseurl + "records?@id=" + id

    def _url_for_ediid(self, id):
        return self.baseurl + "records/" + id

    def _retrieve(self, url, id):
        hdrs = { "Accept": "application/json" }
        try:
            resp = requests.get(url, headers=hdrs)

            if resp.status_code >= 500:
                raise RMMServerError(id, resp.status_code, resp.reason)
            elif resp.status_code == 404:
                raise IDNotFound(id)
            elif resp.status_code == 406:
                raise RMMClientError(id, resp.status_code, resp.reason,
                                     message="JSON data not available from"+
                                         " this URL (is URL correct?)")
            elif resp.status_code >= 400:
                raise RMMClientError(id, resp.status_code, resp.reason)
            elif resp.status_code != 200:
                raise RMMServerError(id, resp.status_code, resp.reason,
                               message="Unexpected response from server: {0} {1}"
                                        .format(resp.status_code, resp.reason))

            return resp.json()
        except ValueError as ex:
            if resp.text and ("<body" in resp.text or "<BODY" in resp.text):
                raise RMMServerError(id,
                                     message="HTML returned where JSON "+
                                     "expected (is service URL correct?)")
            else:
                raise RMMServerError(id,
                                     message="Unable to parse response as "+
                                     "JSON (is service URL correct?)")
        except requests.RequestException as ex:
            raise RMMServerError(id,
                                 message="Trouble connecting to distribution"
                                 +" service: "+ str(ex), cause=ex)

            
class RMMServerError(PDRServerError):
    """
    an exception indicating an error occurred on the server-side while 
    trying to access the distribution service.  

    This exception includes three extra public properties, `status`, `reason`, 
    and `resource` which capture the HTTP response status code, the associated 
    HTTP response message, and (optionally) a name for the record being 
    submitted to it.  
    """

    def __init__(self, resource=None, http_code=None, http_reason=None, 
                 message=None, cause=None):
        super(RMMServerError, self).__init__("rmm-metadata", resource,
                                         http_code, http_reason, message, cause)
                                                 

class RMMClientError(PDRServiceException):
    """
    an exception indicating an error occurred on the client-side while 
    trying to access the distribution service.  

    This exception includes three extra public properties, `status`, `reason`, 
    and `resource` which capture the HTTP response status code, the associated 
    HTTP response message, and (optionally) a name for the record being 
    submitted to it.  
    """

    def __init__(self, resource, http_code, http_reason, message=None,
                 cause=None):
        if not message:
            message = "client-side distribution error occurred"
            if resource:
                message += " while processing " + resource
            message += ": {0} {1}".format(http_code, http_reason)
          
        super(RMMClientError, self).__init__("rmm-metadata", resource,
                                          http_code, http_reason, message, cause)
                                                 

