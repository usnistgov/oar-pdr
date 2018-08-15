from __future__ import print_function
import json, os, cgi, sys, re, hashlib, traceback as tb
from collections import OrderedDict
from wsgiref.headers import Headers

testdir = os.path.dirname(os.path.abspath(__file__))
def_archdir = os.path.join(testdir, 'data')

try:
    import uwsgi
except ImportError:
    print("Warning: running ingest-uwsgi in simulate mode", file=sys.stderr)
    class uwsgi_mod(object):
        def __init__(self):
            self.opt={}
    uwsgi=uwsgi_mod()

class SimArchive(object):
    def __init__(self, archdir):
        self.dir = archdir
        self.lu = {}
        self.loadlu()
    def loadlu(self):
        for rec in [f for f in os.listdir(self.dir) if f.endswith(".json")]:
            try:
                with open(os.path.join(self.dir,f)) as fd:
                    data = json.load(fd, object_pairs_hook=OrderedDict)
                if "ediid" in data:
                    self.lu[data["ediid"]] = f[:-1*len(".json")]
            except:
                pass
    def ediid_to_id(self, ediid):
        return self.lu.get(ediid)

class SimRMM(object):
    def __init__(self, recdir):
        self.archive = SimArchive(recdir)

    def handle_request(self, env, start_resp):
        handler = SimRMMHandler(self.archive, env, start_resp)
        return handler.handle(env, start_resp)

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

class SimRMMHandler(object):

    def __init__(self, archive, wsgienv, start_resp):
        self.arch = archive
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"

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

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path, params)
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")

    def do_GET(self, path, params=None):
        if path:
            path = path.rstrip('/')
        if path.startswith("records"):
            path = path[len("records"):].lstrip('/')
        id = None
        print("path="+str(path)+"; params="+str(params))
        if not path and params and "@id" in params:
            path = params["@id"]
            path = (len(path) > 0 and path[0]) or ''
        if path:
            if path.startswith("ark:/88434/"):
                id = path[len("ark:/88434/"):]
            else:
                self.arch.loadlu()
                id = self.arch.ediid_to_id(path)

        if id:
            mdfile = os.path.join(self.arch.dir, id+".json")
        if not id or not os.path.exists(mdfile):
            if not id:
                id = "resource"
            return self.send_error(404, id + " does not exist")

        try:
            with open(mdfile) as fd:
                data = json.load(fd, object_pairs_hook=OrderedDict)
                data["_id"] ={"timestamp":1521220572,"machineIdentifier":3325465}
                if params and "@id" in params:
                    data = { "ResultCount": 1, "PageSize": 0,
                             "ResultData": [ data ] }
        except Exception as ex:
            print(str(ex))
            return self.send_error(500, "Internal error")

        self.set_response(200, "Identifier exists")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()
        return [ json.dumps(data, indent=2) + "\n" ]
            
            
archdir = uwsgi.opt.get("archive_dir", def_archdir)
application = SimRMM(archdir)
