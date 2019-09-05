from __future__ import absolute_import, print_function
import json, os, cgi, sys, re, hashlib, json
from wsgiref.headers import Headers
from collections import OrderedDict

try:
    import uwsgi
except ImportError:
    print("Warning: running midas-uwsgi in simulate mode", file=sys.stderr)
    class uwsgi_mod(object):
        def __init__(self):
            self.opt={}
    uwsgi=uwsgi_mod()

_arkpre = re.compile(r'^ark:/\d+/')
def _stripark(id):
    return _arkpre.sub('', id)

class SimArchive(object):
    def __init__(self, archdir):
        self.dir = archdir

    def get_pod(self, midasid):
        midasid = _stripark(midasid)
        file = os.path.join(self.dir, midasid+".json")
        if not os.path.exists(file):
            return None

        with open(file) as fd:
            return fd.read()

    def put_pod(self, midasid, podastext):
        midasid = _stripark(midasid)
        file = os.path.join(self.dir, midasid+".json")
        if not os.path.exists(file):
            return None

        with open(file, 'w') as fd:
            fd.write(podastext)

        return podastext


class SimMidas(object):
    def __init__(self, archdir, authkey=None):
        self.archive = SimArchive(archdir)
        self._authkey = authkey

    def handle_request(self, env, start_resp):
        handler = SimMidasHandler(self.archive, env, start_resp, self._authkey)
        return handler.handle(env, start_resp)

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

class SimMidasHandler(object):

    def __init__(self, archive, wsgienv, start_resp, authkey=None):
        self.arch = archive
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        self._authkey = authkey

    def send_error(self, code, message):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], sys.exc_info())
        return []

    def send_unauthorized(self):
        return self.send_error(401, "Unorthodoxed")

    def add_header(self, name, value):
        self._hdr.add_header(name, value)

    def set_response(self, code, message):
        self._code = code
        self._msg = message

    def end_headers(self):
        status = "{0} {1}".format(str(self._code), self._msg)
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

    def handle(self, env, start_resp):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')[1:]
        input = self._env.get('wsgi.input', None)
        params = cgi.parse_qs(self._env.get('QUERY_STRING', ''))
        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path, input, params)
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")

    def do_HEAD(self, path, input=None, params=None):
        return self.do_GET(path, input, params, True)

    def do_GET(self, path, input=None, params=None, forhead=False):
        if not path:
            return self.send_error(200, "Ready")
        parts = path.split('/')
        if parts[0] == "ark:":
            parts.pop(0)
            if len(parts) > 0:
                parts.pop(0)
        if len(parts) > 1:
            return self.send_error(404, "Path not found")

        try:
            out = self.arch.get_pod(path)
        except Exception as ex:
            print(str(ex))
            return self.send_error(500, "Internal Error")
        
        if not out:
            return self.send_error(404, "Identifier not found")

        self.set_response(200, "Identifier resolved")
        self.add_header('Content-Type', 'application/json')
        self.add_header('Content-Length', str(len(out)))
        self.end_headers()
        
        if forhead:
            return []
        return [out]

    def do_PUT(self, path, input=None, params=None):
        if not self.authorized():
            return send_unauthorized()
        
        parts = path.split('/')
        if parts[0] == "ark:":
            parts.pop(0)
            if len(parts) > 0:
                parts.pop(0)
        if len(parts) > 1:
            return self.send_error(404, "Path not found")

        if not input:
            return self.send_error(400, "No POD data provided")
        try:
            data = input.read()
        except OSError as ex:
            return self.send_error(500, "Internal Error")
        if not data:
            return self.send_error(400, "No POD data provided")

        try:
            out = self.arch.put_pod(path, data)
        except Exception as ex:
            print(str(ex))
            return self.send_error(500, "Internal Error")
        
        if not out:
            return self.send_error(404, "Identifier not found")

        self.set_response(200, "Identifier updated")
        self.add_header('Content-Type', 'application/json')
        self.add_header('Content-Length', str(len(out)))
        self.end_headers()
        
        return [out]

        
            
archdir = uwsgi.opt.get("archive_dir", "/tmp")
authkey = uwsgi.opt.get("auth_key")
application = SimMidas(archdir, authkey)
