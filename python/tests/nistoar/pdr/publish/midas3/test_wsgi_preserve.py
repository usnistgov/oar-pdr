from __future__ import print_function
import os, sys, pdb, shutil, logging, json, time, re
import yaml
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils
from nistoar.pdr import config
from nistoar.pdr.preserv.service import status as ps
from nistoar.pdr.publish.midas3 import service as mdsvc
from nistoar.pdr.publish.midas3 import extract_sip_config
from nistoar.pdr.preserv.bagit import builder as bldr
from nistoar.pdr.preserv.bagit import NISTBag

import nistoar.pdr.publish.midas3.wsgi as wsgi
from nistoar.pdr.preserv.service import service as _psrvc

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "preserv", "data" )
cfgdir = os.path.join(os.path.dirname(__file__), "data")
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
#    logging.basicConfig(filename=os.path.join(tmpdir(),"test_builder.log"),
#                        level=logging.INFO)
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_bagger.log"))
    loghdlr.setLevel(logging.DEBUG)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)
    rootlog.setLevel(logging.DEBUG)
    config._log_handler = loghdlr
    config.global_logdir = tmpdir()

    logging.getLogger("jsonmerge").setLevel(logging.INFO)
    startService()

    _psrvc.mp_sync = True
    mdsvc.bg_sync = True

def tearDownModule():
    _psrvc.mp_sync = False
    mdsvc.bg_sync = False

    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    stopService()
    rmtmpdir()

mdarchive = os.path.join(tmpdir(), "mdarchive")

def startService():
    tdir = tmpdir()
    if not os.path.exists(mdarchive):
        os.mkdir(mdarchive)
    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    assert os.path.isdir(basedir)
    assert 'python' in os.listdir(basedir)
    wpy = "python/tests/nistoar/pdr/describe/sim_describe_svc.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simrmm.log"), srvport,
                     os.path.join(basedir, wpy), mdarchive, pidfile)
    os.system(cmd)
    time.sleep(0.5)

def stopService(authmeth=None):
    tdir = tmpdir()
    srvport = 9092
    if authmeth == 'header':
        srvport += 1
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")

    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                                 "simrmm"+str(srvport)+".pid"))
    os.system(cmd)
    time.sleep(1)


class TestPreserveHandler(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkbase = "mds10hw916"
    arkid = "ark:/88434/mds10hw916"
    cfgfile = os.path.join(cfgdir, "pdr-publish.yml")

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def setUp(self):
        self.tf = Tempfiles()
        self.narch = self.tf.mkdir("notify")
        self.workdir = self.tf.mkdir("pubserv")
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.stagedir = os.path.join(self.workdir, "staging")
        self.storedir = os.path.join(self.workdir, "store")
        os.mkdir(self.storedir)
        self.statusdir = os.path.join(self.workdir, "status")
        os.mkdir(self.statusdir)
        self.sipdir = os.path.join(self.mdbags, self.midasid)
        self.nrddir = os.path.join(self.workdir, "nrdserv")
        self.ingestdir = os.path.join(self.workdir, "ingest")
        os.mkdir(self.ingestdir)

        self.dataroot = os.path.join(self.workdir, "data")
        shutil.copytree(self.testsip, self.dataroot)
        self.revdir = os.path.join(self.dataroot, "review")
        self.upldir = os.path.join(self.dataroot, "upload")
        self.datadir = os.path.join(self.revdir, "1491")
        self.bagparent = os.path.join(self.datadir, "_preserv")

        with open(self.cfgfile) as fd:
            defcfg = yaml.load(fd)
        defcfg.update({
            "working_dir": self.workdir,
            "store_dir":   self.storedir,
            "announce_subproc": False,
            "auth_key": "secret",
            "repo_access": {
                "headbag_cache": self.stagedir,
                "metadata_service": {
                    "service_endpoint": "http://localhost:9092/"
                }
            }
        })
        defcfg['sip_type']['midas3']['common'].update({
            "review_dir":  self.revdir,
            "upload_dir":  self.upldir
        })
        defcfg['sip_type']['midas3']['preserv'].update({
            "staging_dir":  self.stagedir,
            "logdir": self.workdir,
            "status_manager": { "cachedir": self.statusdir },
            "ingester": {
                "service_endpoint": "http://localhost:9092/",
                "data_dir": self.ingestdir
            }
        })
        defcfg['sip_type']
        defcfg['sip_type']['midas3']['mdserv'].update({
            "prepub_nerd_dir":  self.nrddir,
            "postpub_nerd_dir": os.path.join(self.stagedir, "_nerdm")
        })
        self.cfg = extract_sip_config(defcfg, "pubserv")

        self.svc = mdsvc.MIDAS3PublishingService(self.cfg)
        self.resp = []

    def tearDown(self):
        self.svc._drop_all_workers(300)
        self.tf.clean()
        for f in os.listdir(mdarchive):
            os.remove(os.path.join(mdarchive, f))

    def create_sip(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isdir(bagdir))
        
    def gethandler(self, path, env):
        return wsgi.PreserveHandler(path, self.svc, env, self.start, "secret")

    def test_not_found(self):
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': 'midas/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(req['PATH_INFO'], req)

        # not created yet
        body = self.hdlr.handle()
        self.assertIn("404 ", self.resp[0])

        stat = json.loads("\n".join(body))
        self.assertEqual(stat['state'], ps.NOT_FOUND)

    def test_ready(self):
        self.create_sip()
        req = {
            'REQUEST_METHOD': "GET",
            'PATH_INFO': 'midas/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(req['PATH_INFO'], req)

        body = self.hdlr.handle()
        self.assertIn("404 ", self.resp[0])

        stat = json.loads("\n".join(body))
        self.assertEqual(stat['state'], ps.READY)


    def test_preserve(self):
        self.create_sip()

        # confirm this is a new publication
        mdbag = os.path.join(self.mdbags, self.midasid)
        mbdir = os.path.join(mdbag, "multbag")
        self.assertFalse(os.path.exists(os.path.join(mbdir,"file-lookup.tsv")))
        nerdf = os.path.join(mdbag, "metadata", "annot.json")
        with open(nerdf) as fd:
            nerd = json.load(fd)
        self.assertNotIn('version', nerd)
        
        req = {
            'REQUEST_METHOD': "PUT",
            'PATH_INFO': 'midas/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(req['PATH_INFO'], req)

        body = self.hdlr.handle()
        self.assertIn("201 ", self.resp[0])

        stat = json.loads("\n".join(body))
        self.assertEqual(stat['state'], ps.SUCCESSFUL)

        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))

        statfile = os.path.join(self.statusdir, self.midasid+".json")
        self.assertTrue(os.path.isfile(statfile))
        with open(statfile) as fd:
            stat = json.load(fd)
        self.assertEqual(stat['user']['state'], ps.SUCCESSFUL)
        
        # metadata bag was deleted
        mdbag = os.path.join(self.mdbags, self.midasid)
        self.assertFalse(os.path.exists(mdbag))

        # data was ingested
        self.assertTrue(os.path.isfile(os.path.join(mdarchive, self.arkbase+".json")))

        # TEST republishing
        self.create_sip()

        # confirm that new metadata bag was constructed from the previous published
        # head bag.
        mbdir = os.path.join(mdbag, "multibag")
        self.assertTrue(os.path.exists(os.path.join(mbdir,"file-lookup.tsv")))
        with open(nerdf) as fd:
            nerd = json.load(fd)
        self.assertEquals(nerd['version'], "1.0.0+ (in edit)")

        # confirm that we fail if we try to publish it as if it's the first time
        self.resp = []
        req = {
            'REQUEST_METHOD': "PUT",
            'PATH_INFO': 'midas/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(req['PATH_INFO'], req)

        body = self.hdlr.handle()
        self.assertIn("409 ", self.resp[0])
        stat = json.loads("\n".join(body))
        self.assertEqual(stat['state'], ps.CONFLICT)

        # now really publish it as an update
        self.resp = []
        req = {
            'REQUEST_METHOD': "PATCH",
            'PATH_INFO': 'midas/'+self.midasid,
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler(req['PATH_INFO'], req)

        body = self.hdlr.handle()
        #
        # NOTE:  changing response to 201 (from 200)
        #
        self.assertIn("201 ", self.resp[0])

        stat = json.loads("\n".join(body))
        self.assertEqual(stat['state'], ps.SUCCESSFUL)

        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_1_0.mbag0_4-1.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                    self.midasid+".1_1_0.mbag0_4-1.zip.sha256")))

        statfile = os.path.join(self.statusdir, self.midasid+".json")
        self.assertTrue(os.path.isfile(statfile))
        with open(statfile) as fd:
            stat = json.load(fd)
        self.assertEqual(stat['user']['state'], ps.SUCCESSFUL)
        
        # metadata bag was deleted
        mdbag = os.path.join(self.mdbags, self.midasid)
        self.assertFalse(os.path.exists(mdbag))

        # data was ingested
        nerdf = os.path.join(mdarchive, self.arkbase+".json")
        self.assertTrue(os.path.isfile(nerdf))
        with open(nerdf) as fd:
            nerd = json.load(fd)
        self.assertEquals(nerd['version'], "1.1.0")
        

        

if __name__ == '__main__':
    test.main()

