from __future__ import print_function
import json, os, cgi, sys
from wsgiref.headers import Headers

try:
    import uwsgi
except ImportError:
    print("Warning: running ingest-uwsgi in simulate mode", file=sys.stderr)
    class uwsgi_mod(object):
        def __init__(self):
            self.opt={}
    uwsgi=uwsgi_mod()

authkey = uwsgi.opt.get("auth_key")
            
class SimIngest(object):
    def handle_request(self, env, start_resp):
        handler = SimIngestHandler(env, start_resp)
        return handler.handle(env, start_resp)

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

class SimIngestHandler(object):

    def __init__(self, wsgienv, start_resp):
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        self._auth = authkey

    def send_error(self, code, message):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], sys.exc_info())
        return []

    def add_header(self, name, value):
        self._hdr.add_header(name, value)

    def set_response(self, code, message):
        self._code = code
        self._msg = message

    def end_headers(self):
        status = "{0} {1}".format(str(self._code), self._msg)
        self._start(status, self._hdr.items())

    def handle(self, env, start_resp):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')[1:]
        params = cgi.parse_qs(self._env.get('QUERY_STRING', ''))
        if not self.authorize(params.get('auth',[])):
            return self.send_error(401, "Not authorized")

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path, params)
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")

    def authorize(self, auths):
        if self._auth:
            # match the last value provided
            return len(auths) > 0 and self._auth == auths[-1]  
        return len(auths) == 0

    def do_GET(self, path, params=None):
        path = path.strip('/')
        if not path:
            try:
                out = json.dumps(["nerdm", "invalid"]) + '\n'
            except Exception, ex:
                return self.send_error(500, "Internal error")

            self.set_response(200, "Supported Record Types")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [out]
        elif path in "nerdm invalid".split():
            self.set_response(200, "Service is ready")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return ["Service ready\n"]
        else:
            return self.send_error(404, "resource does not exist")
            
    def do_POST(self, path, params=None):
        if not params:
            params = {}
        path = path.strip('/')
        steps = path.split('/')
        if len(steps) == 0:
            return self.send_error(405, "POST not supported on this resource")
        elif len(steps) == 1:
            if steps[0] == 'invalid' or params.get('strictness'):
                return self.post_invalid_nerdm_record()
            elif steps[0] == 'nerdm':
                return self.post_nerdm_record()
            else:
                return self.send_error(403, "new records are not allowed for " +
                                       "submission to this resource")
        else:
            return self.send_error(404, "resource does not exist")

    def post_nerdm_record(self):
        try:
            clen = int(self._env['CONTENT_LENGTH'])
        except KeyError, ex:
            return self.send_error(411, "Content-Length is required")
        except ValueError, ex:
            return self.send_error(400, "Content-Length is not an integer")

        try:
            bodyin = self._env['wsgi.input']
            doc = bodyin.read(clen)
            rec = json.loads(doc)
        except Exception, ex:
            return self.send_error(400,
                                   "Failed to load input record (bad format?): "+
                                   str(ex))

        self.set_response(200, "Record accepted")
        self.end_headers()
        return []

    def post_invalid_nerdm_record(self):
        self.set_response(400, "Input record is not valid")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [ json.dumps([
            "You have three misspelled words.",
            "The description is too flowery.",
            "And no one's taking responsibility for this embarrassment.",
            "In other words, I didn't bother to read it."
        ])
                 + '\n' ]
    
application = SimIngest()
