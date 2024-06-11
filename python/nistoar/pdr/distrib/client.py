"""
This distrib submodule provides a client interface to the PDR Distribution 
Service.
"""
import os, sys, shutil, logging, json

import urllib
import requests

from ..exceptions import PDRException, PDRServiceException, PDRServerError

class RESTServiceClient(object):
    """
    a generic public client interface to a REST service featuring JSON inputs and outputs
    """

    def __init__(self, baseurl, authkey=None):
        """
        initialized the service to the given base URL
        """
        self.base = baseurl.rstrip('/')
        self.key = authkey

    def get_json(self, relurl):
        """
        retrieve JSON-encoded data from the specified endpoint.  An Exception
        is raised if the request resource does not exists or if its content
        is not retrievable as JSON.  

        :param str relurl:   a relative URL for the desired resource
        """
        return self._send_request(relurl, 'GET')

    def put_json(self, relurl, body="", params=None):
        """
        PUT a message onto the service
        """
        return self._send_request(relurl, 'PUT')

    def del_json(self, relurl, params=None):
        """
        send a delete request
        """
        return self._send_request(relurl, 'DELETE', params=params)

    def _send_request(self, relurl, meth="GET", body=None, params=None):
        if not relurl.startswith('/'):
            relurl = '/'+relurl
        hdrs = { "Accept": "application/json" }
        if self.key:
            hdrs["Authorization"] = "Bearer: "+self.key

        args = { "headers": hdrs }
        if meth != "GET":
            if body is None:
                body = ""
            args['json'] = body
        if params:
            args['params'] = params

        resp = None
        try:
            resp = requests.request(meth, self.base+relurl, **args)

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
            if resp and resp.text and \
               ("<body" in resp.text or "<BODY" in resp.text):
                raise DistribServerError(relurl,
                                         message="HTML returned where JSON "+
                                         "expected (is service URL correct?)",
                                         cause=ex)
            else:
                raise DistribServerError(relurl,
                                         message="Unable to parse response as "+
                                         "JSON (is service URL correct?)",
                                         cause=ex)
        except requests.RequestException as ex:
            raise DistribServerError(relurl, cause=ex)
        
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

    def head(self, relurl):
        """
        send a HEAD request to the given relative URL to determine if the 
        resource it refers to is available.  

        :rtype tuple:  a 2-tuple including the integer response status (e.g. 
                       200, 404, etc) and the associated message.  
        :raises DistribServerError: if there is a failure while trying to 
                       connect to the server.
        """
        if not relurl.startswith('/'):
            relurl = '/'+relurl

        resp = None
        try:
            resp = requests.get(self.base+relurl, allow_redirects=True)
            return (resp.status_code, resp.reason)

        except requests.RequestException as ex:
            raise DistribServerError(message="Trouble connecting to distribution"
                                     +" service: "+ str(ex), cause=ex)
        
        finally:
            if resp is not None:
                resp.close()

    def is_available(self, relurl):
        """
        return True if the resource pointed to by the given URL is retrievable
        by sending a HEAD request to it and ensuring a response in the 200 range.
        False is returned if any other status code is returned or if there is 
        an error connecting to the service.
        """
        try:
            stat = self.head(relurl)[0]
            return stat >= 200 and stat < 300
        except DistribServerError as ex:
            return False

        

class DistribServiceException(PDRServiceException):
    """
    an exception indicating a problem using the distribution service.
    """

    def __init__(self, message, resource=None, http_code=None, http_reason=None, 
                 cause=None):
        super(DistribServiceException, self).__init__("distribution",
                                resource, http_code, http_status, message, cause)

class DistribServerError(PDRServerError):
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
        super(DistribServerError, self).__init__("distribution", resource,
                                         http_code, http_reason, message, cause)
                                                 

class DistribClientError(PDRServiceException):
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
          
        super(DistribClientError, self).__init__("distribution", resource,
                                          http_code, http_reason, message, cause)
                                                 

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
        
        super(DistribClientError, self).__init__("distribution", resource, 404, 
                                                 http_reason, message, cause)




