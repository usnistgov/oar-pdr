"""
This distrib submodule provides a client interface to the PDR Distribution 
Service.
"""
import os, sys, shutil, logging, json

import urllib
import requests

from ..exceptions import PDRException

class RESTServiceClient(object):
    """
    a generic public client interface to a REST service
    """

    def __init__(self, baseurl):
        """
        initialized the service to the given base URL
        """
        self.base = baseurl

    def get_json(self, relurl):
        """
        retrieve JSON-encoded data from the specified endpoint.  An Exception
        is raised if the request resource does not exists or if its content
        is not retrievable as JSON.  

        :param str relurl:   a relative URL for the desired resource
        """
        if not relurl.startswith('/'):
            relurl = '/'+relurl
        hdrs = { "Accept": "application/json" }

        try:
            resp = requests.get(self.base+relurl, headers=hdrs)

            if resp.status_code >= 500:
                raise DistribServerError(relurl, resp.status_code, resp.reason)
            elif resp.status_code == 404:
                raise DistribResourceNotFound(relurl, resp.reason)
            elif resp.status_code == 406:
                raise DistribClientError(relurl, resp.status_code, resp.reason,
                                         message="JSON data not available from"+
                                         " this URL (is URL correct?)")
            elif resp.status_code >= 400:
                raise DistribClientError(relurl, resp.status_code, resp.reason)
            elif resp.status_code != 200:
                raise DistribServerError(relurl, resp.status_code, resp.reason,
                               message="Unexpected response from server: {0} {1}"
                                        .format(resp.status_code, resp.reason))

            return resp.json()
        except ValueError as ex:
            if resp.text and ("<body" in resp.text or "<BODY" in resp.text):
                raise DistribServerError(relurl,
                                         message="HTML returned where JSON "+
                                        "expected (is service URL correct?)")
            else:
                raise DistribServerError(relurl,
                                         message="Unable to parse response as "+
                                        "JSON (is service URL correct?)")
        except requests.RequestException as ex:
            raise DistribServerError(relurl,
                                     message="Trouble connecting to distribution"
                                     +" service: "+ str(ex), cause=ex)
        
    def get_stream(self, relurl):
        """
        return an open file-like object that will stream the content from 
        the given URL
        """
        if not relurl.startswith('/'):
            relurl = '/'+relurl

        try:
            out = urllib.urlopen(self.base+relurl)

            code = out.getcode()
            hdrs = out.info()
            reason = "(unknown)"
            if 'status' in hdrs:
                reason = hdrs['status']
                if re.match(r'^\d{3} ', reason):
                    reason = reason[4:]

            if code >= 500:
                raise DistribServerError(relurl, code, reason)
            elif code == 404:
                raise DistribResourceNotFound(relurl, reason)
            elif code == 406:
                raise DistribClientError(relurl, code, reason,
                                         message="JSON data not available from"+
                                         " this URL (is URL correct?)")
            elif code >= 400:
                raise DistribClientError(relurl, code, reason)
            elif code != 200:
                raise DistribServerError(relurl, code, reason,
                               message="Unexpected response from server: {0} {1}"
                                        .format(code, reason))

            return out
        except IOError as ex:
            raise DistribServerError(message="Trouble connecting to distribution"
                                     +" service: "+str(ex), cause=ex)

    def retrieve_file(self, relurl, filepath):
        """
        retrive the content at the given URL and save it to a local file
        """
        if not relurl.startswith('/'):
            relurl = '/'+relurl

        resp = None
        try:
            resp = requests.get(self.base+relurl, stream=True)

            if resp.status_code >= 500:
                raise DistribServerError(relurl, resp.status_code, resp.reason)
            elif resp.status_code == 404:
                raise DistribResourceNotFound(relurl, resp.reason)
            elif resp.status_code >= 400:
                raise DistribClientError(relurl, resp.status_code, resp.reason)
            elif resp.status_code != 200:
                raise DistribServerError(relurl, resp.status_code, resp.reason,
                               message="Unexpected response from server: {0} {1}"
                                        .format(resp.status_code, resp.reason))

            with open(filepath, "wb") as fd:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        fd.write(chunk)
        
        except requests.RequestException as ex:
            raise DistribServerError(message="Trouble connecting to distribution"
                                     +" service: "+ str(ex), cause=ex)
        
        finally:
            if resp is not None:
                resp.close()

class DistribServiceException(PDRException):
    """
    an exception indicating a problem using the distribution service.
    """

    def __init__(self, message, resource=None, http_code=None, http_reason=None, 
                 cause=None):
        super(DistribServiceException, self).__init__(message, cause=cause)
        self.status = http_code
        self.reason = http_reason
        self.resource = resource

class DistribServerError(DistribServiceException):
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
        if not message:
            message = "server-side distribution error occurred"
            if resource:
                message += " while retrieving " + resource
            if http_code or http_reason:
                message += ":"
                if http_code:
                    message += " "+str(http_code) 
                if http_reason:
                    message += " "+str(http_reason) 
          
        super(DistribServerError, self).__init__(message, resource, http_code, 
                                                 http_reason, cause)

class DistribClientError(DistribServiceException):
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
          
        super(DistribClientError, self).__init__(message, resource, http_code, 
                                                 http_reason, cause)

class DistribResourceNotFound(DistribClientError):
    """
    An error indicating that a requested resource is not available via the
    distribution service.
    """
    def __init__(self, resource, http_reason=None, message=None,
                 cause=None):
        if not message:
            message = "Requested distribution resource not found"
            if resource:
                message += ": "+resource
        
        super(DistribClientError, self).__init__(resource, 404, 
                                                 http_reason, message, cause)


class DistribTransferError(PDRException):
    """
    an exception indicating an error occurred while downloading a file from 
    the distribution service.  It is usually not known if this is due a problem
    in the client or the server.  This error can be raised if the downloaded
    file appears to be corrupted.  
    """
    def __init__(self, resource, message=None, cause=None):
        if not message:
            message = "Problem detected in transfering " + resource + \
                      " from distribution service"
        super(PDRException, self).__init__(message, cause)
        self.resource = resource



