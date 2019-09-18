from __future__ import absolute_import, print_function
import json, os, cgi, sys, re, hashlib, json
from datetime import datetime
from wsgiref.headers import Headers
from collections import OrderedDict, Mapping

try:
    import uwsgi
except ImportError:
    # print("Warning: running midas-uwsgi in simulate mode", file=sys.stderr)
    class uwsgi_mod(object):
        def __init__(self):
            self.opt={}
            self.started_on = None
    uwsgi=uwsgi_mod()

_arkpre = re.compile(r'^ark:/\d+/')
def _stripark(id):
    return _arkpre.sub('', id)

class SimArchive(object):
    def __init__(self, archdir):
        self.dir = archdir

    def get_pod(self, midasrecn):
        file = os.path.join(self.dir, midasrecn+".json")
        if not os.path.exists(file):
            return None

        mod = datetime.fromtimestamp(os.stat(file).st_mtime).isoformat()

        out = OrderedDict()
        with open(file) as fd:
            out['dataset'] = json.load(fd, object_pairs_hook=OrderedDict)
        out['last_modified'] = mod
        return json.dumps(out, fd, indent=2)

    def put_pod(self, midasrecn, intext):
        file = os.path.join(self.dir, midasrecn+".json")
        if not os.path.exists(file):
            return None

        try:
            data = json.loads(intext)
        except ValueError as ex:
            raise ValueError('Input does not appear to be JSON (starts with "' +
                             intext[:35] + '...")')
        if not isinstance(data, Mapping) or 'dataset' not in data:
            raise ValueError('JSON data missing "dataset" property (starts ' +
                             'with "' + intext[:35] + '...")')
        if not isinstance(data['dataset'], Mapping):
            raise ValueError('JSON data missing proper "dataset" property ' +
                             'content (value = ' + str(data['dataset']))

        out = json.dumps(data['dataset'], indent=2)
        with open(file, 'w') as fd:
            fd.write(out)

        data['last_modified'] = \
                    datetime.fromtimestamp(os.stat(file).st_mtime).isoformat()
        return json.dumps(data, indent=2)


class SimMidas(object):
    def __init__(self, archdir, authkey=None, basepath="/edi/"):
        self.archive = SimArchive(archdir)
        self._authkey = authkey
        if basepath is None:
            basepath = "/"
        self._basepath = basepath

    def handle_request(self, env, start_resp):
        handler = SimMidasHandler(self.archive, env, start_resp,
                                  self._basepath, self._authkey)
        return handler.handle(env, start_resp)

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

class SimMidasHandler(object):

    def __init__(self, archive, wsgienv, start_resp, basepath, authkey=None):
        self.arch = archive
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        self._authkey = authkey
        self._basepath = basepath

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

        path = self._env.get('PATH_INFO', '/')
        if not path.startswith(self._basepath):
            return self.send_error(404, "Path not found")
        path = path.lstrip(self._basepath)
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
        if len(parts) > 2:
            return self.send_error(404, "Path not found")

        try:
            if len(parts) > 1:
                out = self.user_can_update(parts[1], parts[0])
            else:
                out = self.arch.get_pod(parts[0])
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
            return self.send_unauthorized()
        
        parts = path.split('/')
        if len(parts) > 2:
            return self.send_error(404, "Path not found")
        if len(parts) > 1:
            return self.send_error(405, "PUT not allowed on this path")

        if not input:
            return self.send_error(400, "No POD data provided")
        try:
            data = input.read()
        except OSError as ex:
            return self.send_error(500, "Internal Error")
        if not data:
            return self.send_error(400, "No input data provided")

        try:
            out = self.arch.put_pod(path, data)
        except ValueError as ex:
            return self.send_error(400, "Bad input data (%s)" % str(ex))
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
