import os, pdb, sys, logging, threading, time, json, yaml
from copy import deepcopy
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.service import wsgi
from nistoar.pdr.preserv.service import status
from nistoar.pdr.preserv.service.siphandler import SIPHandler, MIDASSIPHandler
from nistoar.pdr.exceptions import PDRException, StateException

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_siphandler.log"))
    loghdlr.setLevel(logging.INFO)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestApp(test.TestCase):

    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def setUp(self):
        self.tf = Tempfiles()
        self.troot = self.tf.mkdir("siphandler")
        self.revdir = os.path.join(self.troot, "review")
        os.mkdir(self.revdir)
        self.workdir = os.path.join(self.troot, "working")
        os.mkdir(self.workdir)
        self.stagedir = os.path.join(self.troot, "staging")
        # os.mkdir(self.stagedir)
        self.mdserv = os.path.join(self.troot, "mdserv")
        os.mkdir(self.mdserv)
        self.store = os.path.join(self.troot, "store")
        os.mkdir(self.store)
        self.statusdir = os.path.join(self.troot, "status")
        os.mkdir(self.statusdir)

        shutil.copytree(self.sipdata, os.path.join(self.revdir, "1491"))

        with open(os.path.join(datadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
            
        self.config = {
            "working_dir": self.workdir,
            "store_dir": self.store,
            "id_registry_dir": self.workdir,
            "sip_type": {
                "midas": {
                    "common": {
                        "review_dir": self.revdir,
                        "id_minter": { "shoulder_for_edi": "edi0" },
                    },
                    "mdserv": {
                        "working_dir": self.mdserv
                    },
                    "preserv": {
                        "bagparent_dir": "_preserv",
                        "staging_dir": self.stagedir,
                        "bagger": baggercfg,
                        "status_manager": { "cachedir": self.statusdir },
                    }
                }
            }
        }

        try:
            self.svc = wsgi.app(self.config)
        except Exception, e:
            self.tearDown()
            raise

        self.resp = []

    def tearDown(self):
        self.svc = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.svc.preserv)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.store))

        self.assertEqual(self.svc.preserv.siptypes, ['midas'])

    def test_evil_id(self):
        req = {
            'PATH_INFO': '/midas/foo<a HrEf="VbScRiPt/MsgBox(11713)">',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("400", self.resp[0])
        self.assertIn('foo<a', self.resp[0])
        self.assertEqual(len(body), 0)
        

    def test_bad_id(self):
        req = {
            'PATH_INFO': '/midas/foo/bar',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("400", self.resp[0])
        self.assertIn('foo/bar', self.resp[0])
        self.resp = []
        
        req = {
            'PATH_INFO': '/midas/../foo/bar',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("400", self.resp[0])
        self.assertIn('../foo/bar', self.resp[0])
        self.resp = []
        
        req = {
            'PATH_INFO': '/midas/.foo',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("400", self.resp[0])
        self.assertIn('.foo', self.resp[0])
        self.resp = []
        
        req = {
            'PATH_INFO': '/midas/_bar',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("400", self.resp[0])
        self.assertIn('_bar', self.resp[0])
        self.resp = []
        
        req = {
            'PATH_INFO': '/midas/ark:/88888/goob/er',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("400", self.resp[0])
        self.assertIn('ark:/88888/goob/er', self.resp[0])
        self.resp = []
        

    def test_accept_arkid(self):
        req = {
            'PATH_INFO': '/midas/ark:/88888/goob',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.resp = []
        
        
    def test_ready(self):
        req = {
            'PATH_INFO': '/midas/'+self.midasid,
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], self.midasid)
        self.assertEqual(data['state'], "ready")

        req = {
            'PATH_INFO': '/midas/'+self.midasid+'/',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], self.midasid)
        self.assertEqual(data['state'], "ready")

    def test_not_found(self):
        req = {
            'PATH_INFO': '/midas/goober',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], 'goober')
        self.assertEqual(data['state'], "not found")

        req = {
            'PATH_INFO': '/midas/goober/',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], 'goober')
        self.assertEqual(data['state'], "not found")

    def test_get_types(self):
        req = {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertTrue(isinstance(data, list))
        self.assertIn('midas', data)
        self.assertEqual(len(data), 1)

    def test_no_requests(self):
        req = {
            'PATH_INFO': '/midas',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 0)

        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 0)

    def test_bad_put(self):
        req = {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'PUT'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])

        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'PUT'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])
        
        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'POST'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])

    def test_good_put(self):
        req = {
            'PATH_INFO': '/midas/'+self.midasid+'/',
            'REQUEST_METHOD': 'PUT'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("201", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], self.midasid)
        self.assertEqual(data['state'], "successful")
        self.assertEqual(len(data['bagfiles']), 1)

        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertTrue(isinstance(data, list))
        self.assertIn(self.midasid, data)
        self.assertEqual(len(data), 1)

        self.resp = []
        req = {
            'PATH_INFO': '/midas/'+self.midasid,
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], self.midasid)
        self.assertEqual(data['state'], "successful")
        self.assertEqual(len(data['bagfiles']), 1)

    def test_bad_patch(self):
        req = {
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'PATCH'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])

        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'PATCH'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])
        
        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'POST'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("403", self.resp[0])

    def test_patch_override(self):
        req = {
            'PATH_INFO': '/midas/'+self.midasid+'/',
            'REQUEST_METHOD': 'POST',
            'HTTP_X_HTTP_METHOD_OVERRIDE': 'PATCH'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("202", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], self.midasid)
        self.assertEqual(data['state'], "successful")

        self.resp = []
        req = {
            'PATH_INFO': '/midas/',
            'REQUEST_METHOD': 'GOOB',
            'HTTP_X_HTTP_METHOD_OVERRIDE': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertTrue(isinstance(data, list))
        self.assertIn(self.midasid, data)
        self.assertEqual(len(data), 1)

        self.resp = []
        req = {
            'PATH_INFO': '/midas/'+self.midasid,
            'REQUEST_METHOD': 'GET'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], self.midasid)
        self.assertEqual(data['state'], "successful")

    def test_auth(self):

        # test rejection when auth key provide but wsgi configured to take one
        req = {
            'PATH_INFO': '/midas/'+self.midasid,
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'goob=able&auth=9e73'
        }
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertEqual(body, [])

        # now configure the service to require a key
        cfg = deepcopy(self.config)
        cfg['auth_key'] = '9e73'
        self.svc = wsgi.app(cfg)

        # test successful acceptance of key
        self.resp = []
        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(data['state'], "ready")

        # test that acceptance of last key provided
        req['QUERY_STRING'] = 'goob=able&auth=gurn&auth=9e73'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(data['state'], "ready")

        req['QUERY_STRING'] = 'goob=able&auth=9e73&auth=gurn'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertEqual(body, [])

        # test single rejections
        req['QUERY_STRING'] = 'goob=able&auth=gurn'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertEqual(body, [])

        # test lack of auth key
        del req['QUERY_STRING']
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertEqual(body, [])

        # test header access key
        cfg['auth_method'] = 'header'
        self.svc = wsgi.app(cfg)

        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertIn("WWW-Authenticate: Bearer", self.resp)
        self.assertEqual(body, [])

        self.resp = []
        req['HTTP_AUTHORIZATION'] = 'Bearer 9e73'
        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertGreater(len(body), 0)
        data = json.loads(body[0])
        self.assertEqual(data['id'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(data['state'], "ready")

        self.resp = []
        req['HTTP_AUTHORIZATION'] = 'Token 9e73'
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertIn("WWW-Authenticate: Bearer", self.resp)
        self.assertEqual(body, [])

        self.resp = []
        req['HTTP_AUTHORIZATION'] = 'Bearer'
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])
        self.assertIn("WWW-Authenticate: Bearer", self.resp)
        self.assertEqual(body, [])
        
        
        
        

if __name__ == '__main__':
    test.main()

        


