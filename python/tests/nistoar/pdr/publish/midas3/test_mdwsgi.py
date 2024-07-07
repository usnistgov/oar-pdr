import os, sys, pdb, shutil, logging, json
from StringIO import StringIO
import unittest as test
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.config as config
import nistoar.pdr.publish.midas3.mdwsgi as wsgi

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
        self.wrkdir = self.tf.mkdir("publish")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.config = {
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'prepub_nerd_dir': datadir,
            'base_path': '/',
            'update': {
                'update_auth_key': "secret",
                'updatable_properties': ['title']
            },
            'download_base_url': '/midas/'
        }

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
        self.assertEqual(len(data['components']), 9)
        for cmp in data['components']:
            if 'downloadURL' in cmp:
                self.assertNotIn("/od/ds/", cmp['downloadURL'])
        
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
        self.assertIn("405", self.resp[0])

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
        mtype = [r for r in self.resp if "Content-Type:" in r]
        self.assertGreater(len(mtype), 0)
        self.assertEqual(mtype[0],"Content-Type: application/json")
        

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

    def test_get_datafile_unicode(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial\xce\xb1.json',
            'REQUEST_METHOD': 'GET'
        }
#         body = self.svc(req, self.start)
        hdlr = wsgi.Handler(self.svc, req, self.start)
        body = hdlr.send_datafile('3A1EE2F169DD3B8CE0531A570681DB5D1491',
                                  u"trial3/trial3\u03b1.json")

        self.assertGreater(len(self.resp), 0)
        self.assertIn("200", self.resp[0])
        redirect = [r for r in self.resp if "X-Accel-Redirect:" in r]
        self.assertGreater(len(redirect), 0)
        self.assertEqual(redirect[0],
                         "X-Accel-Redirect: /midasdata/review_dir/1491/trial3/trial3%CE%B1.json")
        mtype = [r for r in self.resp if "Content-Type:" in r]
        self.assertGreater(len(mtype), 0)
        self.assertEqual(mtype[0],"Content-Type: application/json")
        
    def test_test_permission_read(self):
        hdlr = wsgi.Handler(self.svc, {}, self.start)
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
        self.assertEqual(data, {"user": "all"})

        self.resp = []
        body = hdlr.test_permission('mds2-2000', None)
        self.assertIn("404", self.resp[0])
        self.assertEqual(body, [])

    def test_test_permission_update(self):
        hdlr = wsgi.Handler(self.svc, {}, self.start)
        body = hdlr.test_permission('mds2-2000', 'update', 'all')
        self.assertIn("404", self.resp[0])

        self.resp = []
        body = hdlr.test_permission('mds2-2000', 'update', None)
        self.assertIn("400", self.resp[0])

    def test_get_permission_by_old_path(self):
        # note: this path syntax is no longer allowed
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/_perm/read/me',
            'REQUEST_METHOD': 'GET',
            'HTTP_AUTHORIZATION': "Bearer secret"
        }

        body = self.svc(req, self.start)
        self.assertIn("403", self.resp[0])

        req['PATH_INFO'] = '/mds2-3000/_perm/read/all'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("403", self.resp[0])

        req['HTTP_AUTHORIZATION'] = 'Bearer token'
        self.resp = []
        body = self.svc(req, self.start)
        self.assertIn("401", self.resp[0])

    def test_get_permission_by_post(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/_perm/read',
            'REQUEST_METHOD': 'POST',
            'HTTP_AUTHORIZATION': "Bearer secret"
        }
        req['wsgi.input'] = StringIO('{"user": "me"}')

        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])

        self.resp = []
        req['PATH_INFO'] = '/3A1EE2F169DD3B8CE0531A570681DB5D1491/_perm/update'
        req['wsgi.input'] = StringIO('{"user": "all"}')
        body = self.svc(req, self.start)
        self.assertIn("404", self.resp[0])

    def test_query_permission_by_post(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/_perm',
            'REQUEST_METHOD': 'POST',
            'HTTP_AUTHORIZATION': "Bearer secret"
        }
        req['wsgi.input'] = StringIO('{"action": "read", "user": "me"}')
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), {"read": ["me"]})

        self.resp = []
        req['wsgi.input'] = StringIO('{"action": ["read", "update"], "user": "all"}')
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), {"read": ["all"], "update": []})

        self.resp = []
        req['wsgi.input'] = StringIO('{"action": ["update"], "user": "all"}')
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), {"update": []})

        self.resp = []
        req['wsgi.input'] = StringIO('{"user": "all"}')
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), {"read": ["all"], "update": []})

        self.resp = []
        req['wsgi.input'] = StringIO('{}')
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        self.assertEqual(json.loads(body[0]), {"read": ["all"]})

        
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

    def test_no_readme(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET'
        }
        body = self.svc(req, self.start)
        self.assertIn("404", self.resp[0])

        self.resp = []
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto="
        }
        body = self.svc(req, self.start)
        self.assertIn("404", self.resp[0])

        self.resp = []
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto=false"
        }
        body = self.svc(req, self.start)
        self.assertIn("404", self.resp[0])

        self.resp = []
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto=0"
        }
        body = self.svc(req, self.start)
        self.assertIn("404", self.resp[0])

    def test_auto_readme(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto=true"
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = "".join(body)
        self.assertIn("Version ", body)
        self.assertIn("Version History", body)
        self.assertIn("trial1.json", body)
        self.assertIn("###", body)

        self.resp = []
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto=false&auto=1"
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = "".join(body)
        self.assertIn("Version ", body)
        self.assertIn("Version History", body)
        self.assertIn("trial1.json", body)
        self.assertIn("###", body)

    def test_brief_auto_readme(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto=true&flags=b&flags="
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = "".join(body)
        self.assertIn("Version ", body)
        self.assertIn("Version History", body)
        self.assertNotIn("trial1.json", body)
        self.assertIn("###", body)

    def test_auto_readme_noprompts(self):
        req = {
            'PATH_INFO': '/3A1EE2F169DD3B8CE0531A570681DB5D1491/README.txt',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': "auto=true&flags=b&flags=P"
        }
        body = self.svc(req, self.start)
        self.assertIn("200", self.resp[0])
        body = "".join(body)
        self.assertIn("Version ", body)
        self.assertIn("Version History", body)
        self.assertNotIn("trial1.json", body)
        self.assertNotIn("###", body)
        


if __name__ == '__main__':
    test.main()

        
