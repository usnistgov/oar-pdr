from __future__ import print_function
import os, sys, pdb, json, shutil, copy, re

import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.validate.nist as val
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
        self.bagdir = self.tf.track("XXXX.mbag0_2-0")
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
        
        self.valid8 = val.NISTBagValidator()

    def tearDown(self):
        self.tf.clean()

    def test_all_test_methods(self):
        expect = ["test_"+m for m in
          "name".split()]
        expect.sort()
        meths = self.valid8.all_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

    def test_test_name(self):
        errs = self.valid8.test_name(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        

if __name__ == '__main__':
    test.main()
