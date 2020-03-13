import os, sys, pdb, shutil, logging, json
from StringIO import StringIO
import unittest as test
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.config as config
import nistoar.pdr.publish.midas3.wsgi as wsgi
import nistoar.pdr.publish.midas3.service as mdsvc

datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "preserv", "data"
)
custport = 9091
custbaseurl = "http://localhost:{0}/draft/".format(custport)

rootlog = None
def setUpModule():
    ensure_tmpdir()
    global rootlog
    rootlog = logging.getLogger()
    logfile = os.path.join(tmpdir(),"test_webserver.log")
    config.configure_log(logfile)

def tearDownModule():
    global rootlog
    if config._log_handler:
        if rootlog:
            rootlog.removeHandler(config._log_handler)
        config._log_handler = None
    rmtmpdir()

class TestLatestHandler(test.TestCase):

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
        self.config = {
            'working_dir':     self.bagparent,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.bagparent,
            'async_file_examine': False,
            'customization_service': {
                'service_endpoint': custbaseurl,
                'merge_convention': 'midas1',
                'updatable_properties': [ "title", "authors", "_editStatus" ],
                'auth_key': "SECRET"
            }
        }
        self.bagdir = os.path.join(self.bagparent, self.midasid)

        self.svc = mdsvc.MIDAS3PublishingService(self.config, self.bagparent,
                                                 self.revdir, self.upldir)
        self.podf = os.path.join(self.revdir, "1491", "_pod.json")
        self.hdlr = None
        self.resp = []

    def tearDown(self):
        self.svc.wait_for_all_workers(300)
        self.tf.clean()

    def gethandler(self, path, env):
        return wsgi.LatestHandler(path, self.svc, env, self.start, "secret")

    def test_do_POST(self):
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler('', req)

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(os.path.join(self.bagparent,"mdbags",self.midasid)))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                    self.midasid+".json")))

    def test_do_unauthorized_POST(self):
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/latest',
            'HTTP_AUTHORIZATION': 'Bearer SECRET'
        }
        self.hdlr = self.gethandler('', req)

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("401", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(not os.path.isdir(os.path.join(self.bagparent,"mdbags",self.midasid)))
        self.assertTrue(not os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                        self.midasid+".json")))
    
    def test_do_GET(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/latest/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        # not created yet
        body = self.hdlr.handle()
        self.assertIn("404 ", self.resp[0])

        self.resp = []
        self.test_do_POST()
        self.hdlr = self.gethandler(self.midasid, req)
        self.resp = []
        
        body = self.hdlr.handle()
        self.assertIn("200", self.resp[0])
        pod = json.loads("\n".join(body))
        self.assertEquals(pod['identifier'], self.midasid)

        del req['HTTP_AUTHORIZATION']
        self.hdlr = self.gethandler(self.midasid, req)
        self.resp = []
        
        body = self.hdlr.handle()
        self.assertIn("401", self.resp[0])
        self.assertEquals(body, [])

    
    def test_do_GET_noid(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler('', req)

        # not created yet
        body = self.hdlr.handle()
        self.assertIn("200 ", self.resp[0])
        body = json.loads("\n".join(body))
        self.assertEqual(body, "No identifier given")

    def test_do_GET_badid(self):
        id = '<a href="">id</a>'
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/latest/'+id,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(id, req)

        body = self.hdlr.handle()
        self.assertIn("400 ", self.resp[0])
        self.assertEqual(body, [])

        self.resp = []
        id = "no id"
        req['PATH_INFO'] = '/pdr/latest/'+id
        self.hdlr = self.gethandler(id, req)

        body = self.hdlr.handle()
        self.assertIn("400 ", self.resp[0])
        self.assertEqual(body, [])

        self.resp = []
        id = "ark:/88434/pdr2210"
        req['PATH_INFO'] = '/pdr/latest/'+id
        self.hdlr = self.gethandler(id, req)

        body = self.hdlr.handle()
        self.assertIn("400 ", self.resp[0])
        self.assertEqual(body, [])

    def test_no_PUT(self):
        req = {
            'REQUEST_METHOD': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/latest/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer SECRET'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("405", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(not os.path.isdir(os.path.join(self.bagparent,"mdbags",self.midasid)))
        self.assertTrue(not os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                        self.midasid+".json")))

    def test_no_DELETE(self):
        req = {
            'REQUEST_METHOD': "DELETE",
            'PATH_INFO': '/pdr/latest/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        # not created yet
        body = self.hdlr.handle()
        self.assertIn("405 ", self.resp[0])
        self.assertEqual(body, [])

    


class TestHandler(test.TestCase):

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def gethandler(self, path, env):
        return wsgi.Handler(path, env, self.start, "secret")

    def setUp(self):
        self.resp = []
        self.hdlr = None

    def test_do_GET(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler('', req)
        body = self.hdlr.handle()
        
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "Ready")
        

    def test_do_GET_unknown(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/goober',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler('/goober', req)
        body = self.hdlr.handle()
        
        self.assertIn("404 ", self.resp[0])
        self.assertEqual(body, [])
        



if __name__ == '__main__':
    test.main()
