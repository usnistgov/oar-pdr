"""
A WSGI web service front-end to the ThreadedPreservationService.

This module provides the most basic implementation of a WSGI application 
necessary for integration into a WSGI server.  It should be replaced with 
a framework-based implementation if any further capabilities are needed.
"""

import os, sys, logging, json, cgi, re
from wsgiref.headers import Headers

from .service import ThreadedPreservationService, RerequestException
from . import status
from .. import PreservationSystem

log = logging.getLogger(PreservationSystem().subsystem_abbrev).getChild("preserve")

DEF_BASE_PATH = "/"

class PreservationRequestApp(object):

    def __init__(self, config):
        self.cfg = config
        try:
            wd = config['working_dir']
            self.base_path = config.get('base_path', DEF_BASE_PATH)
        except KeyError, e:
            key = e.message
            raise ConfigurationException("Missing required config param: "+
                                         key)

        self.preserv = ThreadedPreservationService(config)
        self.siptype = 'midas'
        authkey = config.get('auth_key')
        authmeth= config.get('auth_method')
        if authmeth != 'header':
            authmeth = 'qparam'
        self._auth = (authmeth, authkey)
        if not self._auth[1]:
            log.warn("Service launched without authorization key defined")

    def handle_request(self, env, start_resp):
        handler = Handler(self.preserv, self.siptype,
                          env, start_resp, self._auth)
        return handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = PreservationRequestApp

class Handler(object):

    badidre = re.compile(r"[<>\s]")

    def __init__(self, service, siptype, wsgienv, start_resp,
                 auth=None):
        self._svc = service
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        self._auth = auth

    def send_error(self, code, message):
        stat = "{0} {1}".format(str(code), message)
        self._start(stat, [], sys.exc_info())

    def add_header(self, name, value):
        self._hdr.add_header(name, value)

    def set_response(self, code, message):
        self._code = code
        self._msg = message

    def end_headers(self):
        stat = "{0} {1}".format(str(self._code), self._msg)
        self._start(stat, self._hdr.items())

    def handle(self):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/').strip('/')
        if not self.authorize():
            return self.send_unauthorized()

        if hasattr(self, meth_handler):
            out = getattr(self, meth_handler)(path)
            if isinstance(out, list) and len(out) > 0:
                out.append('\n')
            return out
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")

    def authorize(self):
        if self._auth[0] == 'header':
            return self.authorize_via_headertoken()
        else:
            return self.authorize_via_queryparam()

    def authorize_via_queryparam(self):
        params = cgi.parse_qs(self._env.get('QUERY_STRING', ''))
        auths = params.get('auth',[])
        if self._auth[1]:
            # match the last value provided
            return len(auths) > 0 and self._auth[1] == auths[-1]  
        if len(auths) > 0:
            log.warn("Authorization key provided, but none has been configured")
        return len(auths) == 0

    def authorize_via_headertoken(self):
        authhdr = self._env.get('HTTP_AUTHORIZATION', "")
        log.debug("Request HTTP_AUTHORIZATION: %s", authhdr)
        parts = authhdr.split()
        if self._auth[1]:
            return len(parts) > 1 and parts[0] == "Bearer" and \
                self._auth[1] == parts[1]
        if authhdr:
            log.warn("Authorization key provided, but none has been configured")
        return authhdr == ""

    def send_unauthorized(self):
        self.set_response(401, "Not authorized")
        if self._auth[0] == 'header':
            self.add_header('WWW-Authenticate', 'Bearer')
        self.end_headers()
        return []

    def do_GET(self, path):
        # return the status on request or a list of previous requests
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
            if len(steps) > 2:
                path = '/'.join(steps[1:])
                self.send_error(400, "Unsupported SIP identifier: "+path)
                return []
            elif len(steps) > 1:
                if steps[1].startswith("_") or steps[1].startswith(".") or \
                   self.badidre.search(steps[1]):
                    
                    self.send_error(400, "Unsupported SIP identifier: "+path)
                    return []
                
                return self.request_status(steps[1])
                
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
            reqs = self._svc.requests('midas')
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
            stat = self._svc.status(sipid, 'midas')
            out = json.dumps(stat)
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return ["{}"]

        if stat['state'] == status.NOT_READY and \
           stat['message'].startswith('Internal Error'):
            self.set_response(500, stat['message'])
            
        elif stat['state'] == status.FORGOTTEN:
            self.set_response(404, "Preservation history for SIP identifer not found "+
                              "(or forgotten)")
        elif stat['state'] == status.NOT_FOUND:
            self.set_response(404, "Preservation history for SIP identifer not found")

        elif stat['state'] == status.READY:
            self.set_response(404, "Preservation history for SIP identifer not found (but is ready)")

        else:
            self.set_response(200, "Preservation record found")

        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

    def do_PATCH(self, path):
        # create an update request

        steps = path.split('/')
        if steps[0] == '':
            self.send_error(403, "PATCH is not supported on this resource")
            return ['{}']
            
        elif steps[0] == 'midas':
            if len(steps) > 2:
                path = '/'.join(steps[1:])
                self.send_error(400, "Not a legal SIP ID: "+path)
            elif len(steps) > 1:
                return self.update_sip(steps[1])
            else:
                self.send_error(403, "PATCH not supported on this resource")
        else:
            self.send_error(404, "SIP Type not supported")
            return ["{}"]

    def update_sip(self, sipid):

        try: 
            out = self._svc.update(sipid, 'midas')
        
            if out['state'] == status.NOT_FOUND:
                log.warn("Requested SIP ID not found: "+sipid)
                self.set_response(404, "SIP not found (or is not ready)")
            elif out['state'] == status.SUCCESSFUL:
                log.info("SIP update request completed synchronously: "+
                         sipid)
                self.set_response(201, "SIP update completed successfully")
            elif out['state'] == status.FAILED:
                log.error(stat['message'])
                self.set_response(500, "SIP update failed: " +
                                  stat['message'])
            else:
                log.info("SIP update request in progress asynchronously: " +
                         sipid)
                self.set_response(202, "SIP " + out['message'])

            out = json.dumps(out)

        except RerequestException, ex:
            log.warn("Rerequest of SIP update detected: "+sipid)
            self.set_response(403, "Preservation update for SIP was already "+
                              "requested (current status: "+ex.state+")")
            
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

        

    def do_PUT(self, path):
        # create a new preservation request
        
        steps = path.split('/')
        if steps[0] == '':
            self.send_error(403, "PUT is not supported on this resource")
            return ['{}']
            
        elif steps[0] == 'midas':
            if len(steps) > 2:
                path = '/'.join(steps[1:])
                self.send_error(400, "Not a legal SIP ID: "+path)
            elif len(steps) > 1:
                return self.preserve_sip(steps[1])
            else:
                self.send_error(403, "PUT not supported on this resource")
        else:
            self.send_error(404, "SIP Type not supported")
            return ["{}"]

    def preserve_sip(self, sipid):
        out = {}
        try: 
            out = self._svc.preserve(sipid, 'midas')
        
            if out['state'] == status.NOT_FOUND:
                log.warn("Requested SIP ID not found: "+sipid)
                self.set_response(404, "SIP not found")
            elif out['state'] == status.NOT_READY:
                log.warn("Premature request for SIP preservation (not ready): "+
                         sipid)
                self.set_response(409, "SIP is not ready")
            elif out['state'] == status.SUCCESSFUL:
                log.info("SIP preservation request completed synchronously: "+
                         sipid)
                self.set_response(201, "SIP preservation completed successfully")
            elif out['state'] == status.FAILED:
                log.error(out['message'])
                self.set_response(500, "SIP preservation failed: " +
                                  out['message'])
            else:
                log.info("SIP preservation request in progress asynchronously: "+
                         sipid)
                self.set_response(202, "SIP "+out.message)

            out = json.dumps(out)

        except RerequestException, ex:
            log.warn("Rerequest of SIP detected: "+sipid)
            self.set_response(403, "Preservation for SIP was already requested "+
                              "(current status: "+ex.state+")")

        except Exception, ex:
            log.exception("preservation request failure for sip=%s: %s",
                          sipid, str(ex))
            self.set_response(500, "Internal server error")
            
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [out]

