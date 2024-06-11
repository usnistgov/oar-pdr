from __future__ import print_function
import json, os, cgi, sys, re, hashlib, time
from datetime import datetime
from copy import deepcopy
from collections import OrderedDict
from wsgiref.headers import Headers

from nistoar.pdr.distrib import DistribResourceNotFound

try:
    import uwsgi
except ImportError:
    print("Warning: running ingest-uwsgi in simulate mode", file=sys.stderr)
    class uwsgi_mod(object):
        def __init__(self):
            self.opt={}
    uwsgi=uwsgi_mod()

tstltsdata = {
    "tst0-0001": {
        "trial1.json": { "filepath": "trial1.json", "size": 64 },
        "trial2.json": { "filepath": "trial2.json", "size": 36 },
        "trial3/trial3a.json": { "filepath": "trial3/trial3a.json", "size": 48 },
    },
    "tst0-0002": {
        "foo.txt": { "filepath": "foo.txt", "size": 64 },
        "bar.zip": { "filepath": "bar.zip", "size": 136889 }
    }
}

class SimInventory(object):
    """
    a mock inventory database representing the state of a mock cache
    """

    def __init__(self, arch={}, volname="fred"):
        self.volname = volname
        self._inv = {}
        self._lts = arch

    def is_cached(self, aipid, filepath):
        return self._inv.get(aipid,{}).get(filepath,{}).get('cached')

    def describe_datafile(self, aipid, filepath):
        if not self._inv.get(aipid, {}).get(filepath):
            raise DistribResourceNotFound("%s/%s" % (aipid, filepath))
        return self._inv[aipid][filepath]

    def summarize_dataset(self, aipid):
        if not self._inv.get(aipid):
            raise DistribResourceNotFound(aipid)
        filemd = self._inv[aipid].values()

        sizes = [f.get('size') for f in filemd if f.get('cached')]
        return OrderedDict([
            ("aipid", aipid),
            ("ediid", "ark:/88888/" + aipid),
            ("pdrid", "ark:/88888/" + aipid),
            ("filecount", len(sizes)),
            ("totalsize", reduce(lambda t,i: t+i, sizes, 0)),
            ("files", filemd)
        ])

    def summarize_contents(self):
        return [self.summarize_dataset(aipid) for aipid in self._inv]

    def summarize_volume(self, name):
        if name != self.volname:
            raise DistribResourceNotFound(name)

        
        sizes = [f.get('size') for f in reduce(lambda fs, d: fs + d.values(),
                                               [d for d in self._inv.values()], [])
                               if f.get('cached')]
        return OrderedDict([
            ("name", self.volname),
            ("capacity", 100000000),
            ("status", 3),
            ("filecount", len(sizes)),
            ("totalsize", reduce(lambda t,i: t+i, sizes, 0))
        ])

    def volumes(self):
        return [self.summarize_volume(self.volname)]

    def request_caching(self, aipid, filepath=None, force=False):
        files = []
        if aipid not in self._lts:
            raise DistribResourceNotFound(aipid)
        if filepath:
            if filepath not in self._lts[aipid]:
                raise DistribResourceNotFound("/".join((aipid, filepath)))
            files = [ filepath ]
        else:
            files = list(self._lts[aipid].keys())

        newrec = {
            "cached": 1,
            "since":  time.time()
        }
        newrec["sdate"] = datetime.fromtimestamp(newrec['since']).isoformat()

        current = None
        waiting = []
        self._inv.setdefault(aipid, {})
        for file in files:
            name = "%s/%s" % (aipid, file)
            qitem = "%s\t%d" % (name, (force and 1) or 0)
            if not current:
                current = qitem
            else:
                waiting.append(qitem)

            if force or file not in self._inv[aipid] or not self._inv[aipid][file].get('cached'):
                rec = OrderedDict([ ("name", name) ])
                rec.update(self._lts[aipid][file])
                rec.update(newrec)
                    
                self._inv[aipid][file] = rec

        return OrderedDict([
            ("status", "running"),
            ("current", current),
            ("waiting", waiting)
        ])
                
    def get_cache_queue(self):
        return OrderedDict([
            ("status", "running"),
            ("curent", "big1-0001\t0"),
            ("waiting", ["ltl1-0002/bigfile\t1", "ltl1-0002/smallfile\t1"])
        ])

    def uncache(self, aipid, filepath=None):
        if not self._inv.get(aipid):
            return
        if filepath:
            files = [ filepath ]
        else:
            files = list(self._inv[aipid].keys())

        for file in files:
            if self._inv[aipid].get(file,{}).get('cached'):
                self._inv[aipid][file]['cached'] = 0

    
class SimCacheManagerHandler(object):

    def __init__(self, inv, wsgienv, start_resp):
        self.inv = inv
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

    def send_json(self, body, status=200, message="OK", forhead=False):
        try:
            out = json.dumps(body)
        except Exception as ex:
            return self.send_error(500, "Internal error")

        self.set_response(status, message)
        self.add_header('Content-Type', 'application/json')
        self.add_header('Content-Length', str(len(out)))
        self.end_headers()
        if forhead:
            return []
        return [out]

    def handle(self):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')[1:]
        params = cgi.parse_qs(self._env.get('QUERY_STRING', ''))

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path, params)
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")

    def do_HEAD(self, path, params=None, forhead=False):
        return self.do_GET(path, params, True)

    def do_GET(self, path, params=None, forhead=False):
        parts = path.strip('/').split('/')

        if len(parts) == 0:
            return self.json("Ready")

        try:
            if parts[0] == "volumes":
                if len(parts) == 1:
                    return self.send_json(self.inv.volumes())
                return self.send_json(self.inv.summarize_volume("/".join(parts[1:])))

            if parts[0] == "objects":
                if len(parts) == 1:
                    return self.send_json(self.inv.summarize_contents())
                if len(parts) == 2:
                    return self.send_json(self.inv.summarize_dataset(parts[1]))
                return self.send_json(self.inv.describe_datafile(parts[1], "/".join(parts[2:])))

            if parts[0] == "queue":
                if len(parts) > 1:
                    return self.send_error(403, "Forbidden")
                return self.send_json(self.inv.get_cache_queue())

        except DistribResourceNotFound:
            return self.send_error(404, "Object not found")
        except Exception as ex:
            return self.send_error(500, "Failed trigger caching: "+str(ex))

        return self.send_error(404, "Not Found")

    def do_PUT(self, path, params):
        parts = path.strip('/').split('/')

        if len(parts) == 0 or parts[0] == "volumes":
            return self.send_error(405, "Method Not Supported")

        if parts[0] != "queue" and parts[0] != "objects":
            return self.send_error(404, "Not Found")

        if parts[0] == "objects":
            if parts[-1] != ":cached":
                return self.send_error(405, "Method Not Supported")
            parts = parts[:-1]

        force = params.get('recache',[])
        if force:
            force = force[0]

        filepath = None
        if len(parts) > 2:
            filepath = "/".join(parts[2:])
        try:
            return self.send_json(self.inv.request_caching(parts[1], filepath, force))
        except DistribResourceNotFound:
            return self.send_error(404, "Object not found")
        except Exception as ex:
            return self.send_error(500, "Failed trigger caching: "+str(ex))

    def do_DELETE(self, path, params=None):
        parts = path.strip('/').split('/')

        if len(parts) == 0 or parts[0] != "objects" or parts[-1] != ":cached":
            return self.send_error(405, "Method Not Supported")

        filepath = None
        if len(parts) > 2:
            filepath = "/".join(parts[2:-1])
        try:
            self.inv.uncache(parts[1], filepath)
        except Exception as ex:
            return self.send_error(500, "Failed to uncache: "+str(ex))

        if filepath:
            return self.send_json("File(s) "+filepath+" in dataset "+parts[1]+" removed from cache")
        return self.send_json("Dataset "+parts[1]+" in dataset "+" removed from cache")
        

class SimCacheManagerApp(object):
    def __init__(self, inv):
        self.inv = SimInventory(inv)
    def __call__(self, env, start_resp):
        return SimCacheManagerHandler(self.inv, env, start_resp).handle()

application = SimCacheManagerApp(tstltsdata)


        
