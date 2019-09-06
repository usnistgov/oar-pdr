from __future__ import absolute_import
import os, pdb, requests, logging, time, json
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.publish.mdserv import midasclient as midas
from nistoar.pdr.exceptions import ConfigurationException

testdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(os.path.dirname(testdir)),
                       "preserv", "data")
simsrvrsrc = os.path.join(testdir, "sim_midas_srv.py")

port = 9091
baseurl = "http://localhost:{0}/".format(port)

def startService(archdir, authmeth=None):
    srvport = port
    if authmeth == 'header':
        srvport += 1
    tdir = os.path.dirname(archdir)
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3} --set-ph archive_dir={4}"
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
            rootlog.removeLog(loghdlr)
        loghdlr = None
    svcarch = os.path.join(tmpdir(), "simarch")
    stopService(svcarch)
    rmtmpdir()

class TestMIDASClient(test.TestCase):

    def setUp(self):
        svcarch = os.path.join(tmpdir(),"simarch")
        shutil.copyfile(os.path.join(datadir, "pdr2210_pod.json"),
                        os.path.join(svcarch, "pdr2210.json"))
        self.cfg = {
            "service_endpoint": baseurl,
            "auth_key": "secret"
        }

    def test_ctor(self):
        client = midas.MIDASClient(self.cfg)
        self.assertEqual(client.baseurl, baseurl)
        self.assertEqual(client._authkey, "secret")

        client = midas.MIDASClient(self.cfg, "https://midas.nist.gov:8888/rest")
        self.assertEqual(client.baseurl, "https://midas.nist.gov:8888/rest/")
        self.assertEqual(client._authkey, "secret")

        del self.cfg['service_endpoint']
        with self.assertRaises(ConfigurationException):
            client = midas.MIDASClient(self.cfg)

    def test_get_pod(self):
        client = midas.MIDASClient(self.cfg)

        pod = client.get_pod("pdr2210")
        self.assertIn('identifier', pod)
        self.assertEqual(pod['identifier'], "ark:/88434/pdr2210")

    def test_get_pod_wark(self):
        client = midas.MIDASClient(self.cfg)

        pod = client.get_pod("ark:/88434/pdr2210")
        self.assertIn('identifier', pod)
        self.assertEqual(pod['identifier'], "ark:/88434/pdr2210")

    def test_get_pod_wbadid(self):
        client = midas.MIDASClient(self.cfg)

        with self.assertRaises(midas.MIDASRecordNotFound):
            client.get_pod("goober")

    def test_put_pod(self):
        ediid = "ark:/88434/pdr2210"
        client = midas.MIDASClient(self.cfg)
        pod = client.get_pod(ediid)
        self.assertNotEqual(pod['title'], "Goober!")

        pod['title'] = "Goober!"
        data = client.put_pod(pod, ediid)
        self.assertEqual(data['title'], "Goober!")
        
        pod = client.get_pod(ediid)
        self.assertEqual(pod['title'], "Goober!")
        

if __name__ == '__main__':
    test.main()

