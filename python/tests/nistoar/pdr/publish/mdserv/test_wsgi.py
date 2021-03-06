import os, sys, pdb, shutil, logging, json
from StringIO import StringIO
import unittest as test
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.config as config
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
    global rootlog
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
        self.config = {
            'working_dir':     self.bagparent,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.bagparent,
            'async_file_examine': False,
            'update': {
                'update_auth_key': "secret",
                'updatable_properties': ['title']
            }
        }
        self.bagdir = os.path.join(self.bagparent, self.midasid)

        self.svc = wsgi.app(self.config)
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

    def test_ark_id(self):
        req = {
            'PATH_INFO': '/ark:/88434/mds4-29sd17',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertIn('mds4-29sd17', self.resp[0])
        self.assertNotIn('ark:/88434/mds4-29sd17', self.resp[0])

    def test_foreign_ark_id(self):
        req = {
            'PATH_INFO': '/ark:/88888/mds4-29sd17',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertIn('mds4-29sd17', self.resp[0])
        self.assertIn('ark:/88888/mds4-29sd17', self.resp[0])

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
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['ediid'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(len(data['components']), 7)
        
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
        self.assertEqual(redirect[0],"X-Accel-Redirect: /midasdata/review_dir/1491/trial1.json")

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
        self.assertEqual(redirect[0],"X-Accel-Redirect: /midasdata/upload_dir/1491/trial3/trial3a.json")

    def test_test_permission_read(self):
        hdlr = wsgi.Handler(None, {}, {}, self.start, "")
        body = hdlr.test_permission('mds2-2000', "read", "me")
        self.assertEqual(body, [])
        self.assertIn("200", self.resp[0])

        self.resp = []
        body = hdlr.test_permission('mds2-2000', "read", "all")
        self.assertEqual(body, [])
        self.assertIn("200", self.resp[0])

        self.resp = []
        body = hdlr.test_permission('mds2-2000', "read")
        self.assertIn("200", self.resp[0])
        self.assertNotEqual(body, [])
        self.assertEqual(len(body), 1)
        data = json.loads(body[0])
        self.assertEqual(data, ["all"])

        self.resp = []
        body = hdlr.test_permission('mds2-2000', None)
        self.assertIn("200", self.resp[0])
        self.assertNotEqual(body, [])
        self.assertEqual(len(body), 1)
        data = json.loads(body[0])
        self.assertEqual(data, {"read": "all"})

    def test_test_permission_update(self):
        hdlr = wsgi.Handler(None, {}, {}, self.start, "")
        body = hdlr.test_permission('mds2-2000', 'update', 'all')
        self.assertIn("404", self.resp[0])

        self.resp = []
        body = hdlr.test_permission('mds2-2000', 'update', None)
        self.assertIn("400", self.resp[0])

    def test_get_permission_by_path(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/_perm/read/me',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': "Bearer secret"
        }

        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])

        req['PATH_INFO'] = '/mds2-3000/_perm/read/all'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])

        req['PATH_INFO'] = '/mds2-3000/_perm/update/all'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("404", self.resp[0])

        req['PATH_INFO'] = '/mds2-3000/_perm/update/me'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        
        req['HTTP_AUTHORIZATION'] = 'Bearer token'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])

    def test_get_permission_by_query(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/_perm/read',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "user=me",
            'HTTP_AUTHORIZATION': "Bearer secret"
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), ["me"])

        del req['QUERY_STRING']
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), ["all"])

        req['PATH_INFO'] = '/mds2-3000/_perm/update'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("400", self.resp[0])
        self.assertEqual(body, [])

        req['QUERY_STRING'] = 'user=all'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), [])

        req['QUERY_STRING'] = 'action=read&user=all'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), [])

        req['QUERY_STRING'] = 'user=me&user=you'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), ["me", "you"])

        req['PATH_INFO'] = '/mds2-3000/_perm'
        req['QUERY_STRING'] = 'action=goob&action=read&action=update&user=me&user=you'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]),
                         {"update": ["me", "you"],"read": ["me", "you"]})

        req['QUERY_STRING'] = 'action=goob&user=me&user=you'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), {})

        req['QUERY_STRING'] = 'action=&user=me&user=you'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]),
                         {"update": ["me", "you"],"read": ["me", "you"]})
        
    def test_preserv_log(self):
        import re
        from nistoar.pdr.utils import checksum_of
        testpdrdir = re.sub(r'nistoar/pdr/.*$','nistoar/pdr', __file__)
        preservelog = os.path.join(testpdrdir,
                                   "preserv/data/samplembag/preserv.log")
        sum = '3370af43681254b7f44cdcdad8b7dcd40a8c90317630c288e71b2caf84cf685f'
        self.assertEqual(checksum_of(preservelog), sum)
        # self.fail("I dunno")

    def test_patch_bad_id(self):
        input = '{ "title": "Goober" }'
        winput = StringIO(input)
        req = {
            'PATH_INFO': '/asdifuiad',
            'REQUEST_METHOD': 'PATCH',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'CONTENT_LENGTH': 64,
            'wsgi.input': winput
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertIn('asdifuiad', self.resp[0])

    def test_patch_ark_id(self):
        input = '{ "title": "Goober" }'
        winput = StringIO(input)
        req = {
            'PATH_INFO': '/ark:/88434/mds4-29sd17',
            'REQUEST_METHOD': 'PATCH',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'CONTENT_LENGTH': 64,
            'wsgi.input': winput
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("404", self.resp[0])
        self.assertIn('mds4-29sd17', self.resp[0])
        self.assertNotIn('ark:/88434/mds4-29sd17', self.resp[0])

    def test_patch_unauthorized(self):
        input = '{ "title": "Goober" }'
        winput = StringIO(input)
        req = {
            'PATH_INFO': 'mds4-29sd17',
            'REQUEST_METHOD': 'PATCH',
            'HTTP_AUTHORIZATION': 'Bearer goober',
            'CONTENT_LENGTH': 64,
            'wsgi.input': winput
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("401", self.resp[0])
        self.assertNotIn('mds4-29sd17', self.resp[0])

    def test_patch_good_id(self):
        input = '{ "title": "Goober" }'
        winput = StringIO(input)
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491',
            'REQUEST_METHOD': 'PATCH',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'CONTENT_LENGTH': 21,
            'CONTENT_TYPE': 'application/json',
            'wsgi.input': winput
        }
        body = self.svc(req, self.start)

        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        self.assertGreater(len(body), 0)
        self.assertGreater(len([l for l in self.resp if "Content-Type:" in l]),0)
        data = json.loads(body[0])
        self.assertEqual(data['ediid'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(data['title'], 'Goober')
        self.assertEqual(len(data['components']), 7)
        
    def test_patch_bad_content_type(self):
        input = '{ "title": "Goober" }'
        winput = StringIO(input)
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491',
            'REQUEST_METHOD': 'PATCH',
            'HTTP_AUTHORIZATION': 'Bearer secret',
            'CONTENT_LENGTH': 21,
            'CONTENT_TYPE': 'application/junk',
            'wsgi.input': winput
        }
        body = self.svc(req, self.start)
        self.assertIn("415", self.resp[0])
        self.assertNotIn('mds4-29sd17', self.resp[0])

    def test_enableMidasClient(self):
        self.config.update({
            'update': {
                'update_to_midas': True,
                'update_auth_key': '4UPD',
                'midas_service': {
                    'service_endpoint': 'https://midas-ut.nist.gov/api',
                    'auth_key': 'unittest'
                }
            }
        });
        self.svc = wsgi.app(self.config)
        self.assertIsNotNone(self.svc._midascl)


if __name__ == '__main__':
    test.main()

        


