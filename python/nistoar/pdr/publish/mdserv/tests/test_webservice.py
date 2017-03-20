import os, sys, pdb, shutil, logging, json
import unittest as test
import threading, httplib

from nistoar.tests import *
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.publish.mdserv import webservice as wsrvc

datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "preserv", "tests", "data"
)
loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_webserver.log"))
    loghdlr.setLevel(logging.INFO)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)
    rootlog.setLevel(logging.INFO)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    rmtmpdir()

SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8070

def make_server(config):
    addr = (SERVER_ADDR, SERVER_PORT)
    return wsrvc.PrePubMetadataWebServer(addr, config)

class TestWebServer(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("publish")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        config = {
            'working_dir':     self.bagparent,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.bagparent
        }
        self.bagdir = os.path.join(self.bagparent, self.midasid)
        self.server = make_server(config)
        self.server_thread = None

    def listen(self):
        self.server_thread = threading.Thread(target=self.server.handle_request)
        self.server_thread.start()

    def get(self, path):
        self.listen()
        conn = httplib.HTTPConnection("{0}:{1}".format(SERVER_ADDR,SERVER_PORT))
        conn.request("GET", path)
        return conn.getresponse()

    def junk(self):
        pass
        
    def tearDown(self):
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join()
        self.server = None
        self.tf.clean()

    def test_bad_base(self):
        resp = self.get("/goob")
        self.assertEqual(resp.status, 404)

    def test_bad_id(self):
        resp = self.get("/midas/asdifuiad")
        self.assertEqual(resp.status, 404)

    def test_good_id(self):
        resp = self.get("/midas/3A1EE2F169DD3B8CE0531A570681DB5D1491/goob.txt")
        self.assertEqual(resp.status, 200)

        data = json.loads(resp.read())
        self.assertEqual(data['ediid'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(len(data['components']), 5)
        


if __name__ == '__main__':
    test.main()

        
