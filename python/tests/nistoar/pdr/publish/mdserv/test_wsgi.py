import os, sys, pdb, shutil, logging, json
import unittest as test
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.publish.mdserv.config as config
import nistoar.pdr.publish.mdserv.wsgi as wsgi

datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "preserv", "data"
)
rootlog = None
def setUpModule():
    ensure_tmpdir()
    global rootlog
    rootlog = logging.getLogger()
    logfile = os.path.join(tmpdir(),"test_webserver.log")
    config.configure_log(logfile)

def tearDownModule():
    if config._log_handler:
        if rootlog:
            rootlog.removeHandler(config._log_handler)
        config._log_handler = None
    rmtmpdir()

class TestApp(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

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

        self.svc = wsgi.app(config)
        self.resp = []

    def test_bad_id(self):
        req = {
            'PATH_INFO': '/asdifuiad',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertIn('asdifuiad', self.resp[0])

    def test_head_bad_id(self):
        req = {
            'PATH_INFO': '/asdifuiad',
            'REQUEST_METHOD': 'HEAD'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertIn('asdifuiad', self.resp[0])

    def test_good_id(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertEqual(data['ediid'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(len(data['components']), 5)
        
    def test_head_good_id(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491',
            'REQUEST_METHOD': 'HEAD'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertEquals(len(body), 0)
        
    def test_bad_meth(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491',
            'REQUEST_METHOD': 'DELETE'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])

    def test_get_datafile(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial1.json',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        redirect = [r for r in self.resp if "X-Accel-Redirect:" in r]
        self.assertGreater(len(redirect), 0)
        self.assertEqual(redirect[0],"X-Accel-Redirect: /midasdata/review_dir/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial1.json")

    def test_get_datafile2(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial3/trial3a.json',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        redirect = [r for r in self.resp if "X-Accel-Redirect:" in r]
        self.assertGreater(len(redirect), 0)
        self.assertEqual(redirect[0],"X-Accel-Redirect: /midasdata/upload_dir/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial3/trial3a.json")
        

        


if __name__ == '__main__':
    test.main()

        


