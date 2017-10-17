import os, pdb, sys, json, requests, logging, time, re
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.ingest import rmm

testdir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(testdir)))))
oarmetadir = os.path.join(basedir, "oar-metadata")
testrec = os.path.join(oarmetadir, "model", "examples", "hitsc.json")
assert os.path.exists(testrec)

port = 9091
url = "http://localhost:{0}/nerdm/".format(port)
endpt = url + "?auth=critic"

def startService():
    tdir = tmpdir()
    wpy = "python/tests/nistoar/pdr/ingest/sim_ingest_srv.py"
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph auth_key=critic --pidfile {3}"
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), port,
                     os.path.join(basedir, wpy), os.path.join(tdir,"simsrv.pid"))
    os.system(cmd)

def stopService():
    tdir = tmpdir()
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,"simsrv.pid"))
    os.system(cmd)
    time.sleep(1)

loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_rmm.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)
    startService()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    stopService()
    rmtmpdir()

def getrec():
    with open(testrec) as fd:
        return json.load(fd)

class TestSubmit(test.TestCase):

    def test_service_up(self):
        resp = requests.get(endpt)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.reason, "Service is ready")

    def test_unauth(self):
        rec = getrec()
        try:
            rmm.submit_for_ingest(rec, url, 'bo')
            self.fail("Failed to raise IngestException")
        except rmm.IngestAuthzError as ex:
            self.assertEqual(ex.status, 401)
            
    def test_clienterror(self):
        rec = getrec()
        try:
            rmm.submit_for_ingest(rec, url+"/goob/?auth=critic", 'bo')
            self.fail("Failed to raise IngestException")
        except rmm.IngestClientError as ex:
            self.assertGreater(ex.status, 400)

    def test_invalid(self):
        rec = getrec()
        try:
            rmm.submit_for_ingest(rec, endpt+"&strictness=abusive", 'bo')
            self.fail("Failed to raise IngestException")
        except rmm.NotValidForIngest as ex:
            self.assertEqual(ex.status, 400)
            self.assertEqual(len(ex.errors), 4)

    def test_servererror(self):
        try:
            rec = getrec()
            stopService()
            rmm.submit_for_ingest(rec, endpt, 'bo')
        except rmm.IngestServerError as ex:
            self.assertIsNone(ex.status)
        finally:
            startService()

    def test_ok(self):
        rec = getrec()
        rmm.submit_for_ingest(rec, endpt, 'bo')


class TestIngestClient(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.tmp = self.tf.mkdir("ingesttest")
        self.datadir = os.path.join(self.tmp, "ingest")
        self.stagedir = os.path.join(self.datadir, "staging")
        self.inprogdir = os.path.join(self.datadir, "inprogress")
        self.successdir = os.path.join(self.datadir, "succeeded")
        self.faildir = os.path.join(self.tmp, "failed")
        self.cfg = {
            "data_dir": self.datadir,
            "auth_key": "critic",
            "service_endpoint": url,
            "failed_dir": self.faildir
        }
        self.cl = rmm.IngestClient(self.cfg)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.datadir)
        self.assertTrue(os.path.exists(self.stagedir))
        self.assertTrue(os.path.exists(self.successdir))
        self.assertTrue(os.path.exists(self.inprogdir))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "failed")))
        self.assertFalse(os.path.exists(os.path.join(self.datadir, "failed")))
        self.assertTrue(self.cl._endpt)
        self.assertEqual(self.cl.submit_mode, "named")

        # look for a warning about our service endpoint
        with open(os.path.join(tmpdir(),"test_rmm.log")) as fd:
            warnings = [l for l in fd if "Non-HTTPS" in l]
        self.assertGreater(len(warnings), 0)

    def test_stage(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        self.assertEqual(self.cl.staged_names(), ["bru"])

        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        names = self.cl.staged_names()
        self.assertIn("bru", names)
        self.assertIn("bro", names)
        self.assertEqual(len(names), 2)
        self.assertTrue(self.cl.is_staged("bru"))
        self.assertTrue(self.cl.is_staged("bro"))

        self.cl.stage(rec, 'bru')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        names = self.cl.staged_names()
        self.assertIn("bru", names)
        self.assertIn("bro", names)
        self.assertEqual(len(names), 2)

    def test_submit_staged(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        self.cl.submit_staged("bru")
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bru.json")))

        self.cl.submit_staged("bro")
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bru.json")))

        
    def test_submit_named(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        self.assertEqual(self.cl.submit_mode, "named")
        self.cl.submit("bru")
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bru.json")))
        
    def test_submit_none(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        self.cl.submit_mode = "none"
        self.cl.submit("bru")
        self.assertTrue(os.path.exists(os.path.join(self.stagedir,"bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir,"bru.json")))
        self.cl.submit("bro")
        
    def test_submit_staged_invalid(self):
        self.cl._endpt += "&strictness=abusive"
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        with self.assertRaises(rmm.NotValidForIngest):
            self.cl.submit_staged("bru")
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.faildir,"bru.json")))
        self.assertTrue(os.path.exists(os.path.join(self.faildir,"bru.err.txt")))

        with open(os.path.join(self.faildir,"bru.err.txt")) as fd:
            errs = fd.read()

        self.assertIn("Validation Errors:", errs)
        self.assertIn(" bother ", errs)
        
    def test_submit_staged_clerr(self):
        self.cl._endpt = re.sub(r'/nerdm/','/noobum/', self.cl._endpt)
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        with self.assertRaises(rmm.IngestClientError):
            self.cl.submit_staged("bru")
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertFalse(os.path.exists(os.path.join(self.faildir,"bru.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        
    def test_submit_staged_srverr(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        stopService()
        try:
         with self.assertRaises(rmm.IngestServerError):
            self.cl.submit_staged("bru")
         self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
         self.assertFalse(os.path.exists(os.path.join(self.faildir,"bru.json")))
         self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        finally:
         startService()


    def test_submit_all(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        results = self.cl.submit_all()
        self.assertIn("bru", results['succeeded'])
        self.assertIn("bro", results['succeeded'])
        self.assertEqual(len(results['succeeded']), 2)
        self.assertEqual(results['failed'], [])
        self.assertEqual(results['skipped'], [])
        
        self.assertFalse(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertFalse(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bru.json")))

    def test_submit_modeall(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        self.cl.submit_mode = "all"
        self.cl.submit("bru")
        self.assertFalse(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertFalse(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.successdir,"bru.json")))

    def test_submit_all_failed(self):
        rec = getrec()
        self.cl.stage(rec, 'bru')
        self.cl.stage(rec, 'bro')
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.stagedir, "bru.json")))

        self.cl._endpt += "&strictness=abusive"
        results = self.cl.submit_all()
        self.assertIn("bru", results['failed'])
        self.assertIn("bro", results['failed'])
        self.assertEqual(len(results['failed']), 2)
        self.assertEqual(results['succeeded'], [])
        self.assertEqual(results['skipped'], [])
        
        self.assertFalse(os.path.exists(os.path.join(self.stagedir, "bro.json")))
        self.assertFalse(os.path.exists(os.path.join(self.stagedir, "bru.json")))
        self.assertTrue(os.path.exists(os.path.join(self.faildir,"bro.json")))
        self.assertTrue(os.path.exists(os.path.join(self.faildir,"bru.json")))


if __name__ == '__main__':
    test.main()
