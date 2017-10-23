from __future__ import print_function
import os, sys, pdb, json, shutil, copy

import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.validate.bagit as val
import nistoar.pdr.preserv.bagit.bag as bag
import nistoar.pdr.preserv.bagit.exceptions as bagex
import nistoar.pdr.exceptions as exceptions

datadir = os.path.join( os.path.dirname(os.path.dirname(
                           os.path.dirname(__file__))), "data" )
bagdir = os.path.join(datadir, "samplembag")

def setUpModule():
    ensure_tmpdir()

def tearDownModule():
    rmtmpdir()

def has_error(errs, label):
    return len([e for e in errs if e.label == label]) > 0
    
class TestBagItValidator(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.bagdir = self.tf.track("mbag")
        shutil.copytree(bagdir, self.bagdir)
        
        self.bag = bag.NISTBag(self.bagdir)
        self.valid8 = val.BagItValidator()

    def tearDown(self):
        self.tf.clean()

    def test_all_test_methods(self):
        expect = ["test_"+m for m in
             "bagit_txt data_dir manifest tagmanifest baginfo fetch_txt".split()]
        expect.sort()
        meths = self.valid8.all_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

    def test_the_test_methods(self):
        all = ["test_"+m for m in
             "bagit_txt data_dir manifest tagmanifest baginfo fetch_txt".split()]
        all.sort()
        meths = self.valid8.the_test_methods()
        meths.sort()
        self.assertEqual(meths, all)
        
        config = {
            "skip_tests": ["test_"+m for m in "data_dir baginfo".split()]
        }
        self.valid8 = val.BagItValidator(config)
        expect = [t for t in all if t not in config['skip_tests']]
        expect.sort()
        meths = self.valid8.the_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

        config['include_tests']= ["test_"+m for m in "data_dir manifest".split()]
        self.valid8 = val.BagItValidator(config)
        expect = [t for t in all if t in config['include_tests']]
        expect.sort()
        meths = self.valid8.the_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

    def test_test_bagit_txt(self):
        errs = self.valid8.test_bagit_txt(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bagitf = os.path.join(self.bag.dir, "bagit.txt")
        with open(bagitf, 'w') as fd:
            print("BagIt-Version: 1.0", file=fd)
        errs = self.valid8.test_bagit_txt(self.bag)
        self.assertGreater(len(errs), 0)
        self.assertTrue(has_error(errs, "2.1.1-3"))
        self.assertTrue(has_error(errs, "2.1.1-4"))
                         
        with open(bagitf, 'w') as fd:
            print("Tag-File-Character-Encoding: 1.0", file=fd)
        errs = self.valid8.test_bagit_txt(self.bag)
        self.assertGreater(len(errs), 0)
        self.assertTrue(has_error(errs, "2.1.1-2"))
        self.assertTrue(has_error(errs, "2.1.1-5"))

        os.remove(bagitf)
        errs = self.valid8.test_bagit_txt(self.bag)
        self.assertGreater(len(errs), 0)
        self.assertTrue(has_error(errs, "2.1.1-1"))

    def test_test_data_dir(self):
        errs = self.valid8.test_data_dir(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        shutil.rmtree(self.bag.data_dir)
        errs = self.valid8.test_data_dir(self.bag)
        self.assertGreater(len(errs), 0)
        self.assertTrue(has_error(errs, "2.1.2"))

    def test_test_manifest(self):
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        mf = os.path.join(self.bag.dir, "manifest-sha256.txt")
        with open(mf, 'a') as fd:
            print("sd9wh32 metadata/nerdm.json", file=fd)
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(len(errs), 1)
        self.assertTrue(has_error(errs, "2.1.3-3"))

        with open(mf, 'a') as fd:
            print("blah", file=fd)
            print("a secret garden", file=fd)
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(len(errs), 2)
        self.assertTrue(has_error(errs, "2.1.3-2"))

        os.remove(mf)
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(len(errs), 1)
        self.assertTrue(has_error(errs, "2.1.3-1"))
        
        with open(os.path.join(bagdir, "manifest-sha256.txt")) as fd:
            lines = fd.readlines()
        lines.pop(0)
        line = lines.pop(0)
        lines.append("x9sx8lsd "+line.split()[1]+"\n")
        with open(mf, 'w') as fd:
            for line in lines:
                fd.write(line)
            print("sd8h2h20hgw data/trial3", file=fd)
            print("sd8h2h20hgw data/goober.txt", file=fd)
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(len(errs), 4)
        self.assertTrue(has_error(errs, "2.1.3-7"))
        self.assertTrue(has_error(errs, "3-1-2"))
        self.assertTrue(has_error(errs, "2.1.3-4"))
        self.assertTrue(has_error(errs, "2.1.3-5"))

        self.valid8.cfg = {
            "test_manifest": {
                "check_checksums": False
            }
        }
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(len(errs), 3)
        self.assertTrue(has_error(errs, "2.1.3-7"))
        self.assertTrue(has_error(errs, "3-1-2"))
        self.assertTrue(has_error(errs, "2.1.3-4"))
            
    def test_test_tagmanifest(self):
        errs = self.valid8.test_tagmanifest(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        mf = os.path.join(self.bag.dir, "tagmanifest-sha256.txt")
        with open(mf, 'a') as fd:
            print("blah", file=fd)
            print("a secret garden", file=fd)
        errs = self.valid8.test_tagmanifest(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "2.1.3-2"))

        os.remove(mf)
        errs = self.valid8.test_tagmanifest(self.bag)
        self.assertEqual(len(errs), 0, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        
        with open(os.path.join(bagdir, "manifest-sha256.txt")) as fd:
            lines = fd.readlines()
        lines.pop(0)
        line = lines.pop(0)
        lines.append("x9sx8lsd "+line.split()[1]+"\n")
        with open(mf, 'w') as fd:
            for line in lines:
                fd.write(line)
            print("sd8h2h20hgw data/trial3", file=fd)
            print("sd8h2h20hgw data/goober.txt", file=fd)
        errs = self.valid8.test_tagmanifest(self.bag)
        self.assertEqual(len(errs), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "2.1.3-7"))
        self.assertTrue(has_error(errs, "3-1-2"))

        self.valid8.cfg = {
            "test_manifest": {
                "check_checksums": False
            }
        }
        errs = self.valid8.test_manifest(self.bag)
        self.assertEqual(len(errs), 0)
            
    def test_test_baginfo(self):
        errs = self.valid8.test_baginfo(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif, 'a') as fd:
            print("Incorrect", file=fd)
        errs = self.valid8.test_baginfo(self.bag)
        self.assertEqual(len(errs), 1)
        self.assertTrue(has_error(errs, "2.2.2-2"))
        self.assertEqual(errs[0].type, "error")
        
        os.remove(bif)
        errs = self.valid8.test_baginfo(self.bag)
        self.assertEqual(len(errs), 1)
        self.assertTrue(has_error(errs, "2.2.2-1"))
        self.assertEqual(errs[0].type, "recommendation")
        
        with open(bif, 'w') as fd:
            print(" Incorrect", file=fd)
            print("name: value", file=fd)
            print("Bagging-Date: 2017", file=fd)
            print("Bag-Size: 2017", file=fd)
        errs = self.valid8.test_baginfo(self.bag)
        self.assertEqual(len(errs), 3, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "2.2.2-2"))
        self.assertTrue(has_error(errs, "2.2.2-Bagging-Date"))
        self.assertTrue(has_error(errs, "2.2.2-Bag-Size"))
        self.assertEqual(errs[0].type, "error")

    def test_test_fetch_txt(self):
        errs = self.valid8.test_fetch_txt(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        ff = os.path.join(self.bag.dir, "fetch.txt")
        with open(ff, 'a') as fd:
            print("Incorrect", file=fd)
            print("Incorrect file", file=fd)
            print("data/goober http://goober.net/get 20", file=fd)
            print("data/goober 20 http://goober.net/get", file=fd)
            
        errs = self.valid8.test_fetch_txt(self.bag)
        self.assertEqual(len(errs), 3, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "2.2.3-1"))
        self.assertTrue(has_error(errs, "2.2.3-2"))
        self.assertTrue(has_error(errs, "2.2.3-3"))
        self.assertEqual(errs[0].type, "error")

        os.remove(ff)
        errs = self.valid8.test_fetch_txt(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

    def test_validate(self):
        errs = self.valid8.validate(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        # Mess up bag to see if all tests are getting run
        bagitf = os.path.join(self.bag.dir, "bagit.txt")
        with open(bagitf, 'w') as fd:
            print("BagIt-Version: 1.0", file=fd)

        shutil.rmtree(self.bag.data_dir)

        mf = os.path.join(self.bag.dir, "tagmanifest-sha256.txt")
        with open(mf, 'a') as fd:
            print("alskdf", file=fd)

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif, 'a') as fd:
            print("Incorrect", file=fd)
        ff = os.path.join(self.bag.dir, "fetch.txt")
        with open(ff, 'a') as fd:
            print("Incorrect", file=fd)
        
        errs = self.valid8.validate(self.bag)
        self.assertGreater(len(errs), 0)
        self.assertTrue(has_error(errs, "2.1.1-3"))
        self.assertTrue(has_error(errs, "2.1.1-4"))
        self.assertTrue(has_error(errs, "2.1.1-4"))
        self.assertTrue(has_error(errs, "2.2.3-1"))
        self.assertTrue(has_error(errs, "2.2.2-2"))
        self.assertTrue(has_error(errs, "2.1.2"))
        self.assertTrue(has_error(errs, "2.1.3-2"))
        self.assertTrue(has_error(errs, "3-1-2"))
                         
        
        
class TestFmts(test.TestCase):
    def test_email(self):
        self.assertTrue(val._fmt_email("raymond.plante@nist.gov"))
        self.assertTrue(val._fmt_email("ray10171964@gmail.com"))
        self.assertFalse(val._fmt_email("rlp3@nist"))
        self.assertFalse(val._fmt_email("rlp3nist"))
        self.assertFalse(val._fmt_email("ra#964@gmail.com"))

    def test_date(self):
        self.assertTrue(val._fmt_date("2017-10-19"))
        self.assertTrue(val._fmt_date("1907-01-19"))
        self.assertTrue(val._fmt_date("2007-12-20"))
        self.assertTrue(val._fmt_date("2007-12-30"))
        self.assertTrue(val._fmt_date("2007-12-31"))
        self.assertFalse(val._fmt_date("2007-1-19"))
        self.assertFalse(val._fmt_date("2007-01-9"))
        self.assertFalse(val._fmt_date("2007-21-19"))
        self.assertFalse(val._fmt_date("2007-12-34"))

    def test_bagsz(self):
        self.assertTrue(val._fmt_bagsz("132 kb"))
        self.assertTrue(val._fmt_bagsz("132. kB"))
        self.assertTrue(val._fmt_bagsz("132.23 MB"))
        self.assertTrue(val._fmt_bagsz("0.23 GB"))
        self.assertTrue(val._fmt_bagsz(".230 Tb"))
        self.assertFalse(val._fmt_bagsz(". Tb"))
        self.assertFalse(val._fmt_bagsz("23 bytes"))
        self.assertFalse(val._fmt_bagsz("Four kilobytes"))

    def test_bagcnt(self):
        self.assertTrue(val._fmt_bagcnt("1 of 1"))
        self.assertTrue(val._fmt_bagcnt("5 of ?"))
        self.assertTrue(val._fmt_bagcnt("23 of 198"))
        self.assertFalse(val._fmt_bagcnt("12"))
        self.assertFalse(val._fmt_bagcnt("12 of X"))
        self.assertFalse(val._fmt_bagcnt("X of 23"))

    def test_oxum(self):
        self.assertTrue(val._fmt_oxum("0.0"))
        self.assertTrue(val._fmt_oxum("23481.23"))
        self.assertTrue(val._fmt_oxum("8.3"))
        self.assertFalse(val._fmt_oxum(".3"))
        self.assertFalse(val._fmt_oxum("3."))
        self.assertFalse(val._fmt_oxum("3."))
        self.assertFalse(val._fmt_oxum("Four"))
        self.assertFalse(val._fmt_oxum("243509"))

if __name__ == '__main__':
    test.main()

        

