import os, pdb, sys, logging, threading, time, yaml
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.service import service as serv
from nistoar.pdr.preserv.service import status
from nistoar.pdr.preserv.service.siphandler import SIPHandler, MIDASSIPHandler
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
    config.global_logfile = os.path.join(tmpdir(),"test_pressvc.log")

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestThreadedPreservationService(test.TestCase):

    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.narch = self.tf.mkdir("notify")
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
            baggercfg = yaml.safe_load(fd)
            
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
            },
            "notifier": {
                "channels": [
                    {
                        "name": "arch",
                        "type": "archive",
                        "dir": self.narch
                    }
                ],
                "targets": [
                    {
                        "name": "archive",
                        "type": "archive",
                        "channel": "arch"
                    }
                ],
                "alerts": [
                    {
                        "type": "preserve.failure",
                        "targets": [ "archive" ]
                    },
                    {
                        "type": "preserve.success",
                        "targets": [ "archive" ]
                    }
                ]
            }
        }

        try:
            self.svc = serv.ThreadedPreservationService(self.config)
        except Exception, e:
            self.tearDown()
            raise

    def tearDown(self):
        self.svc = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.svc)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.store))

        self.assertEqual(self.svc.siptypes, ['midas'])
        self.assertIsNotNone(self.svc._notifier)

    def test_make_handler(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        
        self.assertTrue(hndlr.bagger)
        self.assertTrue(isinstance(hndlr, SIPHandler),
                        "hndlr is not an SIPHandler")
        self.assertTrue(isinstance(hndlr, MIDASSIPHandler),
                        "hndlr wrong type for 'midas': "+str(type(hndlr)))
        self.assertIsNotNone(hndlr.notifier)

        self.assertEqual(hndlr.cfg['working_dir'], self.workdir)
        self.assertEqual(hndlr.cfg['store_dir'], self.store)
        self.assertEqual(hndlr.cfg['id_registry_dir'], self.workdir)
        self.assertEqual(hndlr.cfg['review_dir'], self.revdir)
        self.assertEqual(hndlr.cfg['id_minter']['shoulder_for_edi'], 'edi0')
        self.assertEqual(hndlr.cfg['bagparent_dir'], '_preserv')
        self.assertEqual(hndlr.cfg['metadata_bags_dir'], self.mdserv)
        self.assertEqual(hndlr.cfg['bagger']['relative_to_indir'], True)
        self.assertEqual(hndlr.cfg['status_manager']['cachedir'], self.statusdir)

        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.stagedir))
        self.assertTrue(os.path.exists(self.mdserv))

        self.assertTrue(isinstance(hndlr.status, dict))
        self.assertEqual(hndlr.state, status.FORGOTTEN)

    def test_make_handler_badtype(self):
        with self.assertRaises(PDRException):
            hndlr = self.svc._make_handler(self.midasid, 'goob')

    def test_launch_sync(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        self.assertEqual(hndlr.state, status.FORGOTTEN)
        (stat, thrd) = self.svc._launch_handler(hndlr, 5)

        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        self.assertEqual(hndlr.state, status.SUCCESSFUL)
        
    def test_launch_async(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        self.assertEqual(hndlr.state, status.FORGOTTEN)
        self.assertTrue(hndlr.isready())
        self.assertEqual(hndlr.state, status.READY)
        self.assertFalse(os.path.exists(hndlr._status._cachefile))
        (stat, thrd) = self.svc._launch_handler(hndlr, 0)

        try:
            self.assertNotEqual(stat['state'], status.SUCCESSFUL)
        finally:
            thrd.join()
        self.assertEqual(hndlr.state, status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))

    def test_preserve(self):
        self.assertFalse(os.path.exists(os.path.join(self.narch,"archive.txt")))

        try:
            stat = self.svc.preserve(self.midasid, 'midas', 2)
            self.assertEqual(stat['state'], status.SUCCESSFUL)
        finally:
            for t in threading.enumerate():
                if t.name == self.midasid:
                   t.join()

        self.assertTrue(os.path.exists(os.path.join(self.narch,"archive.txt")))
        
    def test_preserve_noupdate(self):
        try:
            stat = self.svc.preserve(self.midasid, 'midas', 2)
            self.assertEqual(stat['state'], status.SUCCESSFUL)
        finally:
            for t in threading.enumerate():
                if t.name == self.midasid:
                   t.join()
        
        try:
            with self.assertRaises(serv.RerequestException):
                stat = self.svc.preserve(self.midasid, 'midas', 2)
        finally:
            for t in threading.enumerate():
                if t.name == self.midasid:
                   t.join()
        
    def test_preserve_inprog(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        self.assertEqual(hndlr.state, status.FORGOTTEN)
        hndlr.set_state(status.IN_PROGRESS)
        
        try:
            with self.assertRaises(serv.RerequestException):
                stat = self.svc.preserve(self.midasid, 'midas', 2)
        finally:
            for t in threading.enumerate():
                if t.name == self.midasid:
                   t.join()

    def test_status2(self):
        stat = self.svc.status("FFFFFFFFFF", "midas")
        self.assertEqual(stat['state'], status.NOT_FOUND)
        self.assertTrue(not os.path.exists(os.path.join(self.statusdir,
                                                        "FFFFFFFFFF.json")))

        os.mkdir(os.path.join(self.revdir, "FFFFFFFFFF"))
        stat = self.svc.status("FFFFFFFFFF")
        self.assertEqual(stat['state'], status.FAILED)
        self.assertTrue(not os.path.exists(os.path.join(self.statusdir,
                                                        "FFFFFFFFFF.json")))
        
    def test_status(self):
        stat = self.svc.status(self.midasid, "midas")
        self.assertEqual(stat['state'], status.READY)
        self.assertTrue(not os.path.exists(os.path.join(self.statusdir,
                                                        self.midasid+".json")))
        
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        hndlr.set_state(status.IN_PROGRESS)
        stat = self.svc.status(self.midasid, "midas")
        self.assertEqual(stat['state'], status.IN_PROGRESS)
        hndlr._status.reset()
        stat = self.svc.status(self.midasid, "midas")
        self.assertEqual(stat['state'], status.PENDING)

        with self.assertRaises(serv.RerequestException):
            self.svc.preserve(self.midasid, 'midas', 2)
        hndlr.set_state(status.READY)
        
        try:
            self.svc.preserve(self.midasid, 'midas', 2)
        finally:
            for t in threading.enumerate():
                if t.name == self.midasid:
                   t.join()
        stat = self.svc.status(self.midasid, "midas")
        self.assertEqual(stat['state'], status.SUCCESSFUL)

        # if there is no longer a cached status file, ensure that we notice
        # when there is bag in the store dir
        os.remove(os.path.join(self.statusdir, self.midasid+'.json'))
        stat = self.svc.status(self.midasid, "midas")
        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertIn('orgotten', stat['message'])

    def test_status_badtype(self):
        stat = self.svc.status(self.midasid, 'goob')
        self.assertEqual(stat['state'], status.FAILED)

    def test_requests(self):
        reqs = self.svc.requests()
        self.assertEqual(len(reqs), 0)
        
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        hndlr.set_state(status.IN_PROGRESS)
        reqs = self.svc.requests()
        self.assertIn(self.midasid, reqs)
        self.assertEqual(reqs[self.midasid], 'midas')
        self.assertEqual(len(reqs), 1)
        
        reqs = self.svc.requests('goob')
        self.assertEqual(len(reqs), 0)

        reqs = self.svc.requests('midas')
        self.assertIn(self.midasid, reqs)
        self.assertEqual(reqs[self.midasid], 'midas')
        self.assertEqual(len(reqs), 1)
        
        

class TestMultiprocPreservationService(test.TestCase):

    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

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
            baggercfg = yaml.safe_load(fd)
            
        self.config = {
            "working_dir": self.workdir,
            "store_dir": self.store,
            "logdir": self.troot,
            "id_registry_dir": self.workdir,
            "announce_subproc": False,
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
                        "status_manager": { "cachedir": self.statusdir }
                    }
                }
            }
        }

        try:
            self.svc = serv.MultiprocPreservationService(self.config)
        except Exception as e:
            self.tearDown()
            raise

    def tearDown(self):
        self.svc = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.svc)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.store))

        self.assertEqual(self.svc.siptypes, ['midas'])

    def test_launch_sync(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        self.assertEqual(hndlr.state, status.FORGOTTEN)
        self.assertTrue(hndlr.isready())
        self.assertEqual(hndlr.state, status.READY)

        proc = None
        (stat, proc) = self.svc._launch_handler(hndlr, 10, True)
        self.assertIsNone(proc)
        self.assertEqual(stat['state'], status.SUCCESSFUL)

        self.assertEqual(hndlr.state, status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        
    def test_launch_async(self):
        hndlr = self.svc._make_handler(self.midasid, 'midas')
        self.assertEqual(hndlr.state, status.FORGOTTEN)
        self.assertTrue(hndlr.isready())
        self.assertEqual(hndlr.state, status.READY)

        proc = None
        (stat, proc) = self.svc._launch_handler(hndlr, 10)
        self.assertNotEqual(stat, status.FAILED,
                            "Unexpected handler failure: "+hndlr.status['message'])
        self.assertIsNotNone(proc)
        proc.join()
        self.assertFalse(proc.is_alive())
        self.assertEqual(stat['state'], status.SUCCESSFUL,
                         "Unsuccessful state: %s: %s" % (stat['state'], stat['message']))

        self.assertEqual(hndlr.state, status.SUCCESSFUL)
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                           self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.store,
                                    self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        
    def test_subprocess_handle(self):
        try: 
            serv._subprocess_handle(self.svc.cfg, "SUBDIR/pres.log", self.midasid, "MIDAS-SIP", False, 5)
            
            hndlr = self.svc._make_handler(self.midasid, 'midas')
            self.assertEqual(hndlr.state, status.SUCCESSFUL)
            self.assertTrue(os.path.exists(os.path.join(self.store,
                                               self.midasid+".1_0_0.mbag0_4-0.zip")))
            self.assertTrue(os.path.exists(os.path.join(self.store,
                                        self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))

            plog = os.path.join(self.troot, "preservation.log")
            self.assertTrue(os.path.isfile(plog), "Missing preservation logfile: "+plog)
        finally:
            rootlogger = logging.getLogger()
            rootlogger.removeHandler(config._log_handler)
            setUpModule()


if __name__ == '__main__':
    test.main()
