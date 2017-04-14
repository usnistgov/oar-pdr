"""
A WSGI web service front-end to the PrePubMetadataService.

This module provides the most basic implementation of a WSGI application 
necessary for integration into a WSGI server.  It should be replaced with 
a framework-based implementation if any further capabilities are needed.
"""
import os, sys, logging, json

from .. import PublishSystem
from .serv import (PrePubMetadataService, SIPDirectoryNotFound,
                   ConfigurationException, StateException)

log = logging.getLogger(PublishSystem().subsystem_abbrev).getChild("mdserv")

# DEF_BASE_PATH = "/midas/"
DEF_BASE_PATH = "/"

class PrePubMetadaRequestApp(object):

    def __init__(self, config):
        self.base_path = config.get('base_path', DEF_BASE_PATH)
        self.mdsvc = PrePubMetadataService(config)

    def handle_request(self, env, start_resp):
        handler = Handler(self.mdsvc, env, start_resp)
        handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = PrePubMetadaRequestApp

class Handler(object):

    def __init__(self, service, wsgienv, start_resp):
        self._svc = service
        self._env = wsgienv
        self._start = start_resp
        self._meth = env.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers()
        self._code = 0
        self._msg = "unknown status"

    def send_error(self, code, message):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], sys.exc_info())

    def add_header(self, name, value):
        self._hdr.add_header(name, value)

    def set_response(self, code, message):
        self._code = 200
        self._msg = message

    def end_headers(self):
        status = "{0} {1}".format(str(self._code), self._msg)
        self._start(status, self._hdr)

    def handle(self):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')[1:]

        if hasattr(self, meth_handler):
            getattr(self, meth_handler)(path)
        else:
            self.send_error(403, self._meth + " not supported on this resource")


    def do_GET(self, path):

        if not path:
            self.code = 404
            self.send_error(self.code, "No identifier given")
            return []
        
        try:
            mdata = self._svc.resolve_id(path)
        except SIPDirectoryNotFound, ex:
            #TODO: consider sending a 301
            self.send_error(404, "Dataset with ID={0} not available".format(id))
            return []
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error: "+ str(ex))
            return []

        self.send_response(200, "Identifier found")
        self.add_header('ContentType', 'application/json')
        self.end_headers()

        return [ json.dumps(mdata, indent=4, separators=(',', ': ')) ]

        

