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
from ...preserv.service import status as ps
from ...preserv.service.service import RerequestException, PreservationStateError
from .webrecord import WebRecorder
from ....id import NIST_ARK_NAAN
from ejsonschema import ValidationError
from ... import config as cfgmod

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
            if not os.path.isabs(wrlogf) and cfgmod.global_logdir:
                wrlogf = os.path.join(cfgmod.global_logdir, wrlogf)
            self._recorder = WebRecorder(wrlogf, "pubserver")

        self.base_path = asre(config.get('base_path', DEF_BASE_PATH))
        self.draft_res = asre(config.get('draft_path', '/draft/'))
        self.latest_res = asre(config.get('latest_path', '/latest/'))
        self.preserve_res = asre(config.get('preserve_path', '/preserve/'))

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
        elif self.preserve_res.match(path):
            path = self.preserve_res.sub('', path)
            handler = PreserveHandler(path, self.pubsvc, env, start_resp, self._authkey, req)

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

class PreserveHandler(Handler):
    """
    The web request handler for preservation requests
    """

    badidre = re.compile(r"[<>\s]")

    def __init__(self, path, service, wsgienv, start_resp, auth=None, req=None):
        super(PreserveHandler, self).__init__(path, wsgienv, start_resp, auth, req)
        self._svc = service

    def do_GET(self, path):
        # return the status on request or a list of previous requests
        if self._reqrec:
            self._reqrec.record()
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        steps = path.split('/')
        if steps[0] == '':
            try:
                out = json.dumps(['midas'])
            except Exception, ex:
                log.exception("Internal error: "+str(ex))
                self.send_error(500, "Internal error")
                return ["[]"]

            self.set_response(200, "Supported SIP Types")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [out]

        elif steps[0] == 'midas':
            path = '/'.join(steps[1:])
            if (len(steps) > 2 and steps[1] != "ark:") or len(steps) > 4:
                self.send_error(400, "Unsupported SIP identifier: "+path)
                return []
            elif len(steps) > 1:
                if steps[1].startswith("_") or steps[1].startswith(".") or \
                   self.badidre.search(steps[1]):
                    
                    self.send_error(400, "Unsupported SIP identifier: "+path)
                    return []
                
                return self.request_status(path)
                
            else:
                return self.requests()
        else:
            self.send_error(404, "SIP Type not supported")
            return ["[]"]

    def do_HEAD(self, path):
        self.do_GET(path)
        return []

    def requests(self):
        """
        return a list of identifiers for which preservation has been 
        requested.
        """
        try: 
            reqs = self._svc.preservation_requests()
            out = json.dumps(reqs.keys())
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return ['[]']

        self.set_response(200, "Preservation requests by SIP ID")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

    def request_status(self, sipid):
        """
        return the status of a particular preservation request
        """
        try:
            stat = self._svc.preservation_status(sipid)
            out = json.dumps(stat)
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return ["{}"]

        if stat['state'] == ps.NOT_READY and \
           stat['message'].startswith('Internal Error'):
            self.set_response(500, stat['message'])
            
        elif stat['state'] == ps.FORGOTTEN:
            self.set_response(404, "Preservation history for SIP identifer not found "+
                              "(or forgotten)")
        elif stat['state'] == ps.NOT_FOUND:
            self.set_response(404, "Preservation history for SIP identifer not found")

        elif stat['state'] == ps.READY:
            self.set_response(404, "Preservation history for SIP identifer not found (but is ready)")

        else:
            self.set_response(200, "Preservation record found")

        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

    def do_PUT(self, path):
        # create a new preservation request
        if self._reqrec:
            self._reqrec.record()
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        steps = path.split('/')
        if steps[0] == '':
            self.send_error(403, "PUT is not supported on this resource")
            return ['{}']
            
        elif steps[0] == 'midas':
            path = '/'.join(steps[1:])
            if (len(steps) > 2 and steps[1] != "ark:") or len(steps) > 4:
                self.send_error(400, "Not a legal SIP ID: "+path)
            elif len(steps) > 1:
                if steps[1].startswith("_") or steps[1].startswith(".") or \
                   self.badidre.search(steps[1]):
                    
                    self.send_error(400, "Unsupported SIP identifier: "+path)
                    return []
                
                return self.preserve_sip(path)
            else:
                self.send_error(403, "PUT not supported on this resource")
        else:
            self.send_error(404, "SIP Type not supported")
            return ["{}"]

    def preserve_sip(self, sipid):
        out = {}
        try: 
            out = self._svc.preserve_new(sipid)

            # FYI: detecting success or failure is handled through the
            # returned status object because the preservation service will
            # launch the job asynchronously.  Fast failures resulting from
            # checks that can be done syncronously result in exceptions (see
            # below).  
            if out['state'] == ps.NOT_FOUND:
                log.warn("Requested SIP ID not found: "+sipid)
                self.set_response(404, "SIP not found")
            elif out['state'] == ps.NOT_READY:
                log.warn("Premature request for SIP preservation (not ready): "+
                         sipid)
                self.set_response(409, "SIP is not ready")
            elif out['state'] == ps.SUCCESSFUL:
                log.info("SIP preservation request completed synchronously: "+
                         sipid)
                self.set_response(201, "SIP preservation completed successfully")
            elif out['state'] == ps.CONFLICT:
                log.error(out['message'])
                out['state'] = ps.FAILED
                self.set_response(409, out['message'])
            elif out['state'] == ps.FAILED:
                log.error(out['message'])
                self.set_response(500, "SIP preservation failed: " +
                                  out['message'])
            else:
                log.info("SIP preservation request in progress asynchronously: "+
                         sipid)
                self.set_response(202, "SIP "+out['message'])

            out = json.dumps(out)

        except RerequestException as ex:
            log.warn("Rerequest of SIP detected: "+sipid)
            out = json.dumps({
                "id": sipid,
                "state": ps.IN_PROGRESS,
                "message": str(ex),
                "history": []
            })
            self.set_response(403, "Preservation for SIP was already requested "+
                              "(current status: "+ex.state+")")

        except PreservationStateError as ex:
            log.warn("Wrong AIP state for client request: "+str(ex))
            out = json.dumps({
                "id": sipid,
                "state": ps.CONFLICT,
                "message": str(ex),
                "history": []
            })
            self.set_response(409, "Already preserved (need to request update "+
                                   "via PATCH?)")

        except Exception as ex:
            log.exception("preservation request failure for sip=%s: %s",
                          sipid, str(ex))
            self.set_response(500, "Internal server error")
            
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

    def do_PATCH(self, path):
        # create an update request
        if self._reqrec:
            self._reqrec.record()
        if not self.authorized():
            return self.send_error(401, "Unauthorized")
        
        steps = path.split('/')
        if steps[0] == '':
            self.send_error(403, "PATCH is not supported on this resource")
            return ['{}']
            
        elif steps[0] == 'midas':
            path = '/'.join(steps[1:])
            if (len(steps) > 2 and steps[1] != "ark:") or len(steps) > 4:
                self.send_error(400, "Not a legal SIP ID: "+path)
            elif len(steps) > 1:
                if steps[1].startswith("_") or steps[1].startswith(".") or \
                   self.badidre.search(steps[1]):
                    
                    self.send_error(400, "Unsupported SIP identifier: "+path)
                    return []
                
                return self.update_sip(path)
            else:
                self.send_error(403, "PATCH not supported on this resource")
        else:
            self.send_error(404, "SIP Type not supported")
            return ["{}"]

    def update_sip(self, sipid):
        out = {}
        try: 
            out = self._svc.preserve_update(sipid)
        
            # FYI: detecting success or failure is handled through the
            # returned status object because the preservation service will
            # launch the job asynchronously.  Fast failures resulting from
            # checks that can be done syncronously result in exceptions (see
            # below).  
            if out['state'] == ps.NOT_FOUND:
                log.warn("Requested SIP ID not found: "+sipid)
                self.set_response(404, "SIP not found (or is not ready)")
            elif out['state'] == ps.SUCCESSFUL:
                log.info("SIP update request completed synchronously: "+
                         sipid)
                self.set_response(200, "SIP update completed successfully")
            elif out['state'] == ps.CONFLICT:
                log.error(out['message'])
                out['state'] = ps.FAILED
                self.set_response(409, out['message'])
            elif out['state'] == ps.FAILED:
                log.error(out['message'])
                self.set_response(500, "SIP update failed: " +
                                  out['message'])
            else:
                log.info("SIP update request in progress asynchronously: " +
                         sipid)
                self.set_response(202, "SIP " + out['message'])

            out = json.dumps(out)

        except RerequestException, ex:
            log.warn("Rerequest of SIP update detected: "+sipid)
            out = json.dumps({
                "id": sipid,
                "state": ps.IN_PROGRESS,
                "message": str(ex),
                "history": []
            })
            self.set_response(403, "Preservation update for SIP was already "+
                              "requested (current status: "+ex.state+")")
            
        except PreservationStateError as ex:
            log.warn("Wrong AIP state for client request: "+str(ex))
            out = json.dumps({
                "id": sipid,
                "state": ps.CONFLICT,
                "message": str(ex),
                "history": []
            })
            self.set_response(409, "Not previously preserved (need to issue "+
                                   "PUT?)")

        except Exception as ex:
            log.exception("preservation request failure for sip=%s: %s",
                          sipid, str(ex))
            self.set_response(500, "Internal server error")
            
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

        

    


