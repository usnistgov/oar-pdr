from __future__ import absolute_import
import os, pdb, requests, logging, time, json
import unittest as test
from copy import deepcopy
from collections import OrderedDict

import requests

from nistoar.testing import *
import tests.nistoar.pdr.distrib.sim_cachemgr_srv as srv

testdir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
datadir = os.path.join(testdir, 'data')
basedir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(testdir)))))

port = 9091
baseurl = "http://localhost:{0}/".format(port)

def startService(authmeth=None):
    tdir = tmpdir()
    srvport = port
    if authmeth == 'header':
        srvport += 1
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    wpy = "python/tests/nistoar/pdr/distrib/sim_cachemgr_srv.py"
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3}"
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(basedir, wpy), pidfile)
    os.system(cmd)
    time.sleep(0.5)

def stopService(authmeth=None):
    tdir = tmpdir()
    srvport = port
    if authmeth == 'header':
        srvport += 1
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                                 "simsrv"+str(srvport)+".pid"))
    os.system(cmd)
    time.sleep(1)

# def setUpModule():
#     startService()

# def tearDownModule():
#     stopService()

class TestInventory(test.TestCase):

    def setUp(self):
        self.inv = srv.SimInventory(srv.tstltsdata)

    def test_empty(self):
        self.assertFalse(self.inv._inv)
        self.assertFalse(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertEqual(len(self.inv.summarize_contents()), 0)

        with self.assertRaises(srv.DistribResourceNotFound):
            self.inv.summarize_dataset("tst0-0001")
        with self.assertRaises(srv.DistribResourceNotFound):
            self.inv.describe_datafile("tst0-0001", "trial1.json")

    def test_request_caching(self):
        self.assertEqual(len(self.inv._inv), 0)
        with self.assertRaises(srv.DistribResourceNotFound):
            self.inv.request_caching("goober")

        self.assertFalse(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertFalse(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertFalse(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "bar.zip"))

        res = self.inv.request_caching("tst0-0001", "trial3/trial3a.json")
        self.assertEqual(res['status'], 'running')
        self.assertEqual(res['current'], 'tst0-0001/trial3/trial3a.json\t0')
        self.assertEqual(res['waiting'], [])

        self.assertEqual(len(self.inv._inv), 1)
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 1)
        self.assertTrue(not self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "bar.zip"))

        res = self.inv.request_caching("tst0-0001")
        self.assertEqual(res['status'], 'running')
        self.assertEqual(res['current'], 'tst0-0001/trial1.json\t0')
        self.assertEqual(res['waiting'], ['tst0-0001/trial2.json\t0', 'tst0-0001/trial3/trial3a.json\t0'])

        self.assertEqual(len(self.inv._inv), 1)
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "bar.zip"))

        self.inv.request_caching("tst0-0001")
        self.assertEqual(len(self.inv._inv), 1)
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "bar.zip"))

        self.inv.request_caching("tst0-0002", "bar.zip")
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertEqual(len(self.inv._inv["tst0-0002"]), 1)
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertFalse(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertTrue(self.inv.is_cached("tst0-0002", "bar.zip"))

        self.inv.request_caching("tst0-0002")
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertEqual(len(self.inv._inv["tst0-0002"]), 2)
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(self.inv.is_cached("tst0-0002", "foo.txt"))
        self.assertTrue(self.inv.is_cached("tst0-0002", "bar.zip"))

        fmd = self.inv.describe_datafile('tst0-0001', "trial1.json")
        self.assertEqual(fmd['name'], "tst0-0001/trial1.json")
        self.assertEqual(fmd['size'], 64)
        self.assertTrue(fmd['cached'])

        fmd = self.inv.describe_datafile('tst0-0002', "foo.txt")
        self.assertEqual(fmd['name'], "tst0-0002/foo.txt")
        self.assertEqual(fmd['size'], 64)
        self.assertTrue(fmd['cached'])

        self.inv._inv['tst0-0001']['trial1.json']['size'] = 120
        self.inv._inv['tst0-0002']['foo.txt']['size'] = 120

        self.inv.request_caching("tst0-0001", "trial1.json")
        fmd = self.inv.describe_datafile('tst0-0001', "trial1.json")
        self.assertEqual(fmd['name'], "tst0-0001/trial1.json")
        self.assertEqual(fmd['size'], 120)
        self.assertTrue(fmd['cached'])

        self.inv.request_caching("tst0-0001", "trial1.json", True)
        fmd = self.inv.describe_datafile('tst0-0001', "trial1.json")
        self.assertEqual(fmd['name'], "tst0-0001/trial1.json")
        self.assertEqual(fmd['size'], 64)
        self.assertTrue(fmd['cached'])
        
        self.inv.request_caching("tst0-0002", force=True)
        fmd = self.inv.describe_datafile('tst0-0002', "foo.txt")
        self.assertEqual(fmd['name'], "tst0-0002/foo.txt")
        self.assertEqual(fmd['size'], 64)
        self.assertTrue(fmd['cached'])

    def test_uncache(self):
        self.assertFalse(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.inv.uncache("tst0-0001", "trial2.json")
        self.assertFalse(self.inv.is_cached("tst0-0001", "trial2.json"))

        self.inv.request_caching("tst0-0001")
        self.assertEqual(len(self.inv._inv), 1)
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))

        self.inv.uncache("tst0-0001", "trial2.json")
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        
        fmd = self.inv.describe_datafile('tst0-0001', "trial2.json")
        self.assertFalse(fmd['cached'])

        self.inv.uncache("tst0-0001")
        self.assertEqual(len(self.inv._inv["tst0-0001"]), 3)
        self.assertTrue(not self.inv.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.inv.is_cached("tst0-0001", "trial2.json"))
        self.assertTrue(not self.inv.is_cached("tst0-0001", "trial3/trial3a.json"))
        files = self.inv.summarize_dataset('tst0-0001')['files']
        self.assertTrue(not any([f['cached'] for f in files]))
                         

    def test_summarize_volume(self):
        with self.assertRaises(srv.DistribResourceNotFound):
            self.inv.summarize_volume("ginger")

        vol = self.inv.summarize_volume("fred")
        self.assertEqual(vol['name'], "fred")
        self.assertEqual(vol['capacity'], 100000000)
        self.assertEqual(vol['status'], 3)
        self.assertEqual(vol['filecount'], 0)
        self.assertEqual(vol['totalsize'], 0)

        self.inv = srv.SimInventory(srv.tstltsdata, "ginger")
        with self.assertRaises(srv.DistribResourceNotFound):
            self.inv.summarize_volume("fred")
        for aipid in srv.tstltsdata:
            self.inv.request_caching(aipid)

        vol = self.inv.summarize_volume("ginger")
        self.assertEqual(vol['name'], "ginger")
        self.assertEqual(vol['capacity'], 100000000)
        self.assertEqual(vol['status'], 3)
        self.assertEqual(vol['filecount'], 5)
        self.assertEqual(vol['totalsize'], 136889+64+64+36+48)

class SimCacheManagerHandler(test.TestCase):

    def setUp(self):
        self.inv = srv.SimInventory(srv.tstltsdata)
        self.resp = []

    def create_handler(self, req):
        return srv.SimCacheManagerHandler(self.inv, req, self.start)

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def tostr(self, resplist):
        return [e.decode() for e in resplist]

    def load_json_body(self, body):
        return json.loads("\n".join(self.tostr(body)), object_pairs_hook=OrderedDict)

    def test_volumes(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/volumes/'
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)

        self.assertEqual(len(resp), 1)
        self.assertEqual(resp[0]['name'], "fred")
        self.assertEqual(resp[0]['filecount'], 0)

    def test_summarize_volume(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/volumes/fred'
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)

        self.assertEqual(resp['name'], "fred")
        self.assertEqual(resp['filecount'], 0)

        self.resp = []
        req['PATH_INFO'] = "ginger"
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("404 ", self.resp[0])

        self.resp = []
        req['PATH_INFO'] = "fred/ginger"
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("404 ", self.resp[0])

    def test_summarize_objects(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/objects/'
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)
        self.assertTrue(isinstance(resp, list))
        self.assertEqual(len(resp), 0)

        self.resp = []
        self.inv.request_caching("tst0-0001")
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)
        self.assertEqual(len(resp), 1)

    def test_describe_dataset(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/objects/tst0-0001'
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("404 ", self.resp[0])

        self.resp = []
        self.inv.request_caching("tst0-0001")
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)
        self.assertEqual(len(resp['files']), 3)
        self.assertEqual(resp['filecount'], 3)

    def test_describe_datafile(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/objects/tst0-0001/trial3/trial3a.json',
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("404 ", self.resp[0])

        self.resp = []
        self.inv.request_caching("tst0-0001")
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)
        self.assertEqual(resp['size'], 48)
        self.assertEqual(resp['filepath'], "trial3/trial3a.json")

    def test_request_caching(self):
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial1.json'))

        self.resp = []
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/queue/tst0-0001/trial3/trial3a.json',
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("403 ", self.resp[0])
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial1.json'))

        self.resp = []
        req['REQUEST_METHOD'] = "PUT"
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        resp = self.load_json_body(body)
        self.assertIn("current", resp)
        self.assertIn("waiting", resp)
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial1.json'))

        self.resp = []
        req['PATH_INFO'] = "/queue/tst0-0001"
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial1.json'))

    def test_uncache(self):
        self.inv.request_caching("tst0-0001")
        self.inv.request_caching("tst0-0002")
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial1.json'))
        self.assertTrue(self.inv.is_cached('tst0-0002', 'foo.txt'))

        req = {
            'REQUEST_METHOD': "DELETE",
            'PATH_INFO': '/objects/tst0-0001/trial3/trial3a.json',
        }
        hdlr = self.create_handler(req)
        body = hdlr.handle()
        self.assertIn("405 ", self.resp[0])
        
        self.resp = []
        req['PATH_INFO'] = '/objects/tst0-0001/trial3/trial3a.json/:cached'
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial1.json'))
        self.assertTrue(self.inv.is_cached('tst0-0002', 'foo.txt'))
        resp = self.load_json_body(body)
        self.assertTrue(isinstance(resp, unicode))
        
        self.resp = []
        req['PATH_INFO'] = '/objects/tst0-0002/foo.txt/:cached'
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(self.inv.is_cached('tst0-0001', 'trial1.json'))
        self.assertTrue(not self.inv.is_cached('tst0-0002', 'foo.txt'))
        
        self.resp = []
        req['PATH_INFO'] = '/objects/tst0-0001/:cached'
        body = hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial3/trial3a.json'))
        self.assertTrue(not self.inv.is_cached('tst0-0001', 'trial1.json'))
        self.assertTrue(not self.inv.is_cached('tst0-0002', 'foo.txt'))
        
        
        
class TestWebService(test.TestCase):

    baseurl = "http://localhost:9091"

    @classmethod
    def setUpClass(cls):
        ensure_tmpdir()
        startService()

    @classmethod
    def tearDownClass(cls):
        stopService()
        rmtmpdir()

    def tearDown(self):
        requests.delete(self.baseurl+"/objects/tst0-0001/:cached")
        requests.delete(self.baseurl+"/objects/tst0-0002/:cached")

    def test_volumes(self):
        resp = requests.get(self.baseurl+"/volumes/")
        resp = resp.json()
        
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp[0]['name'], "fred")
        self.assertEqual(resp[0]['filecount'], 0)

    def test_request_caching(self):
        resp = requests.put(self.baseurl+"/queue/tst0-0001/trial3/trial3a.json")
        self.assertEqual(resp.status_code, 200)
        resp = resp.json()        
        self.assertEqual(len(resp['waiting']), 0)

        resp = requests.get(self.baseurl+"/objects/tst0-0001/trial3/trial3a.json")
        self.assertEqual(resp.status_code, 200)
        resp = resp.json()
        self.assertEqual(resp['filepath'], 'trial3/trial3a.json')
        self.assertEqual(resp['cached'], 1)
        
        
        
    
    
        
        

        
        
        


if __name__ == '__main__':
    test.main()





            
