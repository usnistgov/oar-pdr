import os, sys, pdb, shutil, logging, json, time
from StringIO import StringIO
import unittest as test
import requests
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.config as config
import nistoar.pdr.utils as utils
import nistoar.pdr.publish.midas3.wsgi as wsgi
import nistoar.pdr.publish.midas3.service as mdsvc
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
    time.sleep(0.5)

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

class TestDraftHandler(test.TestCase):

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
        self.podf = os.path.join(self.revdir,"1491","_pod.json")

        self.svc = mdsvc.MIDAS3PublishingService(self.config, self.bagparent,
                                                 self.revdir, self.upldir)
        self.resp = []

    def tearDown(self):
        self.svc._drop_all_workers(300)
        requests.delete(custbaseurl, headers={'Authorization': 'Bearer SECRET'})
        self.tf.clean()

    def gethandler(self, path, env):
        return wsgi.DraftHandler(path, self.svc, env, self.start, "secret")

    def test_do_POST(self):
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/draft',
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
        
        resp = requests.head(custbaseurl+self.midasid,
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 200)

    def test_do_PUT(self):
        req = {
            'REQUEST_METHOD': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(os.path.join(self.bagparent,"mdbags",self.midasid)))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                    self.midasid+".json")))

        resp = requests.head(custbaseurl+self.midasid,
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 200)

    def test_do_PUT_wark(self):
        arkid = 'ark:/88434/mds2-1491'
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/draft/'+arkid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(arkid, req)

        with open(podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(os.path.join(self.bagparent,"mdbags","mds2-1491")))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv","mds2-1491.json")))

        resp = requests.head(custbaseurl+"mds2-1491",
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 200)

    def test_do_PUTasPOST(self):
        req = {
            'REQUEST_METHOD': "POST",
            'HTTP_X_HTTP_METHOD_OVERRIDE': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(os.path.join(self.bagparent,"mdbags",self.midasid)))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                    self.midasid+".json")))
        
        resp = requests.head(custbaseurl+self.midasid,
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 200)


    def test_do_GET(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("404", self.resp[0])
        self.assertEquals(body, [])

        self.resp = []
        self.test_do_POST()

        # we can get a draft now
        self.resp = []
        self.hdlr = self.gethandler(self.midasid, req)
        body = self.hdlr.handle()
        self.assertIn("200", self.resp[0])
        pod = json.loads("\n".join(body))
        self.assertEqual(pod["identifier"], self.midasid)
        self.assertEqual(pod["_editStatus"], "in progress")

    def test_do_GET_wark(self):
        arkid = 'ark:/88434/mds2-1491'
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/draft/'+arkid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(arkid, req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("404", self.resp[0])
        self.assertEquals(body, [])

        self.resp = []
        self.test_do_PUT_wark()

        # we can get a draft now
        self.resp = []
        self.hdlr = self.gethandler(arkid, req)
        body = self.hdlr.handle()
        self.assertIn("200", self.resp[0])
        pod = json.loads("\n".join(body))
        self.assertEqual(pod["identifier"], arkid)
        self.assertEqual(pod["_editStatus"], "in progress")

    def test_do_GET_wbadark(self):
        arkid = 'ark:/88888/mds2-1491'
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/draft/ark:/88888/1491',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler("ark:/88888/mds2-1491", req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("400", self.resp[0])
        self.assertEquals(body, [])

    def test_do_GET_wbadid(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/draft/mds2-1491',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler("ark:/88888/mds2-1491", req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("400", self.resp[0])
        self.assertEquals(body, [])

    def test_do_DELETE(self):
        req = {
            'REQUEST_METHOD': "DELETE",
            'PATH_INFO': '/pdr/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("404", self.resp[0])
        self.assertEquals(body, [])

        self.resp = []
        self.test_do_POST()

        # we can delete a draft now
        self.resp = []
        self.hdlr = self.gethandler(self.midasid, req)
        body = self.hdlr.handle()
        self.assertIn("200", self.resp[0])
        self.assertEquals(body, [])

        resp = requests.head(custbaseurl+self.midasid,
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 404)

    def test_do_DELETE_wark(self):
        arkid = 'ark:/88434/mds2-1491'
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "DELETE",
            'PATH_INFO': '/pdr/draft/'+arkid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(arkid, req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("404", self.resp[0])
        self.assertEquals(body, [])

        self.resp = []
        self.test_do_PUT_wark()

        # we can delete a draft now
        self.resp = []
        self.hdlr = self.gethandler(arkid, req)
        body = self.hdlr.handle()
        self.assertIn("200", self.resp[0])
        self.assertEquals(body, [])

        resp = requests.head(custbaseurl+"mds2-1491",
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 404)

    def test_do_DELETEasGET(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pdr/draft/'+self.midasid,
            'HTTP_X_HTTP_METHOD_OVERRIDE': "DELETE",
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(self.midasid, req)

        # draft does not exist yet
        body = self.hdlr.handle()
        self.assertIn("404", self.resp[0])
        self.assertEquals(body, [])

        self.resp = []
        self.test_do_PUTasPOST()

        # we can delete a draft now
        self.resp = []
        self.hdlr = self.gethandler(self.midasid, req)
        body = self.hdlr.handle()
        self.assertIn("200", self.resp[0])
        self.assertEquals(body, [])

        resp = requests.head(custbaseurl+self.midasid,
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 404)


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
        self.config = {
            'working_dir':     self.bagparent,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.bagparent,
            'async_file_examine': False,
            'auth_key':        'secret',
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
        self.tf.clean()

    def test_base_url(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "Ready")

    def test_bad_base_url(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/goober/'
        }
        body = self.web(req, self.start)
        self.assertIn("404 ", self.resp[0])
        self.assertEqual(body, [])

    def test_badmeth_base_url(self):
        req = {
            'REQUEST_METHOD': "POST",
            'PATH_INFO': '/pod/'
        }
        body = self.web(req, self.start)
        self.assertIn("405 ", self.resp[0])
        self.assertEqual(body, [])

    def test_badsubsvc_url(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/goober/and/the/peas'
        }
        body = self.web(req, self.start)
        self.assertIn("404 ", self.resp[0])
        self.assertEqual(body, [])

    def test_latest_base(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "No identifier given")

    def test_draft_base(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/draft',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        self.assertEqual(json.loads("\n".join(body)), "No identifier given")

    def test_noauth(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': '/pod/draft',
        }
        body = self.web(req, self.start)
        self.assertIn("401 ", self.resp[0])
        self.assertEqual(body, [])

    def test_latest_get(self):
        self.test_latest_post()
        self.resp = []
        req = {
            'REQUEST_METHOD': "GET",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/latest/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        data = json.loads("\n".join(body))
        self.assertEqual(data['identifier'], self.midasid)
        

    def test_latest_post_wrongep(self):
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/latest/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)
        
        self.assertIn("405 ", self.resp[0])
        

    def test_latest_post(self):
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        bagdir = os.path.join(self.bagparent,"mdbags",self.midasid)
        self.assertTrue(os.path.isdir(bagdir))
        # self.assertTrue(os.path.isfile(os.path.join(bagdir, "preserv.log")))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                    self.midasid+".json")))

    def test_latest_post_arkid(self):
        base = 'mds0-1491'
        arkid = 'ark:/88434/'+base
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }

        with open(podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        bagdir = os.path.join(self.bagparent,"mdbags",base)
        self.assertTrue(os.path.isdir(bagdir))
        # self.assertTrue(os.path.isfile(os.path.join(bagdir, "preserv.log")))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                    base+".json")))

    def test_latest_get_arkid(self):
        base = 'mds0-1491'
        arkid = 'ark:/88434/'+base
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        self.test_latest_post_arkid()
        
        self.resp = []
        req = {
            'REQUEST_METHOD': "GET",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/latest/'+arkid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        data = json.loads("\n".join(body))
        self.assertEqual(data['identifier'], arkid)

        self.resp = []
        req = {
            'REQUEST_METHOD': "GET",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/latest/'+base,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        data = json.loads("\n".join(body))
        self.assertEqual(data['identifier'], arkid)
        

    def test_no_double_logging(self):
        self.test_latest_post()
        self.resp = []
        self.test_latest_post()

        bagdir = os.path.join(self.bagparent,"mdbags",self.midasid)
        plog = os.path.join(bagdir, "preserv.log")
        self.assertTrue(os.path.isfile(plog))

        lastline = None
        line = None
        doubled = 0
        with open(plog) as fd:
            line = fd.readline()
            if line == lastline:
                doubled += 1
            lastline = line

        self.assertEqual(doubled, 0, "replicated log messages detected")


    def test_draft_put(self):
        req = {
            'REQUEST_METHOD': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(os.path.join(self.bagparent,"mdbags",self.midasid)))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv",
                                                    self.midasid+".json")))
        
        resp = requests.head(custbaseurl+self.midasid,
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 200)

    def test_draft_get_upd(self):
        self.test_draft_put()

        req = {
            'REQUEST_METHOD': "GET",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.resp = []
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        data = json.loads("\n".join(body))
        self.assertEqual(data['identifier'], self.midasid)
        self.assertNotIn('goobers', data['keyword'])

        resp = requests.patch(custbaseurl+self.midasid,
                              headers={'Authorization': 'Bearer SECRET'},
                              json={"keyword": data['keyword']+['goobers']})
        self.assertEqual(resp.status_code, 201)
        resp = requests.get(custbaseurl+self.midasid,
                            headers={'Authorization': 'Bearer SECRET'})
        self.assertIn('goobers', resp.json().get('keyword'))

        self.resp = []
        req = {
            'REQUEST_METHOD': "GET",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/draft/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        body = self.web(req, self.start)
        self.assertIn("200 ", self.resp[0])
        data = json.loads("\n".join(body))
        self.assertEqual(data['identifier'], self.midasid)
        self.assertEqual(data['keyword'][-1], "goobers")

    def test_draft_put_ark(self):
        arkid = 'ark:/88434/mds2-1491'
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/draft/'+arkid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }

        with open(podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(os.path.join(self.bagparent,"mdbags","mds2-1491")))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.bagparent,"nrdserv","mds2-1491.json")))
        
        resp = requests.head(custbaseurl+"mds2-1491",
                             headers={'Authorization': 'Bearer SECRET'})
        self.assertEqual(resp.status_code, 200)

    def test_draft_put_badark(self):
        arkid = 'ark:/88888/mds2-1491'
        podf = self.tf("pod.json")
        altpod(self.podf, podf, {"identifier": arkid})
        req = {
            'REQUEST_METHOD': "PUT",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pod/draft/'+arkid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }

        with open(self.podf) as fd:
            req['wsgi.input'] = fd
            body = self.web(req, self.start)

        self.assertIn("400", self.resp[0])
        self.assertEquals(body, [])

        



if __name__ == '__main__':
    test.main()

    
