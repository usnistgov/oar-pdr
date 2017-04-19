"""
A WSGI web service front-end to the PrePubMetadataService.

This module provides the most basic implementation of a WSGI application 
necessary for integration into a WSGI server.  It should be replaced with 
a framework-based implementation if any further capabilities are needed.
"""
import os, sys, logging, json
from wsgiref.headers import Headers

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

        self.filemap = {}
        for loc in ('review_dir', 'upload_dir'):
            dir = config.get(loc)
            if dir:
                self.filemap[dir] = "/midasdata/"+loc

    def handle_request(self, env, start_resp):
        handler = Handler(self.mdsvc, self.filemap, env, start_resp)
        return handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = PrePubMetadaRequestApp

class Handler(object):

    def __init__(self, service, filemap, wsgienv, start_resp):
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

        if not path:
            self.code = 404
            self.send_error(self.code, "No identifier given")
            return []

        if path.startswith('/'):
            path = path[1:]
        parts = path.split('/')
        dsid = parts[0]
        filepath = "/".join(parts[1:])

        if filepath:
            return self.get_datafile(dsid, filepath)
        return self.get_metadata(dsid)

    def get_metadata(self, dsid):
        
        try:
            mdata = self._svc.resolve_id(dsid)
        except SIPDirectoryNotFound, ex:
            #TODO: consider sending a 301
            self.send_error(404,"Dataset with ID={0} not available".format(dsid))
            return []
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return []

        self.set_response(200, "Identifier found")
        self.add_header('ContentType', 'application/json')
        self.end_headers()

        return [ json.dumps(mdata, indent=4, separators=(',', ': ')) ]

    def get_datafile(self, id, filepath):

        try:
            loc, mtype = self._svc.locate_data_file(id, filepath)
        except SIPDirectoryNotFound, ex:
            #TODO: consider sending a 301
            self.send_error(404,"Dataset with ID={0} not available".format(id))
            return []
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return []
        if not loc:
            self.send_error(404, "Dataset (ID={0}) does not contain file={1}".
                                 format(id, filepath))

        xsend = None
        prfx = [p for p in self._fmap.keys() if loc.startswith(p+'/')]
        if len(prfx) > 0:
            xsend = self._fmap[prfx[0]] + loc[len(prfx[0]):]
            log.debug("Sending file via X-Accel-Redirect: %s", xsend)

        self.set_response(200, "Data file found")
        self.add_header('ContentType', mtype)
        if xsend:
            self.add_header('X-Accel-Redirect', xsend)
        self.end_headers()

        if xsend:
            return []
        return self.iter_file(loc)

    def iter_file(self, loc):
        # this is the backup, inefficient way to send a file
        with open(loc, 'rb') as fd:
            buf = fd.read(5000000)
            yield buf
        
    def do_HEAD(self, path):

        self.do_GET(path)
        return []
        

