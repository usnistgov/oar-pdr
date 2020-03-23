from __future__ import absolute_import, print_function
import json, os, cgi, sys, re, hashlib, json, logging
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

class SimCustom(object):
    def __init__(self, authkey=None, basepath="/draft/"):
        self.data = {}
        self.upds = {}
        self._authkey = authkey
        if basepath is None:
            basepath = "/"
        self._basepath = basepath

    def exists(self, id):
        return id in self.data

    def get(self, id):
        out = dict(self.data[id].items())
        out.update(self.upds[id])
        return out

    def get_updates(self, id):
        return self.upds[id]

    def delete(self, id):
        del self.data[id]
        del self.upds[id]

    def put(self, id, rec):
        self.upds[id] = { '_editStatus': "in progress" }
        self.data[id] = rec

    def set_done(self, id):
        self.upds[id]['_editStatus'] = "done"

    def update(self, id, updates):
        if id not in self.upds:
            raise KeyError(id)
        self.upds[id].update(updates)

    def remove_all(self):
        self.data = {}
        self.upds = {}

    def ids(self):
        return self.data.keys()

    def handle_request(self, env, start_resp):
        handler = SimCustomHandler(self, env, start_resp,
                                   self._basepath, self._authkey)
        return handler.handle(env, start_resp)

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)


class SimCustomHandler(object):
    def __init__(self, repo, wsgienv, start_resp, basepath, authkey=None):
        self.repo = repo
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
        return self.send_error(401, "Not "+self._authkey)

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
        if not path:
            return self.send_error(200, "Ready")

        if not self.authorized():
            return self.send_unauthorized()
        
        parts = path.split('/')
        if len(parts) > 1:
            return self.send_error(404, "Path not found")
        id = parts[0]

        try:
            if self.repo.exists(id):
                return self.send_error(200, "Draft found")
            else:
                return self.send_error(404, "Draft not found with identifier")
        except Exception as ex:
            return self.send_error(500, "Unexpected service error: "+str(ex))

    def do_GET(self, path, input=None, params=None, forhead=False,
               ok=200, okmsg="Identifier resolved"):
        if not path:
            return self.list_all()

        if not self.authorized():
            return self.send_unauthorized()
        
        parts = path.split('/')
        if len(parts) > 1:
            return self.send_error(404, "Path not found")
        id = parts[0]

        try:
            if params and "updates" in params.get("view"):
                out = self.repo.get_updates(id)
            else:
                out = self.repo.get(id)
            out = json.dumps(out)

        except KeyError as ex:
            return self.send_error(404, "Identifier not found")
        except ValueError as ex:
            return self.send_error(500, "System Error: internal data corruption")
        except Exception as ex:
            return self.send_error(500, "Unexpected service error: "+str(ex))

        self.set_response(ok, okmsg)
        self.add_header('Content-Type', 'application/json')
        self.add_header('Content-Length', str(len(out)))
        self.end_headers()

        if forhead:
            return []
        return [out]

    def list_all(self):
        try:
            out = json.dumps(self.repo.ids())
        except Exception as ex:
            return self.send_error(500, "Unexpected service error: "+str(ex))

        self.set_response(200, "Ready")
        self.add_header('Content-Type', 'application/json')
        self.add_header('Content-Length', str(len(out)))
        self.end_headers()
        return [out]

    def remove_all(self):
        try:
            self.repo.remove_all()
            return self.send_error(200, "Repo cleared")
        except Exception as ex:
            return self.send_error(500, "Unexpected service error: "+str(ex))

    def do_DELETE(self, path, input=None, params=None):
        if not path:
            return self.remove_all()

        if not self.authorized():
            return self.send_unauthorized()
        
        parts = path.split('/')
        if len(parts) > 1:
            return self.send_error(404, "Path not found")
        id = parts[0]

        if not self.repo.exists(id):
            return self.send_error(404, "No draft for identifier")
        
        try:
            self.repo.delete(id)
            return self.send_error(200, "Draft deleted")
        except KeyError as ex:
            return self.send_error(404, "No draft for identifier")
        except Exception as ex:
            return self.send_error(500, "Unexpected service error: "+str(ex))


    def do_PUT(self, path, input, params=None):
        if not path:
            return self.send_error(405, "Missing identifier")

        if not self.authorized():
            return self.send_unauthorized()
        
        parts = path.split('/')
        if len(parts) > 1:
            return self.send_error(404, "Path not found")
        id = parts[0]

        try:
            nerdm = json.load(input)
            self.repo.put(id, nerdm)
            return self.send_error(201, "Accepted")
        except (ValueError, TypeError) as ex:
            self.send_error(400, "Input is not JSON")
        except Exception as ex:
            return self.send_error(500, "Unexpected service error: "+str(ex))

    def do_PATCH(self, path, input, params=None):
        if not path:
            return self.send_error(405, "Missing identifier")

        if not self.authorized():
            return self.send_unauthorized()
        
        parts = path.split('/')
        if len(parts) > 1:
            return self.send_error(404, "Path not found")
        id = parts[0]

        try:
            updates = json.load(input)
            self.repo.update(id, updates)
            return self.send_error(201, "Draft updated")
        except KeyError as ex:
            return self.send_error(404, "No draft with identifier")
        except ValueError as ex:
            return self.send_error(400, "Input is not JSON")



authkey = uwsgi.opt.get("auth_key")
application = SimCustom(authkey)
