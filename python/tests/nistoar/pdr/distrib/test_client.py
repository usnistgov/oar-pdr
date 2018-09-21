from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib
import unittest as test

from nistoar.testing import *
from nistoar.pdr.distrib import client as dcli

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
    
    wpy = "python/tests/nistoar/pdr/distrib/sim_distrib_srv.py"
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

def checksum_of(filepath):
    """
    return the checksum for the given file
    """
    bfsz = 10240000   # 10 MB buffer
    sum = hashlib.sha256()
    with open(filepath) as fd:
        while True:
            buf = fd.read(bfsz)
            if not buf: break
            sum.update(buf)
    return sum.hexdigest()

class TestRESTServiceClient(test.TestCase):

    def setUp(self):
        self.base = baseurl
        self.cli = dcli.RESTServiceClient(self.base)

    def test_get_json(self):
        data = self.cli.get_json("pdr1010/_aip/_v")
        self.assertEqual(data, ["1"])

        with self.assertRaises(dcli.DistribResourceNotFound):
            self.cli.get_json("goob/_aip/_v")

    def test_get_stream(self):
        out = os.path.join(tmpdir(), "bag.zip")

        wd = self.cli.get_stream("/_aip/pdr1010.mbag0_3-2.zip")
        with open(out, "wb") as fd:
            buf = wd.read(5000000)
            while buf:
                fd.write(buf)
                buf = wd.read(5000000)
        wd.close()

        self.assertTrue(os.path.isfile(out))
        dlcs = checksum_of(out)
        refcs = checksum_of(os.path.join(datadir,"pdr1010.mbag0_3-2.zip"))
        self.assertEqual(refcs, dlcs)

        with self.assertRaises(dcli.DistribResourceNotFound):
            wd = self.cli.get_stream("/_aip/goob.zip")
            wd.close()
                
    def test_retrieve_file(self):
        out = os.path.join(tmpdir(), "bag.zip")

        wd = self.cli.retrieve_file("/_aip/pdr1010.mbag0_3-2.zip",out)

        self.assertTrue(os.path.isfile(out))
        dlcs = checksum_of(out)
        refcs = checksum_of(os.path.join(datadir,"pdr1010.mbag0_3-2.zip"))
        self.assertEqual(refcs, dlcs)
                
        with self.assertRaises(dcli.DistribResourceNotFound):
            self.cli.retrieve_file("/_aip/goob.zip", out)
        


if __name__ == '__main__':
    test.main()
