from __future__ import absolute_import
import os, pdb, requests, logging, time, json
import unittest as test
from copy import deepcopy

from nistoar.testing import *

testdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(os.path.dirname(testdir)),
                       "preserv", "data")

import imp
simsrvrsrc = os.path.join(testdir, "sim_midas_srv.py")
with open(simsrvrsrc, 'r') as fd:
    simsrv = imp.load_module("sim_midas_srv.py", fd, simsrvrsrc,
                             (".py", 'r', imp.PY_SOURCE))

port = 9091
baseurl = "http://localhost:{0}/".format(port)

def startService(archdir, authmeth=None):
    srvport = port
    if authmeth == 'header':
        srvport += 1
    tdir = os.path.dirname(archdir)
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3} --set-ph archive_dir={4} " 
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(simsrvrsrc), pidfile, archdir)
    os.system(cmd)

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

    startService(svcarch)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    svcarch = os.path.join(tmpdir(), "simarch")
    stopService(svcarch)
    rmtmpdir()

class TestArchive(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.archdir = self.tf.mkdir("podarchive")
        shutil.copyfile(os.path.join(datadir, "pdr2210_pod.json"),
                        os.path.join(self.archdir, "pdr2210.json"))
        self.arch = simsrv.SimArchive(self.archdir)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.arch.dir, self.archdir)
        self.assertTrue(os.path.exists(os.path.join(self.arch.dir,"pdr2210.json")))

    def test_get_pod(self):
        jstr = self.arch.get_pod("pdr2210")
        self.assertTrue(jstr.startswith("{"))
        data = json.loads(jstr)
        self.assertIn('identifier', data)
        self.assertIn('title', data)

    def test_no_get_pod(self):
        jstr = self.arch.get_pod("gurn")
        self.assertIsNone(jstr)

    def test_put_pod(self):
        data = json.loads(self.arch.get_pod("pdr2210"))
        self.assertNotEqual(data['title'], "Goober!")
        data['title'] = "Goober!"
        jstr = self.arch.put_pod("pdr2210", json.dumps(data))
        self.assertEqual(json.loads(jstr)['title'], "Goober!")
        self.assertEqual(json.loads(self.arch.get_pod("pdr2210"))['title'],
                         "Goober!")

    def test_no_put_pod(self):
        data = json.loads(self.arch.get_pod("pdr2210"))
        self.assertNotEqual(data['title'], "Goober!")
        data['title'] = "Goober!"
        self.assertIsNone(self.arch.put_pod("gurn", json.dumps(data)))
        self.assertNotEqual(json.loads(self.arch.get_pod("pdr2210"))['title'],
                            "Goober!")


class TestSimMidas(test.TestCase):

    def setUp(self):
        svcarch = os.path.join(tmpdir(),"simarch")
        shutil.copyfile(os.path.join(datadir, "pdr2210_pod.json"),
                        os.path.join(svcarch, "pdr2210.json"))

    def test_get(self):
        resp = requests.get(baseurl+"pdr2210")
        data = resp.json()
        self.assertEqual(data['identifier'], "ark:/88434/pdr2210")

    def test_get_ark(self):
        resp = requests.get(baseurl+"ark:/88888/pdr2210")
        data = resp.json()
        self.assertEqual(data['identifier'], "ark:/88434/pdr2210")

    def test_get_noexist(self):
        resp = requests.get(baseurl+"goober")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.text, '')

    def test_put(self):
        resp = requests.get(baseurl+"pdr2210")
        data = resp.json()
        self.assertEqual(data['identifier'], "ark:/88434/pdr2210")
        self.assertNotEqual(data['title'], "Goober!")

        data['title'] = "Goober!"
        resp = requests.put(baseurl+"pdr2210", json=data)
        newdata = resp.json()
        self.assertEqual(newdata['identifier'], "ark:/88434/pdr2210")
        self.assertEqual(newdata['title'], "Goober!")

        resp = requests.get(baseurl+"pdr2210")
        data = resp.json()
        self.assertEqual(data['identifier'], "ark:/88434/pdr2210")
        self.assertEqual(data['title'], "Goober!")

    def test_put_noexist(self):
        resp = requests.get(baseurl+"pdr2210")
        data = resp.json()
        data['title'] = "Goober!"
        resp = requests.put(baseurl+"goob", json=data)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.text, '')

if __name__ == '__main__':
    test.main()

        
    
