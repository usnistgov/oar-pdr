from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib
import unittest as test

from nistoar.testing import *
from nistoar.pdr.distrib import client, bagclient

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

class TestBagDistribClient(test.TestCase):

    def setUp(self):
        self.base = baseurl
        self.svc = client.RESTServiceClient(self.base)

    def test_list_versions(self):
        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        self.assertEqual(cli.list_versions(), ['1'])

        cli = bagclient.BagDistribClient("pdr2210", self.svc)
        self.assertEqual(cli.list_versions(), ['1.0', '2', '3.1.3'])

        with self.assertRaises(client.DistribResourceNotFound):
            cli = bagclient.BagDistribClient("goob", self.svc)
            cli.list_versions()

    def test_list_all(self):
        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        self.assertEqual(cli.list_all(),
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])

        cli = bagclient.BagDistribClient("pdr2210", self.svc)
        self.assertEqual(cli.list_all(),
                         ["pdr2210.1_0.mbag0_3-0.zip", "pdr2210.2.mbag0_3-1.zip",
                          "pdr2210.3_1_3.mbag0_3-4.zip"])

        with self.assertRaises(client.DistribResourceNotFound):
            cli = bagclient.BagDistribClient("goob", self.svc)
            cli.list_all()

    def test_list_for_version(self):
        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        self.assertEqual(cli.list_for_version('1'),
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        
        with self.assertRaises(client.DistribResourceNotFound):
            cli.list_for_version('2')

        self.assertEqual(cli.list_for_version('latest'),
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        self.assertEqual(cli.list_for_version(),
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])

        cli = bagclient.BagDistribClient("goob", self.svc)
        with self.assertRaises(client.DistribResourceNotFound):
            cli.list_for_version('1')

        cli = bagclient.BagDistribClient("pdr2210", self.svc)
        self.assertEqual(cli.list_for_version('3.1.3'),
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])

    def test_head_for_version(self):
        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        self.assertEqual(cli.head_for_version('1'), "pdr1010.mbag0_3-2.zip")
        
        with self.assertRaises(client.DistribResourceNotFound):
            cli.head_for_version('2')

        cli = bagclient.BagDistribClient("pdr2210", self.svc)
        self.assertEqual(cli.head_for_version('3.1.3'),
                         "pdr2210.3_1_3.mbag0_3-4.zip")
        
        cli = bagclient.BagDistribClient("goob", self.svc)
        with self.assertRaises(client.DistribResourceNotFound):
            cli.head_for_version('1')

    def test_describe_head_for_version(self):
        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        self.assertEqual(cli.describe_head_for_version('1'),
                         {'name': 'pdr1010.mbag0_3-2.zip', 'aipid': 'pdr1010', 
                          'contentLength': 375, 'sinceVersion': '1',
                          'contentType': "application/zip",
                          "serialization": "zip",
                          'checksum': {'algorithm':"sha256",
     'hash': 'c35f2b8ec2a4b462c77c6c60548f9a61dc1c043ddb4ba11b388312240c1c78e0'},
                          'multibagSequence' : 2, "multibagProfileVersion" :"0.3"
                       })
        
        with self.assertRaises(client.DistribResourceNotFound):
            cli.describe_head_for_version('2')

        cli = bagclient.BagDistribClient("goob", self.svc)
        with self.assertRaises(client.DistribResourceNotFound):
            cli.describe_head_for_version('1')

    def test_stream_bag(self):
        out = os.path.join(tmpdir(), "bag.zip")

        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        wd = cli.stream_bag("pdr1010.mbag0_3-2.zip")
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

        with self.assertRaises(client.DistribResourceNotFound):
            wd = cli.stream_bag("goob.zip")
            wd.close()
        
    def test_save_bag(self):
        cli = bagclient.BagDistribClient("pdr1010", self.svc)
        cli.save_bag("pdr1010.mbag0_3-2.zip", tmpdir())

        out = os.path.join(tmpdir(), "pdr1010.mbag0_3-2.zip")
        self.assertTrue(os.path.isfile(out))
        dlcs = checksum_of(out)
        refcs = checksum_of(os.path.join(datadir,"pdr1010.mbag0_3-2.zip"))
        self.assertEqual(refcs, dlcs)

        with self.assertRaises(client.DistribResourceNotFound):
            cli.save_bag("goob.zip", tmpdir())

        


if __name__ == '__main__':
    test.main()
