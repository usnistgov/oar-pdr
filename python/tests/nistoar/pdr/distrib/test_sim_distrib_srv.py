from __future__ import absolute_import
import os, pdb, requests, logging, time
import unittest as test
from copy import deepcopy

from nistoar.testing import *
import tests.nistoar.pdr.distrib.sim_distrib_srv as dstrb

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

class TestFunc(test.TestCase):

    def test_version_of(self):
        self.assertEqual(dstrb.version_of("pdr2210.1_0.mbag0_3-0.zip"), [1, 0])
        self.assertEqual(dstrb.version_of("pdr2210.2.mbag0_3-1.zip"), [2])
        self.assertEqual(dstrb.version_of("pdr2210.3_1_3.mbag0_3-4.zip"), [3, 1, 3])
        self.assertEqual(dstrb.version_of("pdr2210.mbag0_3-0.zip"), [1])

    def test_seq_of(self):
        self.assertEqual(dstrb.seq_of("pdr2210.1_0.mbag0_3-0.zip"), 0)
        self.assertEqual(dstrb.seq_of("pdr2210.2.mbag0_3-1.zip"), 1)
        self.assertEqual(dstrb.seq_of("pdr2210.3_1_3.mbag0_3-4.zip"), 4)
        self.assertEqual(dstrb.seq_of("pdr2210.mbag0_3-0.zip"), 0)
        self.assertEqual(dstrb.seq_of("pdr1010.mbag0_3-1.zip"), 1)
        self.assertEqual(dstrb.seq_of("pdr1010.mbag0_3-2.zip"), 2)

class TestArchive(test.TestCase):

    def setUp(self):
        self.dir = datadir
        self.arch = dstrb.SimArchive(self.dir)

    def test_ctor(self):
        self.assertIn("pdr1010", self.arch._aips)
        self.assertIn("pdr2210", self.arch._aips)
        self.assertIn("1491", self.arch._aips)
        self.assertEqual(len(self.arch._aips), 3)
                
        self.assertIn("1", self.arch._aips['pdr1010'])
        self.assertEqual(len(self.arch._aips['pdr1010']), 1)

        self.assertIn("1.0", self.arch._aips['pdr2210'])
        self.assertIn("2", self.arch._aips['pdr2210'])
        self.assertIn("3.1.3", self.arch._aips['pdr2210'])
        self.assertEqual(len(self.arch._aips['pdr2210']), 3)
        self.assertIn("1.0", self.arch._aips['1491'])
        self.assertEqual(len(self.arch._aips['1491']), 1)

        self.assertIn("pdr1010.mbag0_3-1.zip", self.arch._aips['pdr1010']['1'])
        self.assertIn("pdr1010.mbag0_3-2.zip", self.arch._aips['pdr1010']['1'])
        self.assertEqual(len(self.arch._aips['pdr1010']['1']), 2)

        self.assertIn("pdr2210.1_0.mbag0_3-0.zip",
                      self.arch._aips['pdr2210']['1.0'])
        self.assertEqual(len(self.arch._aips['pdr2210']['1.0']), 1)
        self.assertIn("pdr2210.2.mbag0_3-1.zip",
                      self.arch._aips['pdr2210']['2'])
        self.assertEqual(len(self.arch._aips['pdr2210']['1.0']), 1)
        self.assertIn("pdr2210.3_1_3.mbag0_3-4.zip",
                      self.arch._aips['pdr2210']['3.1.3'])
        self.assertEqual(len(self.arch._aips['pdr2210']['1.0']), 1)

        self.assertIn("1491.1_0.mbag0_4-0.zip",
                      self.arch._aips['1491']['1.0'])
        self.assertEqual(len(self.arch._aips['1491']['1.0']), 1)
        

    def test_aipids(self):
        self.assertEqual(self.arch.aipids, ['1491', 'pdr1010', 'pdr2210'])

    def test_versions_for(self):
        self.assertEqual(self.arch.versions_for('pdr1010'), ['1'])
        vers = self.arch.versions_for('pdr2210')
        self.assertIn('1.0', vers)
        self.assertIn('2', vers)
        self.assertIn('3.1.3', vers)
        self.assertEqual(len(vers), 3)

    def test_list_bags(self):
        self.assertEqual([f['name'] for f in self.arch.list_bags('pdr1010')],
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        self.assertEqual([f['name'] for f in self.arch.list_bags('pdr2210')],
                         ["pdr2210.1_0.mbag0_3-0.zip", "pdr2210.2.mbag0_3-1.zip",
                          "pdr2210.3_1_3.mbag0_3-4.zip"])
        self.assertEqual(self.arch.list_bags('pdr1010')[0],
                         {'name': 'pdr1010.mbag0_3-1.zip', 'hashtype': 'sha256',
                          'size': 375, 'id': 'pdr1010', 'version': '1',
    'hash': '9e70295bd074a121d720e2721ab405d7003e46086912cd92f012748c8cc3d6ad' })

    def test_list_for_version(self):
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr1010', '1')],
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr1010', '2.1')], [])

        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr2210', '1.0')],
                         ["pdr2210.1_0.mbag0_3-0.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr2210', '2')],
                         ["pdr2210.2.mbag0_3-1.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr2210', '3.1.3')],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr2210', '3.1.2')], [])

    def test_list_for_latest_version(self):
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr1010', 'latest')],
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr1010')],
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr2210', 'latest')],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.list_for_version('pdr2210')],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])

    def test_head_for(self):
        self.assertEqual([f['name'] for f in self.arch.head_for('pdr1010', '1')],
                         ["pdr1010.mbag0_3-2.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.head_for('pdr2210', '1.0')],
                         ["pdr2210.1_0.mbag0_3-0.zip"])
        self.assertEqual([f['name'] for f in self.arch.head_for('pdr2210', '2')],
                         ["pdr2210.2.mbag0_3-1.zip"])
        self.assertEqual([f['name'] for f in
                          self.arch.head_for('pdr2210', '3.1.3')],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])
        self.assertEqual(self.arch.head_for('pdr2210', '3'), [])

    def test_head_for_latest(self):
        self.assertEqual([f['name'] for f in
                          self.arch.head_for('pdr1010', 'latest')],
                         ["pdr1010.mbag0_3-2.zip"])
        self.assertEqual([f['name'] for f in self.arch.head_for('pdr1010')],
                         ["pdr1010.mbag0_3-2.zip"])

class TestSimService(test.TestCase):

    def test_aipids(self):
        resp = requests.get(baseurl)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "AIP Identifiers")
        self.assertEqual(resp.json(), ["1491", "pdr1010", "pdr2210"])

    def test_list_all(self):
        resp = requests.get(baseurl+"/pdr1010")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "AIP Identifier exists")
        self.assertEqual(resp.json(), ["pdr1010"])

        resp = requests.get(baseurl+"/pdr2210")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "AIP Identifier exists")
        self.assertEqual(resp.json(), ["pdr2210"])

        resp = requests.get(baseurl+"/pdr2222")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.reason, "resource does not exist")

    def test_list_bags(self):
        resp = requests.get(baseurl+"/pdr1010/_bags")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID")
        self.assertEqual([f['name'] for f in resp.json()], 
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])
        self.assertEqual(resp.json()[0],
                         {'name': 'pdr1010.mbag0_3-1.zip', 'hashtype': 'sha256',
                          'size': 375, 'id': 'pdr1010', 'version': '1',
    'hash': '9e70295bd074a121d720e2721ab405d7003e46086912cd92f012748c8cc3d6ad' })

        resp = requests.get(baseurl+"/pdr2210/_bags")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID")
        self.assertEqual([f['name'] for f in resp.json()], 
                         ["pdr2210.1_0.mbag0_3-0.zip", "pdr2210.2.mbag0_3-1.zip",
                          "pdr2210.3_1_3.mbag0_3-4.zip"])

    def test_versions_for(self):
        resp = requests.get(baseurl+"/pdr1010/_bags/_v")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "versions for ID")
        self.assertEqual(resp.json(), ["1"])

        resp = requests.get(baseurl+"/pdr2210/_bags/_v/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "versions for ID")
        self.assertEqual(resp.json(), ["1.0", "2", "3.1.3"])

    def test_list_for_version(self):
        resp = requests.get(baseurl+"/pdr1010/_bags/_v/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()], 
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])

        resp = requests.get(baseurl+"/pdr1010/_bags/_v/2")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.reason, "resource does not exist")

        resp = requests.get(baseurl+"/pdr2210/_bags/_v/1.0")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.1_0.mbag0_3-0.zip"])
                         
        resp = requests.get(baseurl+"/pdr2210/_bags/_v/2")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.2.mbag0_3-1.zip"])

        resp = requests.get(baseurl+"/pdr2210/_bags/_v/3.1.3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])

    def test_list_for_latest_version(self):
        resp = requests.get(baseurl+"/pdr1010/_bags/_v/latest")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()], 
                         ["pdr1010.mbag0_3-1.zip", "pdr1010.mbag0_3-2.zip"])

        resp = requests.get(baseurl+"/pdr2210/_bags/_v/latest")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "All bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])

    def test_head(self):
        resp = requests.get(baseurl+"/pdr1010/_bags/_v/1/head")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Head bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr1010.mbag0_3-2.zip"])
        
        resp = requests.get(baseurl+"/pdr2210/_bags/_v/1.0/head")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Head bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.1_0.mbag0_3-0.zip"])
                         
        resp = requests.get(baseurl+"/pdr2210/_bags/_v/2/head")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Head bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.2.mbag0_3-1.zip"])

        resp = requests.get(baseurl+"/pdr2210/_bags/_v/3.1.3/head")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Head bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])

        resp = requests.get(baseurl+"/pdr1010/_bags/_v/2/head")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.reason, "resource does not exist")

    def test_head_latest(self):
        resp = requests.get(baseurl+"/pdr1010/_bags/_v/latest/head")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Head bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr1010.mbag0_3-2.zip"])
        
        resp = requests.get(baseurl+"/pdr2210/_bags/_v/latest/head")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Head bags for ID/vers")
        self.assertEqual([f['name'] for f in resp.json()],
                         ["pdr2210.3_1_3.mbag0_3-4.zip"])

    def test_download(self):
        out = os.path.join(tmpdir(), "bag.zip")
        resp = requests.get(baseurl+"/pdr1010/_bags/pdr1010.mbag0_3-2.zip",
                            stream=True)
        with open(out, "wb") as fd:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    fd.write(chunk)

        self.assertTrue(os.path.isfile(out))
        dlcs = dstrb.checksum_of(out)
        refcs = dstrb.checksum_of(os.path.join(datadir,"pdr1010.mbag0_3-2.zip"))
        self.assertEqual(refcs, dlcs)

        


if __name__ == '__main__':
    test.main()
