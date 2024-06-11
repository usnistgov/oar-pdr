from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib
import unittest as test

from nistoar.testing import *
from nistoar.pdr.distrib import cachemgr as cm

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
    status = (os.system(cmd) == 0)
    time.sleep(0.5)
    return status

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


loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_simsrv.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)
    if not startService():
        raise RuntimeError("Failed to start the mock service")

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    stopService()
    rmtmpdir()


class TestCacheManagerClient(test.TestCase):

    def setUp(self):
        self.base = baseurl
        self.svc = cm.CacheManagerClient(self.base)

    def tearDown(self):
        requests.delete(self.base+"/objects/tst0-0001/:cached")
        requests.delete(self.base+"/objects/tst0-0002/:cached")

    def test_volumes(self):
        vols = self.svc.volumes()
        self.assertEqual(len(vols), 1)
        self.assertEqual(vols[0]['name'], 'fred')
        self.assertEqual(vols[0]['filecount'], 0)

    def test_volume_names(self):
        self.assertEqual(self.svc.volume_names(), ['fred'])

    def test_summarize_volume(self):
        vol = self.svc.summarize_volume('fred')
        self.assertEqual(vol['name'], 'fred')
        self.assertEqual(vol['filecount'], 0)

    def test_cache_cycle(self):
        objs = self.svc.summarize_contents()
        self.assertEqual(len(objs), 0)
        self.assertEqual(self.svc.dataset_ids(), [])
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0002", "foo.txt"))

        self.svc.request_caching("tst0-0001", "trial3/trial3a.json")
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0002", "foo.txt"))

        objs = self.svc.summarize_contents()
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['aipid'], 'tst0-0001')
        self.assertEqual(objs[0]['filecount'], 1)
        self.assertEqual(len(objs[0]['files']), 1)
        self.assertEqual(objs[0]['files'][0]['filepath'], "trial3/trial3a.json")
        self.assertEqual(objs[0]['files'][0]['cached'], 1)
        
        self.assertEqual(self.svc.dataset_ids(), ['tst0-0001'])
        obj = self.svc.summarize_dataset("tst0-0001")
        self.assertEqual(obj['aipid'], 'tst0-0001')
        self.assertEqual(obj['filecount'], 1)
        self.assertEqual(len(obj['files']), 1)
        self.assertEqual(obj['files'][0]['filepath'], "trial3/trial3a.json")

        filemd = self.svc.describe_datafile("tst0-0001", "trial3/trial3a.json")
        self.assertEqual(filemd['filepath'], "trial3/trial3a.json")
        self.assertEqual(filemd['size'], 48)
        self.assertEqual(filemd['cached'], 1)

        self.svc.request_caching("tst0-0001")
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0002", "foo.txt"))

        self.svc.request_caching("tst0-0002")
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.svc.is_cached("tst0-0002", "foo.txt"))

        self.svc.uncache("tst0-0001", "trial3/trial3a.json")
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.svc.is_cached("tst0-0002", "foo.txt"))

        self.svc.uncache("tst0-0001")
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(self.svc.is_cached("tst0-0002", "foo.txt"))

        self.svc.uncache("tst0-0002")
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial3/trial3a.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0001", "trial1.json"))
        self.assertTrue(not self.svc.is_cached("tst0-0002", "foo.txt"))
        
        objs = self.svc.summarize_contents()
        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0]['aipid'], 'tst0-0001')
        self.assertEqual(objs[0]['filecount'], 0)
        self.assertEqual(len(objs[0]['files']), 3)
        self.assertEqual(objs[0]['files'][0]['cached'], 0)
        
        
        
        

        


        
        
        


if __name__ == '__main__':
    test.main()
