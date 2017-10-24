from __future__ import print_function
import os, sys, pdb, json, shutil, copy, re

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
    return len([e for e in errs.failed() if e.label == label]) > 0
    
class TestMultibagValidator(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.bagdir = self.tf.track("mbag")
        shutil.copytree(bagdir, self.bagdir)
        
        self.bag = bag.NISTBag(self.bagdir)
        mbtagf = os.path.join(self.bag.multibag_dir, "group-members.txt")
        with open(mbtagf, 'w') as fd:
            print(self.bag.name, file=fd)
        mbtagf = os.path.join(self.bag.multibag_dir, "group-directory.txt")
        nmre = re.compile(r'samplebag')
        with open(mbtagf) as fd:
            lines = fd.readlines()
        with open(mbtagf, 'w') as fd:
            for line in lines:
                fd.write(nmre.sub(self.bag.name, line))
        
        self.valid8 = val.MultibagValidator()

    def tearDown(self):
        self.tf.clean()

    def test_all_test_methods(self):
        expect = ["test_"+m for m in
          "version reference tag_directory head_version head_deprecates baginfo_recs group_members group_directory".split()]
        expect.sort()
        meths = self.valid8.all_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

    def test_test_version(self):
        errs = self.valid8.test_version(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Version:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Version: 0.1", file=fd)

        errs = self.valid8.test_version(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Version-val"))

        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)

        errs = self.valid8.test_version(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Version"))

    def test_test_reference(self):
        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Reference:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Reference: ", file=fd)

        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(len(errs.failed()), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Reference-val"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Reference: AIPSpec.pdf", file=fd)

        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Reference-val"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)

        errs = self.valid8.test_reference(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Reference"))
        
    def test_test_tag_directory(self):
        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(errs.failed(), [],
                       "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Tag-Directory:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Tag-Directory: ", file=fd)

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Tag-Directory"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Tag-Directory: goober", file=fd)

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Tag-Directory"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Tag-Directory: multibag", file=fd)
            print("Multibag-Tag-Directory: multibag", file=fd)

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Tag-Directory"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
        shutil.rmtree(os.path.join(self.bag.dir, "multibag"))

        errs = self.valid8.test_tag_directory(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Tag-Directory"))
        
        
    def test_test_head_version(self):
        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(errs.failed(), [],
                       "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            biflines = fd.readlines()
        biflines = [ln for ln in biflines if "Multibag-Head-Version:" not in ln]
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Version: ", file=fd)

        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Head-Version"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Version: 1.0", file=fd)
            print("Multibag-Head-Version: 1.2", file=fd)

        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Head-Version"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)

        errs = self.valid8.test_head_version(self.bag, True)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Head-Version"))
        
    def test_test_head_deprecates(self):
        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(errs.failed(), [],
                       "False Positives: "+ str([str(e) for e in errs.failed()]))

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
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Head-Deprecates"))
        
        with open(bif, 'w') as fd:
            for line in biflines:
                fd.write(line)
            print("Multibag-Head-Deprecates: 0.9", file=fd)
            print("Multibag-Head-Deprecates: 1.2", file=fd)

        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(len(errs.failed()), 0, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")

        with open(bif, 'a') as fd:
            print("Multibag-Head-Deprecates: ", file=fd)
            print("Multibag-Head-Version: 1.2", file=fd)
        errs = self.valid8.test_head_deprecates(self.bag, True)
        self.assertEqual(len(errs.failed()), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-Head-Deprecates"))
        
    def test_test_baginfo_recs(self):
        errs = self.valid8.test_baginfo_recs(self.bag)
        self.assertEqual(errs.failed(), [],
                     "False Positives: "+ str([str(e) for e in errs.failed()]))

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
        self.assertEqual(len(errs.failed()), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-2"))

    def test_test_group_members(self):
        errs = self.valid8.test_group_members(self.bag)
        self.assertEqual(errs.failed(), [],
                     "False Positives: "+ str([str(e) for e in errs.failed()]))

        gmf = os.path.join(self.bag.multibag_dir, "group-members.txt")
        with open(gmf, 'a') as fd:
            print(self.bag.name, file=fd)
            print("goober_bag bag.zip", file=fd)
            print("goober_bag bag.zip", file=fd)
            print("goober_bag bag.zip", file=fd)
            print("goober_bag bag.zip", file=fd)
            print("gurn_bag bag.zip foobar", file=fd)

        errs = self.valid8.test_group_members(self.bag, ishead=True)
        self.assertEqual(len(errs.failed()), 4, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3.1-1"))
        self.assertTrue(has_error(errs, "3.1-2"))
        self.assertTrue(has_error(errs, "3.1-4"))
        self.assertTrue(has_error(errs, "3.1-5"))

        os.remove(gmf)
        errs = self.valid8.test_group_members(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3.0-1"))
        
        with open(gmf, 'w') as fd:
            print("goober_bag", file=fd)
        errs = self.valid8.test_group_members(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3.1-3"))

    def test_test_group_directory(self):
        errs = self.valid8.test_group_directory(self.bag)
        self.assertEqual(errs.failed(), [],
                     "False Positives: "+ str([str(e) for e in errs.failed()]))

        gdf = os.path.join(self.bag.multibag_dir, "group-directory.txt")
        with open(gdf, 'a') as fd:
            print("data/goober.dat {0}".format(self.bag.name), file=fd)
            print("data/goober.dat otherbag", file=fd)
            print("gurn.json", file=fd)
            print("gurn.json booger bonnet", file=fd)
            print("data/trial1.json otherbag", file=fd)

        errs = self.valid8.test_group_directory(self.bag)
        self.assertEqual(len(errs.failed()), 3, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3.2-1"))
        self.assertTrue(has_error(errs, "3.2-2"))
        self.assertTrue(has_error(errs, "3.2-3"))

        with open(gdf, 'w') as fd:
            print("data/trial1.json {0}".format(self.bag.name), file=fd)

        errs = self.valid8.test_group_directory(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3.2-4"))

        os.remove(gdf)
        errs = self.valid8.test_group_directory(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3.0-2"))


if __name__ == '__main__':
    test.main()

        



        
                
