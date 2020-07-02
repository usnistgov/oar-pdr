from __future__ import print_function
import os, sys, pdb, shutil, logging, json, time, re
import yaml
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils
from nistoar.pdr import config
from nistoar.pdr.preserv.service import status
from nistoar.pdr.publish.midas3 import service as mdsvc
from nistoar.pdr.publish.midas3 import extract_sip_config
from nistoar.pdr.preserv.bagit import builder as bldr
from nistoar.pdr.preserv.bagit import NISTBag

from nistoar.pdr.preserv.service import service as _psrvc
_psrvc.mp_sync = True

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

def tearDownModule():
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


class TestMIDAS3PublishingServicePreserve(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    wrongid = '333333333333333333333333333333331491'
    arkid = "ark:/88434/mds2-1491"
    cfgfile = os.path.join(cfgdir, "pdr-publish.yml")

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
        

    def test_ctor(self):
        self.assertTrue(os.path.isdir(self.svc.workdir))
        self.assertTrue(os.path.isdir(self.svc.mddir))
        self.assertTrue(os.path.isdir(self.svc.nrddir))
        self.assertTrue(os.path.isdir(self.svc.podqdir))
        self.assertTrue(os.path.isdir(self.svc.storedir))
        self.assertTrue(os.path.isdir(self.svc._schemadir))

        self.assertIsNotNone(self.svc.pressvc)

    def test_preserve_new(self):
        self.create_sip()
        stat = self.svc.preserve_new(self.midasid, False)

        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))

        statfile = os.path.join(self.statusdir, self.midasid+".json")
        self.assertTrue(os.path.isfile(statfile))
        with open(statfile) as fd:
            stat = json.load(fd)
        self.assertEqual(stat['user']['state'], status.SUCCESSFUL)
        
        # metadata bag was deleted
        mdbag = os.path.join(self.mdbags, self.midasid)
        self.assertFalse(os.path.exists(mdbag))

        # data was ingested
        self.assertTrue(os.path.join(mdarchive, self.midasid+".json"))

    def test_preserve_cant_update(self):
        self.create_sip()

        with self.assertRaises(mdsvc.PreservationStateError):
            stat = self.svc.preserve_update(self.midasid, False)
        

    def test_preserve_cant_renew(self):
        self.create_sip()

        # do initial submission
        stat = self.svc.preserve_new(self.midasid, False)
        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        mdbag = os.path.join(self.mdbags, self.midasid)
        self.assertFalse(os.path.exists(mdbag))

        self.create_sip()

        # prove that we can't use preserve_new() now
        with self.assertRaises(mdsvc.PreservationStateError):
            stat = self.svc.preserve_new(self.midasid, False)


    def test_preserve_update(self):
        self.create_sip()

        # do initial submission
        stat = self.svc.preserve_new(self.midasid, False)
        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        mdbag = os.path.join(self.mdbags, self.midasid)
        self.assertFalse(os.path.exists(mdbag))

        self.create_sip()

        # prove that we can't use preserve_new() now
        with self.assertRaises(mdsvc.PreservationStateError):
            stat = self.svc.preserve_new(self.midasid, False)

        # now test update
        stat = self.svc.preserve_update(self.midasid, False)

        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_1_0.mbag0_4-1.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                    self.midasid+".1_1_0.mbag0_4-1.zip.sha256")))

        statfile = os.path.join(self.statusdir, self.midasid+".json")
        self.assertTrue(os.path.isfile(statfile))
        with open(statfile) as fd:
            stat = json.load(fd)
        self.assertEqual(stat['user']['state'], status.SUCCESSFUL)
        
        # metadata bag was deleted
        mdbag = os.path.join(self.mdbags, self.midasid)
        self.assertFalse(os.path.exists(mdbag))


if __name__ == '__main__':
    test.main()

