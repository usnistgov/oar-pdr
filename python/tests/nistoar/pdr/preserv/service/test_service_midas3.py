import os, pdb, sys, logging, threading, time, yaml
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.bagger import midas3 as midas
from nistoar.pdr.preserv.service import service as serv
from nistoar.pdr.preserv.service import status
from nistoar.pdr.preserv.service.siphandler import SIPHandler, MIDAS3SIPHandler
from nistoar.pdr.exceptions import PDRException, StateException
from nistoar.pdr import config

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_pressvc.log"))
    loghdlr.setLevel(logging.INFO)
    rootlog.addHandler(loghdlr)
    config._log_handler = loghdlr
    config.global_logdir = tmpdir()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestM3MultiprocessPreservationService(test.TestCase):

    testsip = os.path.join(datadir, "metadatabag")
    revdir = os.path.join(datadir, "midassip", "review")
    # testdata = os.path.join(datadir, "samplembag", "data")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        self.narch = self.tf.mkdir("notify")
        self.troot = self.tf.mkdir("midas3")
        self.dataroot = os.path.join(self.troot, "data")
        os.mkdir(self.dataroot)
        self.workdir = os.path.join(self.troot, "working")
        os.mkdir(self.workdir)
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.datadir = os.path.join(self.dataroot, "1491")
        self.stagedir = os.path.join(self.workdir, "staging")
        self.storedir = os.path.join(self.workdir, "store")
        os.mkdir(self.storedir)
        self.statusdir = os.path.join(self.workdir, "status")
        os.mkdir(self.statusdir)
        self.bagparent = os.path.join(self.datadir, "_preserv")
        self.sipdir = os.path.join(self.mdbags, self.midasid)

        with open(os.path.join(datadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
            
        # set the config we'll use
        self.config = {
            "working_dir": self.workdir,
            "store_dir": self.storedir,
            "id_registry_dir": self.workdir,
            "announce_subproc": False,
            "sip_type": {
                'midas': {},
                'midas3': {
                    "common": {
                        "working_dir": self.workdir,
                        "review_dir": self.dataroot,
                        "id_minter": { "shoulder_for_edi": "edi0" },
                    },
                    "pubserv": { },
                    "preserv": {
                        "staging_dir": self.stagedir,
                        "status_manager": { "cachedir": self.statusdir },
                        'bagger': baggercfg,
                        "ingester": {
                            "data_dir":  os.path.join(self.workdir, "ingest"),
                            "submit": "none"
                        },
                        "multibag": {
                            "max_headbag_size": 2000000,
#                             "max_headbag_size": 100,
                            "max_bag_size": 200000000
                        }
                    }
                }
            }
        }

        # copy the data files first
        shutil.copytree(os.path.join(self.revdir, "1491"), self.datadir)
        # os.mkdir(self.bagparent)

        # copy input bag to writable location
        shutil.copytree(self.testsip, self.sipdir)

        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, self.datadir)
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.done()

        try:
            self.svc = serv.MultiprocPreservationService(self.config)
        except Exception as e:
            self.tearDown()
            raise

    def tearDown(self):
        self.sip = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.svc)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.storedir))

        self.assertEqual(len(self.svc.siptypes), 2)
        self.assertIn('midas', self.svc.siptypes)
        self.assertIn('midas3', self.svc.siptypes)

    def test_wait_and_see_proc(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas3')
        self.assertEquals(hndlr.state, status.FORGOTTEN)
        self.assertTrue(hndlr.isready())
        self.assertEqual(hndlr.state, status.READY)
        
        self.svc._wait_and_see_proc(999999, hndlr, 0.2)
        self.assertEquals(hndlr.state, status.FAILED)

        hndlr.set_state(status.SUCCESSFUL, "Done!")
        self.svc._wait_and_see_proc(999999, hndlr, 0.2)
        self.assertEquals(hndlr.state, status.SUCCESSFUL)

    def test_setup_child(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas3')
        self.assertEquals(hndlr.state, status.FORGOTTEN)
        self.assertTrue(hndlr.isready())
        self.assertEqual(hndlr.state, status.READY)

        try:
            self.svc._setup_child(hndlr)
            self.assertEqual(os.path.basename(config.global_logfile),
                             self.midasid+".log")
        finally:
            rootlogger = logging.getLogger()
            rootlogger.removeHandler(config._log_handler)
            setUpModule()

    def test_launch_sync(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas3')
        self.assertEqual(hndlr.state, status.FORGOTTEN)
        self.assertTrue(hndlr.isready())
        self.assertEqual(hndlr.state, status.READY)

        proc = None
        (stat, proc) = self.svc._launch_handler(hndlr, 10, True)
        self.assertIsNone(proc)
        self.assertEqual(stat['state'], status.SUCCESSFUL)

        self.assertEqual(hndlr.state, status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        



if __name__ == '__main__':
    test.main()
