from __future__ import print_function
import os, sys, pdb, shutil, logging, json, time, re
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils
from nistoar.pdr.publish.midas3 import service as mdsvc
from nistoar.pdr.preserv.bagit import builder as bldr
from nistoar.pdr.preserv.bagit import NISTBag
from ejsonschema import ValidationError

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "preserv", "data" )

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

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestMIDAS3PublishingService(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    wrongid = '333333333333333333333333333333331491'
    arkid = "ark:/88434/mds2-1491"
    defcfg = {
        'store_dir': "store",
        'customization_service': {
            'auth_key': 'SECRET',
            'service_endpoint': "http:notused.net/",
            'merge_convention': 'midas1'
        },
        'update': {
            'updatable_properties': [ "title", "authors", "_editStatus" ]
        }
    }

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("publish")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.nrddir = os.path.join(self.workdir, "nrdserv")
        self.storedir = os.path.join(self.workdir, "store")
        self.svc = mdsvc.MIDAS3PublishingService(self.defcfg, self.workdir,
                                                 self.revdir, self.upldir)

    def tearDown(self):
        self.svc._drop_all_workers(300)
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(os.path.isdir(self.svc.workdir))
        self.assertTrue(os.path.isdir(self.svc.mddir))
        self.assertTrue(os.path.isdir(self.svc.nrddir))
        self.assertTrue(os.path.isdir(self.svc.podqdir))
        self.assertTrue(os.path.isdir(self.svc.storedir))
        self.assertTrue(os.path.isdir(self.svc._schemadir))

        self.assertIsNotNone(self.svc._podvalid8r)

    def test_get_bagging_thread(self):
        bagdir = os.path.join(self.svc.mddir, "mds2-1491")
        self.assertTrue(not os.path.exists(bagdir))

        w = self.svc._get_bagging_worker(self.arkid)
        self.assertTrue(not os.path.exists(bagdir))  # not created until request to do something
        self.assertEqual(w.working_pod, os.path.join(self.svc.podqdir,"current","mds2-1491.json"))
        self.assertEqual(w.next_pod, os.path.join(self.svc.podqdir,"next","mds2-1491.json"))

    def test_queue_POD(self):
        bagdir = os.path.join(self.svc.mddir, "mds2-1491")
        w = self.svc._get_bagging_worker(self.arkid)
        self.assertTrue(not os.path.exists(bagdir))
        self.assertTrue(not os.path.exists(w.working_pod))
        self.assertTrue(not os.path.exists(w.next_pod))

        pod = utils.read_json(os.path.join(w.bagger.sip.revdatadir, "_pod.json"))
        w.queue_POD(pod)
        self.assertTrue(not os.path.exists(bagdir))
        self.assertTrue(not os.path.exists(w.working_pod))
        self.assertTrue(os.path.exists(w.next_pod))

        w.queue_POD(pod)
        self.assertTrue(not os.path.exists(w.working_pod))
        self.assertTrue(os.path.exists(w.next_pod))

        os.rename(w.next_pod, w.working_pod)
        self.assertTrue(os.path.exists(w.working_pod))
        self.assertTrue(not os.path.exists(w.next_pod))

        w.queue_POD(pod)
        self.assertTrue(os.path.isfile(w.working_pod))
        self.assertTrue(os.path.isfile(w.next_pod))

        pod = utils.read_json(os.path.join(w.bagger.sip.upldatadir, "_pod.json"))
        self.assertTrue(os.path.isfile(w.working_pod))
        self.assertTrue(os.path.isfile(w.next_pod))

    def test_update_ds_with_pod(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isdir(bagdir))
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","pod.json")))
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","nerdm.json")))
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata","trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.nrddir, self.midasid+".json")))
        data = utils.read_json(os.path.join(self.nrddir, self.midasid+".json"))
        self.assertEqual(data.get('ediid'), self.midasid)

    def test_update_ds_with_emptypod(self):
        with self.assertRaises(ValueError):
            self.svc.update_ds_with_pod({}, False)

    def test_update_ds_with_minpod(self):
        pod = {"identifier": self.midasid}
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isdir(bagdir))
        data = utils.read_json(os.path.join(self.nrddir, self.midasid+".json"))
        self.assertEqual(data.get('ediid'), self.midasid)

        pod = {"identifier": self.midasid, "description": ""}

        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isdir(bagdir))
        data = utils.read_json(os.path.join(self.nrddir, self.midasid+".json"))
        self.assertEqual(data.get('ediid'), self.midasid)

    def test_update_ds_with_badpod(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        pod['contactPoint']['hasEmail'] = "gurn.cranston@nist.gov"   # missing mailto: prefix!
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        with self.assertRaises(ValidationError):
            self.svc.update_ds_with_pod(pod, False)
        

    def test_update_ds_with_pod_wannot(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","nerdm.json")))

        # add some annotations
        annotf = os.path.join(bagdir,"metadata","annot.json")
        utils.write_json({"_marker": True}, annotf)
        self.assertTrue(NISTBag(bagdir).nerdm_record(True).get("_marker"),
                        "Failed to initialize annotations")

        self.svc.update_ds_with_pod(pod, True)
        self.svc.wait_for_all_workers(5)
        self.assertTrue(os.path.isdir(bagdir))
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","pod.json")))
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","nerdm.json")))
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","annot.json")))
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata","trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.nrddir, self.midasid+".json")))
        data = utils.read_json(os.path.join(self.nrddir, self.midasid+".json"))
        self.assertEqual(data.get('ediid'), self.midasid)
        self.assertTrue(data.get('_marker'), "Failed to retain annotations")

    def test_delete(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.assertTrue(not os.path.isdir(bagdir))
        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isdir(bagdir))

        self.svc.delete(pod['identifier'])
        self.assertTrue(not os.path.isdir(bagdir))

    def test_drop_worker(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, False)
        worker = self.svc._bagging_workers.get(pod['identifier'])
        self.assertIsNotNone(worker)

        self.svc._drop_bagging_worker(worker)
        self.assertNotIn(pod['identifier'], self.svc._bagging_workers)

    def test_no_double_logging(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.isdir(bagdir))
        plog = os.path.join(bagdir, "preserv.log")
        self.assertTrue(os.path.isfile(plog))

        podf = os.path.join(self.upldir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        self.svc.update_ds_with_pod(pod, False)
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

    def test_serve_nerdm(self):
        self.assertTrue(not os.path.exists(os.path.join(self.nrddir, "gramma.json")))
        self.assertTrue(not os.path.exists(os.path.join(self.nrddir, "pdr0-1000.json")))
        nerdm = {"foo": "bar", "ediid": "pdr0-1000"}

        self.svc.serve_nerdm(nerdm, "gramma")
        self.assertTrue(os.path.isfile(os.path.join(self.nrddir, "gramma.json")))
        self.assertTrue(not os.path.exists(os.path.join(self.nrddir, "pdr0-1000.json")))

        # see if we properly padded the record
        nerd = utils.read_json(os.path.join(self.nrddir, "gramma.json"))
        self.assertIn('contactPoint', nerd)
        self.assertEqual(nerd['contactPoint']['@type'], "vcard:Contact")
        self.assertEqual(nerd['contactPoint']['fn'], "")
        self.assertEqual(nerd['contactPoint']['hasEmail'], "")

        nerdm['contactPoint'] = {
            "fn": "Joe",
            "hasEmail": "joe@joe.com"
        }

        self.svc.serve_nerdm(nerdm)
        self.assertTrue(os.path.isfile(os.path.join(self.nrddir, "gramma.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.nrddir, "pdr0-1000.json")))

        nerd = utils.read_json(os.path.join(self.nrddir, "pdr0-1000.json"))
        self.assertIn('contactPoint', nerd)
        self.assertEqual(nerd['contactPoint']['fn'], "Joe")
        self.assertEqual(nerd['contactPoint']['hasEmail'], "joe@joe.com")
        self.assertEqual(nerd['contactPoint']['@type'], "vcard:Contact")

    def test_update_ds_with_pod_async(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        bagdir = os.path.join(self.svc.mddir, self.midasid)

        self.svc.update_ds_with_pod(pod, True)
        self.assertTrue(os.path.isdir(bagdir))

        self.svc.wait_for_all_workers(5)
        
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","pod.json")))
        self.assertTrue(os.path.isfile(os.path.join(bagdir,"metadata","nerdm.json")))
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata","trial1.json")))
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata","sim++.json")))

    def test_process_queue(self):
        bagdir = os.path.join(self.svc.mddir, self.midasid)
        w = self.svc._get_bagging_worker(self.midasid)
        self.assertTrue(not os.path.exists(bagdir))
        self.assertTrue(not os.path.exists(w.working_pod))
        self.assertTrue(not os.path.exists(w.next_pod))

        pod = utils.read_json(os.path.join(w.bagger.sip.revdatadir, "_pod.json"))
        self.svc.update_ds_with_pod(pod)
        self.assertTrue(os.path.exists(bagdir))
        pod = utils.read_json(os.path.join(w.bagger.sip.upldatadir, "_pod.json"))
        self.svc.update_ds_with_pod(pod)

        time.sleep(0.1)
        # there has not been enough time about to process the second one yet
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata","sim++.json")))
        self.assertTrue(not os.path.isdir(os.path.join(bagdir,"metadata","sim.json")))

        self.svc.wait_for_all_workers(5)
        
        self.assertTrue(not os.path.isdir(os.path.join(bagdir,"metadata","sim++.json")))
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata","sim.json")))

    def test_get_pod(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)
        self.svc.update_ds_with_pod(pod, False)

        gpod = self.svc.get_pod(self.midasid)

        self.assertEqual(pod, gpod)

        with self.assertRaises(mdsvc.IDNotFound):
            gpod = self.svc.get_pod("goober")

    def test_restart_workders(self):
        wpoddir = os.path.join(self.workdir, "podq", "current")
        npoddir = os.path.join(self.workdir, "podq", "next")
        os.makedirs(wpoddir)
        os.makedirs(npoddir)
        pod = utils.read_json(os.path.join(self.revdir, "1491", "_pod.json"))
        utils.write_json(pod, os.path.join(wpoddir, self.midasid+".json"))

        self.assertTrue(not os.path.exists(os.path.join(self.nrddir, self.midasid+".json")))

        self.svc.restart_workers()
        self.svc.wait_for_all_workers(300)

        nerdf = os.path.join(self.nrddir, self.midasid+".json")
        self.assertTrue(os.path.isfile(nerdf))
        nerd = utils.read_json(nerdf)
        self.assertTrue(nerd['title'].startswith("Op"))

        pod['title'] = "Goober!"
        utils.write_json(pod, os.path.join(npoddir, self.midasid+".json"))

        self.svc.restart_workers()
        self.svc.wait_for_all_workers(300)

        self.assertTrue(os.path.isfile(nerdf))
        nerd = utils.read_json(nerdf)
        self.assertEqual(nerd['title'], "Goober!")
        
        
                        



if __name__ == '__main__':
    test.main()

