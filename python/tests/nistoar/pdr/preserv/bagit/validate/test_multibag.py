from __future__ import print_function
import os, sys, pdb, json, shutil, copy

import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.validate.multibag as val
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
    
class TestMultibagValidator(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.bagdir = self.tf.track("mbag")
        shutil.copytree(bagdir, self.bagdir)
        
        self.bag = bag.NISTBag(self.bagdir)
        self.valid8 = val.MultibagValidator()

    def tearDown(self):
        self.tf.clean()

    def test_all_test_methods(self):
        expect = ["test_"+m for m in
          "version reference tag_directory head_version head_deprecates baginfo_recs".split()]
        expect.sort()
        meths = self.valid8.all_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

    def test_test_version(self):
        errs = self.valid8.test_version(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Version:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Version: 0.1", file=fd)

        errs = self.valid8.test_version(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Version-val"))

        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)

        errs = self.valid8.test_version(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Version"))

    def test_test_reference(self):
        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Reference:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Reference: ", file=fd)

        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Reference-val"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Reference: AIPSpec.pdf", file=fd)

        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Reference-val"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)

        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Reference"))
        
    def test_test_tag_directory(self):
        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Tag-Directory:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Tag-Directory: ", file=fd)

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Tag-Directory"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Tag-Directory: goober", file=fd)

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Tag-Directory"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Tag-Directory: multibag", file=fd)
            print("Multibag-Tag-Directory: multibag", file=fd)

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Tag-Directory"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
        shutil.rmtree(os.path.join(self.bag.dir, "multibag"))

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Tag-Directory"))
        
        
    def test_test_head_version(self):
        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Head-Version:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Version: ", file=fd)

        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Head-Version"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Version: 1.0", file=fd)
            print("Multibag-Head-Version: 1.2", file=fd)

        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Head-Version"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)

        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Head-Version"))
        
    def test_test_head_deprecates(self):
        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines
                       if "Multibag-Head-Deprecates:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Deprecates: ", file=fd)

        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(len(errs), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Head-Deprecates"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Deprecates: 0.9", file=fd)
            print("Multibag-Head-Deprecates: 1.2", file=fd)

        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(len(errs), 0, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")

        with open(bif, 'a') as fd:
            print("Multibag-Head-Deprecates: ", file=fd)
            print("Multibag-Head-Version: 1.2", file=fd)
        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(len(errs), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-Head-Deprecates"))
        
    def test_test_baginfo_recs(self):
        errs = self.valid8.test_baginfo_recs(self.bag)
        self.assertEqual(errs, [],
                         "False Positives: "+ str([str(e) for e in errs]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines
                       if "Bag-Group-Identifier:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Internal-Sender-Description: ", file=fd)
        
        errs = self.valid8.test_baginfo_recs(self.bag)
        self.assertEqual(len(errs), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs]) + "\n]")
        self.assertTrue(has_error(errs, "1.2-2"))
        



if __name__ == '__main__':
    test.main()

        



        
                
