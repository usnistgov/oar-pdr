"""
A WSGI web service front-end to the ThreadedPreservationService.

This module provides the most basic implementation of a WSGI application 
necessary for integration into a WSGI server.  It should be replaced with 
a framework-based implementation if any further capabilities are needed.
"""

import os, sys, logging, json
from wsgiref.headers import Headers

from .. import PreservationSystem

log = logging.getLogger(PreservationSystem().subsystem_abbrev).getChild("preserve")

DEF_BASE_PATH = "/"

class PreservationRequestApp(object):

    def __init__(self, config):
        self.base_path = config.get('base_path', DEF_BASE_PATH)
        self.preserv = ThreadedPreservationService(config)
        self.siptype = 'midas'

    def handle_request(self, env, start_resp):
        handler = Handler(self.preserv, self.siptype, env, start_resp)
        return handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = PreservationRequestApp

class Handler(object):

    def __init__(self, service, siptype, wsgienv, start_resp):
        self._svc = service
        self._fmap = filemap
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
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
        self._start(status, self._hdr.items())

    def handle(self):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')[1:]

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path)
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")

    def do_GET(self, path):
        # return the status on request or a list of previous requests
        pass

    def do_PATCH(self, path):
        # create an update request
        pass

    def do_POST(self, path):
        # create a new preservation request
        pass
