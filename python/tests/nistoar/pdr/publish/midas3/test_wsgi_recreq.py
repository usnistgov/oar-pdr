import os, sys, pdb, shutil, logging, json, time
from StringIO import StringIO
from collections import OrderedDict
import unittest as test
import requests
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.config as config
import nistoar.pdr.utils as utils
import nistoar.pdr.publish.midas3.wsgi as wsgi
import nistoar.pdr.publish.midas3.service as mdsvc
from nistoar.pdr.publish.midas3.webrecord import RequestLogParser
from nistoar.pdr.preserv.bagit import builder as bldr

datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "preserv", "data"
)
testdir = os.path.dirname(os.path.abspath(__file__))
simsrvrsrc = os.path.join(testdir, "sim_cust_srv.py")
custport = 9091
custbaseurl = "http://localhost:{0}/draft/".format(custport)

loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
    global rootlog
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_publishing.log"))
    loghdlr.setLevel(logging.DEBUG)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)
    rootlog.setLevel(logging.DEBUG)

    custdir = os.path.join(tmpdir(),"simcust")
    os.mkdir(custdir)
    startService(custdir)

def tearDownModule():
    global rootlog
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    stopService(os.path.join(tmpdir(),"simcust"))
    rmtmpdir()

def startService(workdir):
    srvport = custport
    tdir = workdir
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3} "   \
          "--set-ph auth_key=SECRET" 
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(simsrvrsrc), pidfile)
    os.system(cmd)

def stopService(workdir):
    srvport = custport
    pidfile = os.path.join(workdir,"simsrv"+str(srvport)+".pid")
    cmd = "uwsgi --stop {0}".format(pidfile)
    os.system(cmd)
    time.sleep(1)

def altpod(srcf, destf, upddata):
    pod = utils.read_json(srcf)
    if upddata:
        pod.update(upddata)
    utils.write_json(pod, destf)

class TestMIDAS3PublishingApp(test.TestCase):

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
        self.reqlog = os.path.join(self.bagparent, "pubserver_req.log")
        self.config = {
            'working_dir':     self.bagparent,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.bagparent,
            'async_file_examine': False,
            'auth_key':        'secret',
            'record_to':       self.reqlog,
            'customization_service': {
                'service_endpoint': custbaseurl,
                'merge_convention': 'midas1',
                'updatable_properties': [ "title", "authors", "keyword", "_editStatus" ],
                'auth_key': "SECRET"
            }
        }
        self.bagdir = os.path.join(self.bagparent, self.midasid)
        self.podf = os.path.join(self.revdir,"1491","_pod.json")

        self.web = wsgi.MIDAS3PublishingApp(self.config)
        self.svc = self.web.pubsvc
        self.resp = []

    def tearDown(self):
        self.svc._drop_all_workers(300)
        requests.delete(custbaseurl, headers={'Authorization': 'Bearer SECRET'})

        if self.web._recorder:
            self.web._recorder.close_file()
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.web._recorder)

    def test_base_url(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "Ready")

        p = RequestLogParser(self.reqlog)
        recs = p.parse()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].resource, "/pod/")
        self.assertEqual(recs[0].op, "GET")

    def test_latest_base(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "No identifier given")

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "GET")
        self.assertEqual(rec.resource, "/pod/latest")
        self.assertEqual(rec.headers, ["Authorization: Bearer secret"])

    def test_latest_post(self):
        req = OrderedDict([
            ('REQUEST_METHOD', "POST"),
            ('CONTENT_TYPE', 'application/json'),
            ('PATH_INFO', '/pod/latest'),
            ('HTTP_AUTHORIZATION', 'Bearer secret')
        ])

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "POST")
        self.assertEqual(rec.resource, "/pod/latest")
        self.assertEqual(rec.headers,
                         [
                             "Content-Type: application/json",
                             "Authorization: Bearer secret"
                         ])
        data = json.loads(rec.body, object_pairs_hook=OrderedDict)
        self.assertEqual(data['identifier'], self.midasid)


    def test_badsubsvc_url(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/goober/and/the/peas'
        }
        body = self.web(req, self.start)
        self.assertIn("404 ", self.resp[0])
        self.assertEqual(body, [])

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "GET")
        self.assertEqual(rec.resource, "/pod/goober/and/the/peas")
        self.assertEqual(rec.headers, [])

    def test_badmeth_base_url(self):
        req = {
            'REQUEST_METHOD': "POST",
            'PATH_INFO': '/pod/'
        }
        body = self.web(req, self.start)
        self.assertIn("405 ", self.resp[0])
        self.assertEqual(body, [])

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "POST")
        self.assertEqual(rec.resource, "/pod/")
        self.assertEqual(rec.headers, [])

    def test_draft_base(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/draft',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "No identifier given")

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "GET")
        self.assertEqual(rec.resource, "/pod/draft")
        self.assertEqual(rec.headers, ["Authorization: Bearer secret"])

    def test_noauth(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/draft',
        }
        body = self.web(req, self.start)
        self.assertIn("401 ", self.resp[0])
        self.assertEqual(body, [])

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "GET")
        self.assertEqual(rec.resource, "/pod/draft")
        self.assertEqual(rec.headers, [])

    def test_draft_put(self):
        req = OrderedDict([
            ('REQUEST_METHOD', "PUT"),
            ('CONTENT_TYPE', 'application/json'),
            ('PATH_INFO', '/pod/draft/'+self.midasid),
            ('HTTP_AUTHORIZATION', 'Bearer secret')
        ])

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        p = RequestLogParser(self.reqlog)
        rec = p.parse_last()
        self.assertEqual(rec.op, "PUT")
        self.assertEqual(rec.resource, "/pod/draft/"+self.midasid)
        self.assertEqual(rec.headers,
                         [
                             "Content-Type: application/json",
                             "Authorization: Bearer secret"
                         ])
        data = json.loads(rec.body, object_pairs_hook=OrderedDict)
        self.assertEqual(data['identifier'], self.midasid)

        



if __name__ == '__main__':
    test.main()

    
