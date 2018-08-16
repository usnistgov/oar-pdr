from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib, shutil
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.bagger import prepupd
from nistoar.pdr import distrib

pdrdir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
datadir = os.path.join(pdrdir, 'distrib', 'data')
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(pdrdir))))

port = 9091
baseurl = "http://localhost:{0}/".format(port)

def startService(authmeth=None):
    tdir = tmpdir()
    srvport = port
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")

    wpy = "python/tests/nistoar/pdr/distrib/sim_distrib_srv.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3}"
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(basedir, wpy), pidfile)
    os.system(cmd)

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
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_simsrv.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)
    startService()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    stopService()
    rmtmpdir()

class TestHeadBagCacher(test.TestCase):

    def setUp(self):
        self.cachedir = os.path.join(tmpdir(), "dest")
        if os.path.isdir(self.cachedir):
            shutil.rmtree(self.cachedir)
        os.mkdir(self.cachedir)

        self.distribsvc = distrib.RESTServiceClient(baseurl)
        self.cacher = prepupd.HeadBagCacher(self.distribsvc, self.cachedir)
        self.infodir = os.path.join(self.cachedir, "_info")

    def test_recall_head_info(self):
        info = {"9.0": { "id": "pdr0000", "name": "pdr0000.9_0.mbag0_4-13.zip",
                         "size": 5432, "hashtype": "md5", "hash": "xxxxx",
                         "version": "9.0" },
                "1.1": { "id": "pdr0000", "name": "pdr0000.1_1.mbag0_4-3.zip",
                         "size": 5432, "hashtype": "md5", "hash": "xxxxx",
                         "version": "1.1" }
        }
        with open(os.path.join(self.infodir, "pdr0000"), 'w') as fd:
            json.dump(info, fd, indent=2)

        self.assertEqual(self.cacher._recall_head_info("pdr0000"), info)
        self.assertEqual(self.cacher._recall_head_info("pdr0001"), {})

    def test_save_head_info(self):
        info = {"9.0": { "id": "pdr0000", "name": "pdr0000.9_0.mbag0_4-13.zip",
                         "size": 5432, "hashtype": "md5", "hash": "xxxxx",
                         "version": "9.0" },
                "1.1": { "id": "pdr0000", "name": "pdr0000.1_1.mbag0_4-3.zip",
                         "size": 5432, "hashtype": "md5", "hash": "xxxxx",
                         "version": "1.1" }
        }
        self.cacher._save_head_info("pdr0000", info)
        
        with open(os.path.join(self.infodir, "pdr0000")) as fd:
            data = json.load(fd)

        self.assertEqual(info, data)

    def test_head_info_file(self):
        self.assertEqual(self.cacher._head_info_file("pdr2222"),
                         os.path.join(self.infodir, "pdr2222"))

    def test_cache_head_info(self):
        info = {"9.0": { "id": "pdr0000", "name": "pdr0000.9_0.mbag0_4-13.zip",
                         "size": 5432, "hashtype": "md5", "hash": "xxxxx",
                         "version": "9.0" }}
        ninfo= {"1.1": { "id": "pdr0000", "name": "pdr0000.1_1.mbag0_4-3.zip",
                         "size": 5432, "hashtype": "md5", "hash": "xxxxx",
                         "version": "1.1" }}
              
        self.cacher._cache_head_info("pdr0000", "9.0", info["9.0"])
        with open(os.path.join(self.infodir, "pdr0000")) as fd:
            data = json.load(fd)
        self.assertEqual(info, data)

        self.cacher._cache_head_info("pdr0000", "1.1", ninfo["1.1"])
        with open(os.path.join(self.infodir, "pdr0000")) as fd:
            data = json.load(fd)
        info.update(ninfo)
        self.assertEqual(info, data)

    def test_confirm_bagfile(self):
        hbfile = os.path.join(datadir,"pdr1010.mbag0_3-2.zip")
        shutil.copy(hbfile, self.cachedir)
        hbfile = os.path.join(self.cachedir, "pdr1010.mbag0_3-2.zip")
        self.assertTrue(os.path.exists(hbfile))
        
        info = {"id": "pdr1010", "name": "pdr1010.mbag0_3-2.zip",
                "version": "1", "hashtype": "sha256",
      "hash": "c35f2b8ec2a4b462c77c6c60548f9a61dc1c043ddb4ba11b388312240c1c78e0"}

        self.cacher.confirm_bagfile(info)
        self.assertTrue(os.path.exists(hbfile))

        info["hash"] = "c35f"
        with self.assertRaises(prepupd.CorruptedBagError):
            self.cacher.confirm_bagfile(info, False)
        self.assertTrue(os.path.exists(hbfile))

        # check that the file gets removed when purge_on_error=True
        with self.assertRaises(prepupd.CorruptedBagError):
            self.cacher.confirm_bagfile(info, True)
        self.assertTrue(not os.path.exists(hbfile))

        hbfile = os.path.join(datadir,"pdr1010.mbag0_3-2.zip")
        shutil.copy(hbfile, self.cachedir)
        hbfile = os.path.join(self.cachedir, "pdr1010.mbag0_3-2.zip")
        self.assertTrue(os.path.exists(hbfile))
        self.cacher._cache_head_info("pdr1010", "1", info)
        with open(os.path.join(self.infodir, "pdr1010")) as fd:
            data = json.load(fd)
        self.assertIn("1", data)
        
        # now check that the info gets purged, too.
        with self.assertRaises(prepupd.CorruptedBagError):
            self.cacher.confirm_bagfile(info, True)
        self.assertTrue(not os.path.exists(hbfile))
        with open(os.path.join(self.infodir, "pdr1010")) as fd:
            data = json.load(fd)
        self.assertNotIn("1", data)

    def test_cache_headbag(self):
        hbfile = os.path.join(self.cachedir, "pdr1010.mbag0_3-2.zip")
        infofile = os.path.join(self.infodir, "pdr1010")
        self.assertTrue(not os.path.exists(hbfile))
        self.assertTrue(not os.path.exists(infofile))
        self.assertEqual(self.cacher.cache_headbag("pdr1010", "1", True), hbfile)
        self.assertTrue(os.path.exists(hbfile))
        self.assertTrue(os.path.exists(infofile))

        info = self.cacher._recall_head_info("pdr1010")
        self.assertIn("1", info)

        hbfile = os.path.join(self.cachedir, "pdr2210.2.mbag0_3-1.zip")
        infofile = os.path.join(self.infodir, "pdr2210")
        self.assertTrue(not os.path.exists(hbfile))
        self.assertTrue(not os.path.exists(infofile))
        self.assertEqual(self.cacher.cache_headbag("pdr2210", "2", True), hbfile)
        self.assertTrue(os.path.exists(hbfile))

        self.assertTrue(os.path.exists(infofile))
        info = self.cacher._recall_head_info("pdr2210")
        self.assertIn("2", info)

        hbfile = os.path.join(self.cachedir, "pdr2210.3_1_3.mbag0_3-4.zip")
        self.assertTrue(not os.path.exists(hbfile))
        self.assertTrue(os.path.exists(infofile))
        self.assertEqual(self.cacher.cache_headbag("pdr2210"), hbfile)
        self.assertTrue(os.path.exists(hbfile))

        info = self.cacher._recall_head_info("pdr2210")
        self.assertIn("3.1.3", info)
        self.assertIn("2", info)

        with open(hbfile, 'a') as fd:
            fd.write("x")

        self.assertTrue(os.path.exists(hbfile))
        with self.assertRaises(prepupd.CorruptedBagError):
            self.cacher.cache_headbag("pdr2210")
        self.assertTrue(not os.path.exists(hbfile))
        info = self.cacher._recall_head_info("pdr2210")
        self.assertNotIn("3.1.3", info)
        self.assertIn("2", info)

        self.assertIsNone(self.cacher.cache_headbag("goober"))

        
        
                    



if __name__ == '__main__':
    test.main()
