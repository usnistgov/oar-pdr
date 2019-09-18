from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib, shutil
from collections import OrderedDict
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.bagit import multibag
from nistoar.pdr.exceptions import IDNotFound
from nistoar.pdr.utils import checksum_of
from nistoar.pdr.distrib import DistribResourceNotFound
from nistoar.pdr.preserv.bagit import NISTBag

from multibag.testing import mkdata
import bagit

bagsrcdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
mdsrcdir = os.path.join(os.path.dirname(os.path.dirname(bagsrcdir)), "describe", "data")

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_simsrv.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

def mkbag(dsdir):
    spec = {
        "totalfiles": 22,
        "totalsize": 1014600,
        "files": [{ "type": "inventory",
                    "sizes": { 1400: 1, 159800: 1, 35000: 2, 0: 1, 1000: 1 }}],
        "dirs": [{
            "files": [{ "type": "inventory", "sizes": { 86000: 3 }}],
            "dirs": [{
                "files": [{ "type": "inventory", "sizes": {110000: 1, 5800: 4}}]
            }]
        }, {
            "files": [{ "type": "inventory", "sizes": { 86000: 3 }}],
            "dirs": [{
                "files": [{ "type": "inventory", "sizes": {110000: 1, 5800: 4}}]
            }]
        }]
    }

    mkr = mkdata.DatasetMaker(dsdir, spec)
    mkr.fill()

    bag = bagit.make_bag(dsdir)
    # self.assertTrue(bag.validate())

    # create metadata tree
    datadir = os.path.join(dsdir,"data")
    mdatadir = os.path.join(dsdir,"metadata")
    os.mkdir(mdatadir)
    with open(os.path.join(dsdir,"tagmanifest-sha256.txt"), "a") as fd:
        for dir, subdirs, files in os.walk(datadir):
            for f in files:
                f = os.path.join(mdatadir, os.path.join(dir, f)[len(datadir)+1:])
                if not os.path.exists(os.path.dirname(f)):
                    os.makedirs(os.path.dirname(f))
                mkdata.create_file(f, 16)
                fd.write("{0} {1}\n".format(checksum_of(f), f[len(dsdir)+1:]))

    # set the Bag-Size
    sz = du(dsdir)
    line = "Bag-Size: {0} B\n".format(sz)
    sz += len(line)
    line = "Bag-Size: {0} B\n".format(sz)
    with open(os.path.join(dsdir, "bag-info.txt"), "a") as fd:
        fd.write(line)


def du(udir):
    tot = 0
    for dir, subdirs, files in os.walk(udir):
        for f in files:
            tot += os.stat(os.path.join(dir, f)).st_size
    return tot

class TestOARSplitter(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("preserv")

    def tearDown(self):
        self.tf.clean()

    def test_plan(self):
        bagdir = os.path.join(self.workdir,"dataset")
        mkbag(bagdir)

        self.assertTrue(os.path.isdir(os.path.join(bagdir,"data")))
        self.assertTrue(os.path.isdir(os.path.join(bagdir,"metadata")))

        spltr = multibag.OARSplitter(400000)
        plan = spltr.plan(bagdir)

        self.assertTrue(plan.is_complete())
        mfs = list(plan.manifests())
        # self.assertEqual(len(mfs), 3)
        self.assertGreater(len(mfs), 1)

        # all metadata files are in the last output multibag
        for i in range(len(mfs)-1):
            self.assertEqual(len([p for p in mfs[i]['contents']
                                    if p.startswith("metadata/")]), 0)
        self.assertEqual(len([p for p in mfs[-1]['contents']
                              if p.startswith("metadata/")]), 22)

        for mf in mfs:
            self.assertLess(mf['totalsize'], 1.05*400000)

class TestMultibagSplitter(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("preserv")
        self.bagdir = os.path.join(self.workdir,"dataset-0")
        mkbag(self.bagdir)
        self.spltr = None

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.spltr = multibag.MultibagSplitter(self.bagdir)
        self.assertEqual(self.spltr.maxsz, 0)
        self.assertEqual(self.spltr.maxhbsz, 0)
        self.assertEqual(self.spltr.trgsz, 0)

        cfg = {
            "max_bag_size": 1000000000,
            "max_headbag_size": 5000000,
            "target_bag_size": 800000000
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)
        self.assertEqual(self.spltr.maxsz, 1000000000)
        self.assertEqual(self.spltr.maxhbsz, 5000000)
        self.assertEqual(self.spltr.trgsz, 800000000)

        cfg = {
            "max_bag_size": 10000000
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)
        self.assertEqual(self.spltr.maxsz, 10000000)
        self.assertEqual(self.spltr.maxhbsz, 10000000)
        self.assertEqual(self.spltr.trgsz, 10000000)

    def test_check(self):
        cfg = {
            "max_bag_size": 1000000000,
            "max_headbag_size": 5000000,
            "target_bag_size": 800000000
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)
        self.assertFalse( self.spltr.check() )

        cfg = {
            "max_bag_size": 10000,
            "max_headbag_size": 5000000
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        self.assertTrue( self.spltr.check() )

        cfg = {
            "max_bag_size": 10000
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        self.assertTrue( self.spltr.check() )

        cfg = { }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        self.assertFalse( self.spltr.check() )

    def test_split(self):
        cfg = {
            "max_bag_size": 400000,
            "max_headbag_size": 50000,
            "verify_complete": True,
            "validate": True
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.split(self.workdir)
        self.assertEqual([os.path.basename(b) for b in bags],
                         ["dataset-1", "dataset-2", "dataset-3", "dataset-4"])
        self.assertTrue(os.path.isdir(os.path.join(bags[-1], "multibag")))

    def test_split_replace(self):
        cfg = {
            "max_bag_size": 400000,
            "max_headbag_size": 50000,
            "replace": True,
            "verify_complete": False
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.split(self.workdir)
        self.assertEqual([os.path.basename(b) for b in bags],
                         ["dataset-0", "dataset-1", "dataset-2", "dataset-3"])
        self.assertTrue(os.path.isdir(os.path.join(bags[-1], "multibag")))

    def test_split_too_small(self):
        cfg = {
            "max_bag_size": 400000000,
            "max_headbag_size": 50000000,
            "verify_complete": False
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.split(self.workdir)
        self.assertEqual(len(bags), 1)
        self.assertTrue(os.path.exists(os.path.join(bags[0], "multibag")))

    def test_check_and_split(self):
        cfg = {
            "max_bag_size": 400000,
            "max_headbag_size": 50000
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.check_and_split(self.workdir)
        self.assertEqual(len(bags), 4)
        self.assertTrue(os.path.exists(os.path.join(bags[-1], "multibag")))

    def test_check_and_split_too_small(self):
        cfg = {
            "max_bag_size": 400000000,
            "max_headbag_size": 50000000,
            "verify_complete": False
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.check_and_split(self.workdir)
        self.assertEqual(len(bags), 1)
        self.assertFalse(os.path.exists(os.path.join(bags[0], "multibag")))

    def test_check_and_split_mksingle(self):
        cfg = {
            "max_bag_size": 400000000,
            "max_headbag_size": 50000000,
            "convert_small": True,
            "verify_complete": False
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.check_and_split(self.workdir)
        self.assertEqual(len(bags), 1)
        self.assertTrue(os.path.exists(os.path.join(bags[0], "multibag")))

    def test_verify_complete(self):
        cfg = {
            "max_bag_size": 400000,
            "max_headbag_size": 50000,
            "verify_complete": False
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.split(self.workdir)

        self.spltr._verify_complete(self.bagdir, bags)

        with open(os.path.join(bags[0],"manifest-sha256.txt")) as fd:
            datafile = fd.readline().strip().split()[-1]
        os.remove(os.path.join(bags[0], datafile))

        try:
            self.spltr._verify_complete(self.bagdir, bags)
            self.fail("Failed to raise Validation exception")
        except Exception as ex:
            self.assertEqual(len(ex.errors), 1)

        datafile = "meta"+datafile
        os.remove(os.path.join(bags[-1], datafile))

        try:
            errors = self.spltr._verify_complete(self.bagdir, bags)
            self.fail("Failed to raise Validation exception")
        except Exception as ex:
            self.assertEqual(len(ex.errors), 2)

                         
    def test_confirm_found(self):
        cfg = {
            "max_bag_size": 400000,
            "max_headbag_size": 50000,
            "verify_complete": False
        }
        self.spltr = multibag.MultibagSplitter(self.bagdir, cfg)

        bags = self.spltr.split(self.workdir)
        headbag = multibag.multibag.open_headbag(bags[-1])

        error = self.spltr._confirm_found("data/goober", bags, headbag)
        self.assertIsNotNone(error)
        self.assertIn("Failed to find", error)
        

        
        
                    



if __name__ == '__main__':
    test.main()
