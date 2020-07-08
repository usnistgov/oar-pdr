from __future__ import absolute_import
import os, pdb, requests, logging, time, json
from collections import OrderedDict, Mapping
from StringIO import StringIO
import unittest as test
from copy import deepcopy

from nistoar.testing import *

testdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(os.path.dirname(testdir)),
                       "preserv", "data")

import imp
simsrvrsrc = os.path.join(testdir, "sim_cust_srv.py")
with open(simsrvrsrc, 'r') as fd:
    simsrv = imp.load_module("sim_cust_srv.py", fd, simsrvrsrc,
                             (".py", 'r', imp.PY_SOURCE))

port = 9091
baseurl = "http://localhost:{0}/draft/".format(port)

def startService(archdir, authmeth=None):
    srvport = port
    if authmeth == 'header':
        srvport += 1
    tdir = os.path.dirname(archdir)
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3} --set-ph archive_dir={4} "   \
          "--set-ph auth_key=secret"
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(simsrvrsrc), pidfile, archdir)
    os.system(cmd)
    time.sleep(0.5)

def stopService(archdir, authmeth=None):
    srvport = port
    pidfile = os.path.join(os.path.dirname(archdir),"simsrv"+str(srvport)+".pid")
    cmd = "uwsgi --stop {0}".format(pidfile)
    os.system(cmd)
    time.sleep(1)

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    tdir = tmpdir()
    svcarch = os.path.join(tdir, "simarch")
    os.mkdir(svcarch)

    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_simsrv.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    svcarch = os.path.join(tmpdir(), "simarch")
    rmtmpdir()

class TestSimCustomService(test.TestCase):

    def setUp(self):
        self.svc = simsrv.SimCustom("secret")

    def test_ctor(self):
        self.assertEqual(self.svc.data, {})
        self.assertEqual(self.svc.upds, {})
        self.assertEqual(self.svc._authkey, "secret")
        self.assertEqual(self.svc._basepath, "/draft/")

    def test_exists(self):
        self.assertTrue(not self.svc.exists("goober"))
        self.svc.data["goober"] = { }
        self.assertTrue(self.svc.exists("goober"))
        
    def test_getputdel(self):
        self.assertTrue(not self.svc.exists("goober"))
        with self.assertRaises(KeyError):
            self.svc.get("goober")
        self.svc.put("goober", { "foo": "bar" })
        self.assertTrue(self.svc.exists("goober"))
        self.assertEqual(self.svc.get("goober"), { "foo": "bar", "_editStatus": "in progress"})

        self.svc.delete("goober")
        self.assertTrue(not self.svc.exists("goober"))
        with self.assertRaises(KeyError):
            self.svc.get("goober")

    def test_update(self):
        with self.assertRaises(KeyError):
            self.svc.update("goober", { "a": "b", "_editStatus": "done" })
        
        self.svc.put("goober", { "foo": "bar" })
        self.assertTrue(self.svc.exists("goober"))
        self.assertEqual(self.svc.get("goober"), { "foo": "bar", "_editStatus": "in progress"})

        self.svc.update("goober", { "a": "b", "_editStatus": "done" })
        self.assertEqual(self.svc.get("goober"),
                         { "a": "b", "foo": "bar", "_editStatus": "done"})

    def test_set_done(self):
        with self.assertRaises(KeyError):
            self.svc.set_done("goober")

        self.svc.put("goober", { "foo": "bar" })
        self.assertTrue(self.svc.exists("goober"))
        self.assertEqual(self.svc.get("goober"), { "foo": "bar", "_editStatus": "in progress"})

        self.svc.set_done("goober")
        self.assertEqual(self.svc.get("goober"), { "foo": "bar", "_editStatus": "done"})

    def test_ids(self):
        self.assertEqual(self.svc.ids(), [])
        self.assertTrue(not self.svc.exists("goober"))
        self.assertTrue(not self.svc.exists("gurn"))

        self.svc.put("goober", { "foo": "bar" })
        self.assertEqual(self.svc.ids(), ["goober"])
        
        self.svc.put("gurn", { "bar": "foo" })
        self.assertEqual(self.svc.ids(), ["gurn", "goober"])

        self.svc.remove_all()
        self.assertTrue(not self.svc.exists("goober"))
        self.assertTrue(not self.svc.exists("gurn"))
        self.assertEqual(self.svc.ids(), [])
        

class TestCustomHandler(test.TestCase):

    def setUp(self):
        self.svc = simsrv.SimCustom("secret")
        self.resp = []

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def test_ready(self):
        req = {
            'PATH_INFO': '/draft/',
            'REQUEST_METHOD': 'HEAD',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])

    def test_ids(self):
        req = {
            'PATH_INFO': '/draft/',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, [])

        self.svc.put("Gurn", {"foo": "bar"})
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, ["Gurn"])


    def test_put(self):
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'PUT',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"foo": "bar"}')
        }

        body = self.svc(req, self.start)
        self.assertIn("201", self.resp[0])
        self.assertEqual(body, [])

        self.resp = []
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"foo": "bar"}')
        }
        
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, {"foo":"bar", "_editStatus":"in progress"})
        self.assertEqual(self.svc.data["goob"], {"foo": "bar"})
        self.assertEqual(self.svc.upds["goob"], {"_editStatus": "in progress"})

        self.resp = []
        req = {
            'PATH_INFO': '/draft/',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, ["goob"])
        
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'PUT',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"hank": "frank"}')
        }
        
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("201", self.resp[0])
        self.assertEqual(body, [])

        self.resp = []
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"foo": "bar"}')
        }
        
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, {"hank":"frank", "_editStatus":"in progress"})


    def test_do_GET(self):
        self.svc.put("goob", {"foo": "bar"})
        self.assertTrue(self.svc.exists("goob"))
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, {"foo":"bar", "_editStatus":"in progress"})

    def test_do_GETupdates(self):
        self.svc.put("goob", {"foo": "bar"})
        self.assertTrue(self.svc.exists("goob"))
        req = {
            'PATH_INFO': '/draft/goob',
            'QUERY_STRING': "view=updates",
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, {"_editStatus":"in progress"})

    def test_do_DELETE(self):
        self.svc.put("goob", {"foo": "bar"})
        self.assertTrue(self.svc.exists("goob"))
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'DELETE',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertFalse(self.svc.exists("goob"))
        
    def test_do_PATCH(self):
        self.svc.put("goob", {"foo": "bar"})
        self.assertTrue(self.svc.exists("goob"))
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'PATCH',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"hank": "frank", "_editStatus": "done"}')
        }
        body = self.svc(req, self.start)
        self.assertIn("201", self.resp[0])
        self.assertEqual(body, [])
        self.assertEqual(self.svc.get("goob"),
                         {"foo":"bar", "hank": "frank", "_editStatus":"done"})
        self.assertEqual(self.svc.data["goob"], {"foo": "bar"})
        self.assertEqual(self.svc.upds["goob"],
                         {"hank": "frank", "_editStatus": "done"})

        self.resp = []
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'PUT',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"hank": "frank"}')
        }
        body = self.svc(req, self.start)
        self.assertIn("201", self.resp[0])

        self.resp = []
        req = {
            'PATH_INFO': '/draft/goob',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'wsgi.input': StringIO('{"foo": "bar"}')
        }
        
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, {"hank":"frank", "_editStatus":"in progress"})

        
class TestCustomServiceAPI(test.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.svcarch = os.path.join(tmpdir(), "simarch")
        startService(cls.svcarch)

    @classmethod
    def tearDownClass(cls):
        stopService(cls.svcarch)

    def tearDown(self):
        requests.delete(baseurl)
        self.assertEqual(requests.get(baseurl).json(), [])

    _headers = {
        "Accept": "application/json",
        "Authorization": "Bearer secret"
    }

    def test_getputdel(self):
        resp = requests.get(baseurl+"pdr2210", headers=self._headers)
        self.assertEqual(resp.status_code, 404)

        resp = requests.put(baseurl+"pdr2210", json={"foo": "bar"}, headers=self._headers)
        self.assertEqual(resp.status_code, 201)

        resp = requests.head(baseurl+"pdr2210", headers=self._headers)
        self.assertEqual(resp.status_code, 200)
        resp = requests.get(baseurl+"pdr2210", headers=self._headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"foo": "bar", "_editStatus": "in progress"})

        resp = requests.delete(baseurl+"pdr2210", headers=self._headers)
        self.assertEqual(resp.status_code, 200)
        resp = requests.head(baseurl+"pdr2210", headers=self._headers)
        self.assertEqual(resp.status_code, 404)

    def test_list_ids(self):
        resp = requests.get(baseurl)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        resp = requests.put(baseurl+"pdr2210", json={"foo": "bar"}, headers=self._headers)
        self.assertEqual(resp.status_code, 201)
        resp = requests.get(baseurl)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), ["pdr2210"])

        resp = requests.put(baseurl+"gurn", json={"foo": "bar"}, headers=self._headers)
        self.assertEqual(resp.status_code, 201)
        resp = requests.get(baseurl)
        self.assertEqual(resp.status_code, 200)
        ids = resp.json()
        self.assertEqual(len(ids), 2)
        self.assertIn("gurn", ids)
        self.assertIn("pdr2210", ids)

    def test_update(self):
        resp = requests.patch(baseurl+"pdr2210", json={"foo": "bar"}, headers=self._headers)
        self.assertEqual(resp.status_code, 404)
        
        resp = requests.put(baseurl+"pdr2210", json={"foo": "bar"}, headers=self._headers)
        self.assertEqual(resp.status_code, 201)

        resp = requests.patch(baseurl+"pdr2210",
                              json={"hank": "frank", "_editStatus": "done"},
                              headers=self._headers)
        self.assertEqual(resp.status_code, 201)
        resp = requests.get(baseurl+"pdr2210", headers=self._headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"foo": "bar", "hank": "frank", "_editStatus": "done"})

        resp = requests.get(baseurl+"pdr2210?view=updates", headers=self._headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"hank": "frank", "_editStatus": "done"})

    
    



if __name__ == '__main__':
    test.main()


        
            
        
        
