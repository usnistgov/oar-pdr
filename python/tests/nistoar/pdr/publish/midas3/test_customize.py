from __future__ import absolute_import
import os, pdb, requests, logging, time, json
from collections import OrderedDict, Mapping
from StringIO import StringIO
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.publish.midas3 import customize
from nistoar.pdr import exceptions as exc

testdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(os.path.dirname(testdir)),
                       "preserv", "data")
simsrvrsrc = os.path.join(testdir, "sim_cust_srv.py")

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
          "--set-ph auth_key=SECRET" 
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

class TestCustomClient(test.TestCase):

    def setUp(self):
        self.cfg = {
            'service_endpoint': baseurl,
            'auth_key': 'SECRET'
        }
        self.client = customize.CustomizationServiceClient(self.cfg)

    def test_ctor(self):
        self.assertEqual(self.client._authkey, 'SECRET')
        self.assertEqual(self.client.baseurl, baseurl)

    def test_getputdel(self):
        with self.assertRaises(exc.IDNotFound):
            self.client.get_draft("pdr2210")

        draft = self.client.create_draft({'ediid': 'ark:/88434/pdr2210', "foo": "bar"})
        self.assertIsNone(draft, None)

        draft = self.client.get_draft('pdr2210')
        self.assertEqual(draft, {
            'ediid': 'ark:/88434/pdr2210', "foo": "bar", "_editStatus": "in progress"
        })

        draft = self.client.get_draft('ark:/88434/pdr2210')
        self.assertEqual(draft, {
            'ediid': 'ark:/88434/pdr2210', "foo": "bar", "_editStatus": "in progress"
        })

        draft = self.client.get_draft('ark:/88434/pdr2210', True)
        self.assertEqual(draft, {
            "_editStatus": "in progress"
        })

        self.client.delete_draft('ark:/88434/pdr2210')
        with self.assertRaises(exc.IDNotFound):
            self.client.get_draft("pdr2210")

    def test_draft_exists(self):
        self.assertTrue(not self.client.draft_exists("pdr2210"))

        draft = self.client.create_draft({'ediid': 'ark:/88434/pdr2210', "foo": "bar"})
        self.assertIsNone(draft, None)

        draft = self.client.get_draft('pdr2210')
        self.assertEqual(draft, {
            'ediid': 'ark:/88434/pdr2210', "foo": "bar", "_editStatus": "in progress"
        })

        self.assertTrue(self.client.draft_exists("pdr2210"))
        
        self.client.delete_draft('ark:/88434/pdr2210')
        self.assertTrue(not self.client.draft_exists("pdr2210"))

        

if __name__ == '__main__':
    test.main()

