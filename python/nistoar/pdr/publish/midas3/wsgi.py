"""
A WSGI web service front-end to the MIDAS-to-PDR publishing service (pubserver),
Mark III version. 

This module provides the most basic implementation of a WSGI application 
necessary for integration into a WSGI server.  It should be replaced with 
a framework-based implementation if any further capabilities are needed.
"""
import os, sys, logging, json, re
from wsgiref.headers import Headers
from cgi import parse_qs, escape as escape_qp
from collections import OrderedDict

from .. import PublishSystem, PDRServerError
from .service import (MIDAS3PublishingService, SIPDirectoryNotFound, IDNotFound,
                      ConfigurationException, StateException, InvalidRequest)
from .webrecord import WebRecorder
from ....id import NIST_ARK_NAAN
from ejsonschema import ValidationError

log = logging.getLogger(PublishSystem().subsystem_abbrev).getChild("pubserv")

DEF_BASE_PATH = "/pod/"
ARK_NAAN = NIST_ARK_NAAN

class MIDAS3PublishingApp(object):
    """
    A WSGI-compliant service app for managing interactions between MIDAS and the 
    PDR's pre-publication landing page service during the publication preparation 
    process.  This interface sits in front of a MIDAS3PublishingService instance.

    Endpoints:
    /pod/latest
    POST /pod/latest/ -- creates or updates a data publication with a POD
      record from MIDAS.  This is called by MIDAS every time it saves changes to
      the POD metadata
    GET /pod/latest/{dsid} -- returns the latest save POD record

    /pod/draft
    PUT /pod/draft/{dsid} -- creates (over-writing previously PUT records) a draft
       NERDm record from a submitted POD record in the customization service for 
       editing via the landing page 
    GET /pod/draft/{dsid} -- retrieves an updated POD record generated from the 
       NERDm record being edited via the landing page
    DELETE /pod/draft/{dsid} -- deletes the NERDm record in the customization service.  
    """

    def __init__(self, config):
        def asre(path):
            if path.endswith('/'):
                path = path[:-1]
            path += r'(/|$)'
            if not path.startswith('/'):
                path = '/'+path
            return re.compile(path)
        
        level = config.get('loglevel')
        if level:
            log.setLevel(level)

        # log input messages
        self._recorder = None
        wrlogf = config.get('record_to')
        if wrlogf:
            self._recorder = WebRecorder(wrlogf, "pubserver")

        self.base_path = asre(config.get('base_path', DEF_BASE_PATH))
        self.draft_res = asre(config.get('draft_path', '/draft/'))
        self.latest_res = asre(config.get('draft_path', '/latest/'))

        self._authkey = config.get('auth_key')

        self.pubsvc = MIDAS3PublishingService(config)

    def handle_request(self, env, start_resp):
        handler = None
        req = None
        if self._recorder:
            req = self._recorder.from_wsgi(env)
        path = env.get('PATH_INFO', '/')
        if self.base_path.match(path):
            path = self.base_path.sub('/', path)
            if self.draft_res.match(path):
                path = self.draft_res.sub('', path)
                handler = DraftHandler(path, self.pubsvc, env, start_resp, self._authkey, req)
            elif self.latest_res.match(path):
                path = self.latest_res.sub('', path)
                handler = LatestHandler(path, self.pubsvc, env, start_resp, self._authkey, req)

        if not handler:
            handler = Handler(path, env, start_resp, self._authkey, req)
        return handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = MIDAS3PublishingApp

_badidre = re.compile(r"[<>\s/]")
_arkidre = re.compile(r"^ark:/"+ARK_NAAN+"/")
_arklocalre = re.compile(r"^mds\d+\-\d{3}\d+")

class Handler(object):
    """
    a default web request handler that also serves as a base class for the 
    handlers specialized for the supported resource paths.
    """

    def __init__(self, path, wsgienv, start_resp, auth=None, req=None):
        self._path = path
        self._env = wsgienv
        self._start = start_resp
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        self._authkey = auth
        self._reqrec = req

        self._meth = self._env.get('REQUEST_METHOD', 'GET')

        # This accommadates MIDAS whose HTTP client api is unable to
        # submit against some standard methods.  
        if self._env.get('HTTP_X_HTTP_METHOD_OVERRIDE'):
            self._meth = self._env.get('HTTP_X_HTTP_METHOD_OVERRIDE')

    def send_error(self, code, message):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], sys.exc_info())
        return []

    def send_ok(self, message="OK", content=None, code=200):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], None)
        if content is not None:
            return [content]
        return []

    def add_header(self, name, value):
        # Caution: HTTP does not support Unicode characters (see
        # https://www.python.org/dev/peps/pep-0333/#unicode-issues);
        # thus, this will raise a UnicodeEncodeError if the input strings
        # include Unicode (char code > 255).
        e = "ISO-8859-1"
        self._hdr.add_header(name.encode(e), value.encode(e))

    def set_response(self, code, message):
        self._code = code
        self._msg = message

    def end_headers(self):
        status = "{0} {1}".format(str(self._code), self._msg)
        ###DEBUG:
        log.debug("sending header: %s", str(self._hdr.items()))
        ###DEBUG:
        self._start(status, self._hdr.items())

    _spdel = re.compile(r'\s+')
    def authorized(self):
        auth = self._spdel.split(self._env.get('HTTP_AUTHORIZATION', ""), 1)
        if not self._authkey and not auth[0]:
            return True
        if bool(auth[0]) != bool(self._authkey):
            return False
        if auth[0] != "Bearer" or len(auth) < 2:
            return False
        return auth[1] == self._authkey

    def handle(self):
        meth_handler = 'do_'+self._meth

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(self._path)
        else:
            if self._reqrec:
                self._reqrec.record()
            return self.send_error(405, self._meth +
                                   " not supported on this resource")


    def do_GET(self, path):
        if self._reqrec:
            self._reqrec.record()
        if path and path != "/":
           return self.send_error(404, "Resource does not exist")

        self.set_response(200, "Ready")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()

        return [ '"Ready"' ]

class DraftHandler(Handler):
    """
    The web request handler for the draft API used to transfer POD editing control 
    to the customization service.
    """

    def __init__(self, path, service, wsgienv, start_resp, auth=None, req=None):
        super(DraftHandler, self).__init__(path, wsgienv, start_resp, auth, req)
        self._svc = service

    def do_GET(self, path):
        if self._reqrec:
            self._reqrec.record()
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        path = path.strip('/')
        if not path:
            return self.send_ok("Ready", '"No identifier given"')

        midasid = path
        if not midasid.startswith("ark:"):
            if len(path) >= 30:
                # this looks like an old-style MIDAS identifier
                if _badidre.search(midasid):
                    return self.send_error(400, "Bad identifier syntax")
            else:
                # assume new style identifier and convert to ark: syntax
                midasid = "ark:/"+ARK_NAAN+"/"+midasid
        if midasid.startswith("ark:") and not _arkidre.search(path):
            return self.send_error(400, "Bad identifier syntax")
        
        try:
            out = self._svc.get_customized_pod(midasid)
            out = json.dumps(out, indent=2)
        except IDNotFound as ex:
            return self.send_error(404, "Identifier not found as draft")
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            return self.send_error(500, "Internal error")

        self.set_response(200, "Found draft")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()

        return [ out ]

    def do_POST(self, path):
        # create
        if path:
            return self.send_error(405, "Method not allowed on this resource")

        return self.create_draft()

    def do_PUT(self, path):
        # create
        if not path:
            return self.send_error(405, "Method not allowed on this resource")

        return self.create_draft(path)

    def create_draft(self, path=''):
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        if "/json" not in self._env.get('CONTENT_TYPE', 'application/json'):
            return self.send_error(415, "Non-JSON input content type specified")

        midasid = path
        if midasid:
            if not midasid.startswith("ark:"):
                if len(path) >= 30:
                    # this looks like an old-style MIDAS identifier
                    if _badidre.search(midasid):
                        return self.send_error(400, "Bad identifier syntax")
                else:
                    # assume new style identifier and convert to ark: syntax
                    midasid = "ark:/"+ARK_NAAN+"/"+midasid
            if midasid.startswith("ark:") and not _arkidre.search(path):
                return self.send_error(400, "Bad identifier syntax")
        
        try:
            bodyin = self._env.get('wsgi.input')
            if bodyin is None:
                if self._reqrec:
                    self._reqrec.record()
                return send_error(400, "Missing input POD document")
            if log.isEnabledFor(logging.DEBUG) or self._reqrec:
                body = bodyin.read()
                pod = json.loads(body, object_pairs_hook=OrderedDict)
            else:
                pod = json.load(bodyin, object_pairs_hook=OrderedDict)
            if self._reqrec:
                self._reqrec.add_body_text(json.dumps(pod, indent=2)).record()

        except (ValueError, TypeError) as ex:
            if log.isEnabledFor(logging.DEBUG):
                log.error("Failed to parse input: %s", str(ex))
                log.debug("\n%s", body)
            if self._reqrec:
                self._reqrec.add_body_text(body).record()
            return self.send_error(400, "Input not parseable as JSON")

        except Exception as ex:
            if self._reqrec:
                self._reqrec.add_body_text(body).record()
            raise

        if 'identifier' not in pod:
            return self.send_error(400, "Input POD missing required identifier property")
        if not midasid:
            midasid = pod['identifier']

        try:
            
            self._svc.start_customization_for(pod)

        except ValidationError as ex:
            log.error("/latest/: Input is not a valid POD record:\n  "+str(ex))
            return self.send_error(400, "Input is not a valid POD record")
        except PDRServerError as ex:
            log.exception("Problem accessing customization service: "+str(ex))
            return self.send_error(502, "Customization Service access failure")
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            return self.send_error(500, "Internal error")

        return self.send_ok("Draft created", code=201)


    def do_DELETE(self, path):
        if self._reqrec:
            self._reqrec.record()
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        midasid = path
        if not midasid.startswith("ark:"):
            if len(path) >= 30:
                # this looks like an old-style MIDAS identifier
                if _badidre.search(midasid):
                    return self.send_error(400, "Bad identifier syntax")
            else:
                # assume new style identifier and convert to ark: syntax
                midasid = "ark:/"+ARK_NAAN+"/"+midasid
        if midasid.startswith("ark:") and not _arkidre.search(path):
            return self.send_error(400, "Bad identifier syntax")
        
        try:

            self._svc.end_customization_for(midasid)

        except IDNotFound as ex:
            return self.send_error(404, "Draft not found")
        except PDRServerError as ex:
            log.exception("Problem accessing customization service: "+str(ex))
            return self.send_error(502, "Customization Service access failure")
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            return self.send_error(500, "Internal error")

        return self.send_ok("Draft deleted")


class LatestHandler(Handler):
    """
    The web request handler for the latest API used by MIDAS to send saved POD records
    to the PDR.
    """

    def __init__(self, path, service, wsgienv, start_resp, auth=None, req=None):
        super(LatestHandler, self).__init__(path, wsgienv, start_resp, auth, req)
        self._svc = service

    def do_POST(self, path):
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        if path:
            return self.send_error(405, "Method not allowed on this resource")

        if "/json" not in self._env.get('CONTENT_TYPE', 'application/json'):
            return self.send_error(415, "Non-JSON input content type specified")
        
        try:
            bodyin = self._env.get('wsgi.input')
            if bodyin is None:
                if self._reqrec:
                    self._reqrec.record()
                return send_error(400, "Missing input POD document")

            if log.isEnabledFor(logging.DEBUG) or self._reqrec:
                body = bodyin.read()
                pod = json.loads(body, object_pairs_hook=OrderedDict)
            else:
                pod = json.load(bodyin, object_pairs_hook=OrderedDict)
            if self._reqrec:
                self._reqrec.add_body_text(json.dumps(pod, indent=2)).record()

        except (ValueError, TypeError) as ex:
            if log.isEnabledFor(logging.DEBUG):
                log.error("Failed to parse input: %s", str(ex))
                log.debug("\n%s", body)
            if self._reqrec:
                self._reqrec.add_body_text(body).record()
            return self.send_error(400, "Input not parseable as JSON")

        if 'identifier' not in pod:
            return self.send_error(400, "Input POD missing required identifier property")

        try:
            self._svc.update_ds_with_pod(pod)
        except ValidationError as ex:
            log.error("/latest/: Input is not a valid POD record:\n  "+str(ex))
            return self.send_error(400, "Input is not a valid POD record")
        except PDRServerError as ex:
            log.exception("Problem accessing customization service: "+str(ex))
            return self.send_error(502, "Customization Service access failure")
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            return self.send_error(500, "Internal error")

        return self.send_ok("POD Accepted", code=201)


    def do_GET(self, path):
        if self._reqrec:
            self._reqrec.record()
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        path = path.strip('/')
        if not path:
            self.set_response(200, "Ready")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return ['"No identifier given"']

        if not _arkidre.search(path) and _badidre.search(path):
            return self.send_error(400, "Bad identifier syntax")
        if _arklocalre.search(path):
            path = "ark:/"+ARK_NAAN+"/"+path

        try:
            pod = self._svc.get_pod(path)
            pod = json.dumps(pod, indent=2)
        except IDNotFound as ex:
            return self.send_error(404, "Record with identifier not currently being edited")
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            return self.send_error(500, "Internal error")

        self.set_response(200, "Found")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()

        return [ pod ]




