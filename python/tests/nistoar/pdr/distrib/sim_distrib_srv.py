from __future__ import print_function
import json, os, cgi, sys, re
from wsgiref.headers import Headers

try:
    import uwsgi
except ImportError:
    print("Warning: running ingest-uwsgi in simulate mode", file=sys.stderr)
    class uwsgi_mod(object):
        def __init__(self):
            self.opt={}
    uwsgi=uwsgi_mod()

testdir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
archdir = os.path.join(testdir, 'data')
    
bagvnmre = re.compile("^(\w+)\.(\d+\w*)\.mbag(\d+_\d+)-(\\d+)\.(\w+)$")
bagnmre = re.compile("^(\w+)\.mbag(\d+_\d+)-(\\d+)\.(\w+)$")

def version_of(bagname):
    m = bagvnmre.search(bagname)
    if m:
        return [int(v) for v in m.group(2).split('_')]
    return [1]
def seq_of(bagname):
    m = bagvnmre.search(bagname)
    if m:
        return int(m.group(4))
    m = bagnmre.search(bagname)
    if m:
        return int(m.group(3))
    return -1

class SimArchive(object):
    def __init__(self, archdir):
        self.dir = archdir
        self._aips = {}
        self.loadinfo()

    def add_file(self, filename):
        m = bagvnmre.search(filename)
        if m:
            aid = m.group(1)
            vers = m.group(2)
            mbv = m.group(3)
            seq = m.group(4)
            ext = m.group(5)
        else:
            m = bagnmre.search(filename)
            if m:
                aid = m.group(1)
                mbv = m.group(2)
                seq = m.group(3)
                ext = m.group(4)
                vers = "1"
        if m:
            vers = re.sub(r'_','.',vers)
            if aid not in self._aips:
                self._aips[aid] = {}
            if vers not in self._aips[aid]:
                self._aips[aid][vers] = set()
            self._aips[aid][vers].add(filename)
        
    def loadinfo(self):
        for f in os.listdir(self.dir):
            self.add_file(f)

    @property
    def aipids(self):
        return sorted([k for k in self._aips.keys()])

    def versions_for(self, aid):
        if aid not in self._aips:
            return []
        return sorted([k for k in self._aips[aid].keys()])

    def list_bags(self, aid):
        out = set()
        if aid not in self._aips:
            return list(out)
        for v in self._aips[aid]:
            out.update(self._aips[aid][v])
        return sorted(out, key=seq_of)

    def list_for_version(self, aid, vers=None):
        if aid not in self._aips:
            return []
        if not vers:
            vers = 'latest'
        if vers == 'latest':
            vers = sorted(self.versions_for(aid), key=lambda v: v.split('.'))[-1]

        out = set()
        if aid not in self._aips:
            return list(out)
        if vers not in self._aips[aid]:
            return list(out)

        out.update(self._aips[aid][vers])
        return sorted(out, key=seq_of)

    def head_for(self, aid, vers=None):
        if aid not in self._aips:
            return []
        if not vers:
            vers = 'latest'
        if vers == 'latest':
            vers = sorted(self.versions_for(aid), key=lambda v: v.split('.'))[-1]
        return self.list_for_version(aid, vers)[-1:]
        

class SimDistrib(object):
    def __init__(self, archdir):
        self.archive = SimArchive(archdir)
        
    def handle_request(self, env, start_resp):
        handler = SimDistribHandler(self.archive, env, start_resp)
        return handler.handle(env, start_resp)

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

class SimDistribHandler(object):

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
        aid = None
        vers = None
        path = path.strip('/')
        print("processing "+path)
        if not path:
            try:
                out = json.dumps(self.arch.aipids) + '\n'
            except Exception, ex:
                return self.send_error(500, "Internal error")

            self.set_response(200, "AIP Identifiers")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [out]

        elif '/' in path:
            parts = path.split('/', 1)
            aid = parts[0]
            path = (len(parts) > 1 and parts[1]) or ''
            print("accessing "+aid)

        elif path:
            aid = path
            path = ''

        else: 
            return self.send_error(404, "resource does not exist")

        if aid not in self.arch._aips:
            return self.send_error(404, "resource does not exist")
        
        if not path:
            self.set_response(200, "AIP Identifier exists")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return ['["'+aid+'"]']
        
        elif path == "_bags":
            try:
                out = json.dumps(self.arch.list_bags(aid)) + '\n'
            except Exception, ex:
                return self.send_error(500, "Internal error")

            self.set_response(200, "All bags for ID")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [out]

        elif path == "_bags/_v":
            try:
                out = json.dumps(self.arch.versions_for(aid)) + '\n'
            except Exception, ex:
                return self.send_error(500, "Internal error")

            self.set_response(200, "versions for ID")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [out]
            
        elif path.startswith("_bags/_v/"):
            path = path[len("_bags/_v/"):]

        elif path.startswith("_bags/"):
            path = path[len("_bags/"):].strip('/')
            filepath = os.path.join(self.arch.dir, path)
            if os.path.isfile(filepath):
                self.set_response(200, "Bag file found")
                self.add_header('Content-Type', "application/zip")
                self.end_headers()
                return self.iter_file(filepath)
            else:
                return self.send_error(404, "bag file does not exist")

        else:
            return self.send_error(404, "resource does not exist")

        if '/' in path:
            parts = path.split('/', 1)
            vers = parts[0]
            path = ''
            if len(parts) > 1:
                path = parts[1]
        else:
            vers = path
            path = ''

        if vers and not path:
            try:
                out = self.arch.list_for_version(aid, vers)
                if out:
                    out = json.dumps(out) + '\n'
            except Exception, ex:
                return self.send_error(500, "Internal error")

            if out:
                self.set_response(200, "All bags for ID/vers")
                self.add_header('Content-Type', 'application/json')
                self.end_headers()
                return [out]
            else:
                return self.send_error(404, "resource does not exist")

        elif vers and path == "head":
            try:
                out = self.arch.head_for(aid, vers)
                if out:
                    out = json.dumps(out) + '\n'
            except Exception, ex:
                return self.send_error(500, "Internal error")

            if out:
                self.set_response(200, "Head bags for ID/vers")
                self.add_header('Content-Type', 'application/json')
                self.end_headers()
                return [out]
            else:
                return self.send_error(404, "resource does not exist")

        else:
            return self.send_error(404, "resource does not exist")
            
    def iter_file(self, loc):
        # this is the backup, inefficient way to send a file
        with open(loc, 'rb') as fd:
            buf = fd.read(5000000)
            while buf:
                yield buf
                buf = fd.read(5000000)
        
            
            
application = SimDistrib(archdir)
