from __future__ import print_function
import os, sys, pdb, json, shutil, copy, re

import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.validate.nist as val
import nistoar.pdr.preserv.bagit.bag as bag
import nistoar.pdr.preserv.bagit.exceptions as bagex
import nistoar.pdr.exceptions as exceptions

pydir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
basedir = os.path.dirname(pydir)
schemadir = os.path.join(basedir, "oar-metadata", "model")

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
        self.bagdir = self.tf.track("XXXX.1_0.mbag0_4-0")
        shutil.copytree(bagdir, self.bagdir)
        
        self.bag = bag.NISTBag(self.bagdir)
        mbtagf = os.path.join(self.bag.multibag_dir, "member-bags.tsv")
        with open(mbtagf, 'w') as fd:
            print(self.bag.name, file=fd)
        mbtagf = os.path.join(self.bag.multibag_dir, "file-lookup.tsv")
        nmre = re.compile(r'samplebag')
        with open(mbtagf) as fd:
            lines = fd.readlines()
        with open(mbtagf, 'w') as fd:
            for line in lines:
                fd.write(nmre.sub(self.bag.name, line))

        config = {
            "nerdm_schema_dir": schemadir,
        }
        
        self.valid8 = val.NISTBagValidator(config)

    def tearDown(self):
        self.tf.clean()

    def test_all_test_methods(self):
        expect = ["test_"+m for m in
          "name bagit_mdels version nist_md metadata_dir pod nerdm metadata_tree nerdm_validity".split()]
        expect.sort()
        meths = self.valid8.all_test_methods()
        meths.sort()
        self.assertEqual(meths, expect)

    def test_test_name(self):
        errs = self.valid8.test_name(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        badbag = val.NISTBag(self.tf.mkdir("goober"))
        errs = self.valid8.test_name(badbag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-0"))
        
        badbag = val.NISTBag(self.tf.mkdir("XXXX.3_5_2.mbag1_0-10"))
        errs = self.valid8.test_name(badbag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "2-2"))
        
    def test_name_patterns(self):
        self.assertIsNotNone(self.valid8.namere02.match("XXXX.mbag0_2-0"))
        self.assertIsNotNone(self.valid8.namere02.match("XXXX.mbag1_0-10"))
        self.assertIsNotNone(self.valid8.namere02.match("XXXX.mbag13_40-103"))

        self.assertIsNone(self.valid8.namere02.match("XXXX.mbag0_2-"))
        self.assertIsNone(self.valid8.namere02.match("XXXX.mbag0.2-3"))
        self.assertIsNone(self.valid8.namere02.match("XXXX.mbag"))
        self.assertIsNone(self.valid8.namere02.match("samplebag"))

        self.assertIsNotNone(self.valid8.namere04.match("XXXX.1_0.mbag0_2-0"))
        self.assertIsNotNone(self.valid8.namere04.match("XXXX.1_2_3.mbag1_0-10"))
        self.assertIsNotNone(self.valid8.namere04.match("XXXX.21_12.mbag13_40-103"))

        
    def test_test_bagit_mdels(self):
        errs = self.valid8.test_bagit_mdels(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            bilines = fd.readlines()

        with open(bif, 'w') as fd:
            for line in bilines:
                if not line.startswith('Source-Organization:') and \
                   not line.startswith('Organization-Address') and \
                   "ark:/" not in line:
                    fd.write(line)
            print('External-Identifier: doi:10.18434/T45K4', file=fd)
            print('Organization-Address: 100 Bureau Drive', file=fd)

        errs = self.valid8.test_bagit_mdels(self.bag, True)
        self.assertEqual(len(errs.failed()), 4, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3-1-1"))
        self.assertTrue(has_error(errs, "3-1-1-1"))
        self.assertTrue(has_error(errs, "3-2-1-1"))
        self.assertTrue(has_error(errs, "3-2-3-1"))
        
        with open(bif, 'a') as fd:
            print('External-Identifier: ark:/18434/T45K4', file=fd)
            print('Source-Organization: NIST', file=fd)
            print('Organization-Address: Gaithersburg, MD 20899', file=fd)
            
        errs = self.valid8.test_bagit_mdels(self.bag, True)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3-1-1-1"))

    def test_test_version(self):
        errs = self.valid8.test_version(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif) as fd:
            bilines = fd.readlines()

        with open(bif, 'w') as fd:
            for line in bilines:
                if not line.startswith('NIST-BagIt-Version:'):
                    fd.write(line)

        errs = self.valid8.test_version(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3-3-1"))
        
    def test_test_nist_md(self):
        errs = self.valid8.test_nist_md(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        bif = os.path.join(self.bag.dir, "bag-info.txt")
        with open(bif, 'a') as fd:
            print("NIST-POD-Metadata: pod.json", file=fd)
            print("NIST-NERDm-Metadata: metadata/nerdm.json", file=fd)

        errs = self.valid8.test_nist_md(self.bag)
        self.assertEqual(len(errs.failed()), 2, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3-3-2"))
        
        with open(bif, 'a') as fd:
            print("NIST-NERDm-Metadata: ", file=fd)

        errs = self.valid8.test_nist_md(self.bag)
        self.assertEqual(len(errs.failed()), 5, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "3-3-2"))
        self.assertTrue(has_error(errs, "3-3-3"))
        
    def test_test_metadata_dir(self):
        errs = self.valid8.test_metadata_dir(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        shutil.rmtree(self.bag.metadata_dir)
        errs = self.valid8.test_metadata_dir(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "4.1-1"))
                
    def test_test_pod(self):
        errs = self.valid8.test_pod(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        podfile = os.path.join(self.bag.metadata_dir, "pod.json")
        os.remove(podfile)
        errs = self.valid8.test_pod(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "4.1-2-0"))

        with open(podfile, 'w') as fd:
            print("Goober!", file=fd)
        errs = self.valid8.test_pod(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "4.1-2-1"))

    def test_get_mdval_flavor(self):
        data = [
            {"$schema": 1},
            {"$extensionSchemas": 1},
            {"$schema": 1, "$extensionSchemas": 1},
            {"_schema": 1},
            {"_extensionSchemas": 1},
            {"_schema": 1, "_extensionSchemas": 1},
            {"schema": 1, "extensionSchemas": 1}
        ]
        for i in range(len(data)):
            pfx = self.valid8._get_mdval_flavor(data[i])
            if i < 3:
                self.assertEqual(pfx, "$")
            else:
                self.assertEqual(pfx, "_")

    def test_test_nerdm(self):
        errs = self.valid8.test_nerdm(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        nerdmfile = os.path.join(self.bag.metadata_dir, "nerdm.json")
        os.remove(nerdmfile)
        errs = self.valid8.test_nerdm(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "4.1-3-0"))

        with open(nerdmfile, 'w') as fd:
            print("Goober!", file=fd)
        errs = self.valid8.test_nerdm(self.bag)
        self.assertEqual(len(errs.failed()), 1, "Unexpected # of errors: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "4.1-3-1"))

    def test_test_metadat_tree(self):
        errs = self.valid8.test_metadata_tree(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        os.remove(os.path.join(self.bag.metadata_dir,"trial1.json","nerdm.json"))
        os.remove(os.path.join(self.bag.metadata_dir,"trial3","nerdm.json"))
        errs = self.valid8.test_metadata_tree(self.bag)
        self.assertEqual(len(errs.failed()), 1, "# of errors != 1: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-5")
        
        os.rmdir(os.path.join(self.bag.metadata_dir,"trial1.json"))
        errs = self.valid8.test_metadata_tree(self.bag)
        self.assertEqual(len(errs.failed()), 2, "# of errors != 2: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-1b")
        self.assertEqual(errs.failed()[1].label, "4.1-5")
        
        shutil.rmtree(os.path.join(self.bag.metadata_dir,"trial3"))
        errs = self.valid8.test_metadata_tree(self.bag)
        self.assertEqual(len(errs.failed()), 2, "# of errors != 2: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-1a")
        self.assertEqual(errs.failed()[1].label, "4.1-4-1b")

        shutil.copyfile(os.path.join(self.bag.data_dir,"trial1.json"),
                        os.path.join(self.bag.metadata_dir,"trial1.json"))
        shutil.copyfile(os.path.join(self.bag.data_dir,"trial1.json"),
                        os.path.join(self.bag.metadata_dir,"trial3"))
        errs = self.valid8.test_metadata_tree(self.bag)
        self.assertEqual(len(errs.failed()), 3, "# of errors != 3: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-1b")
        self.assertEqual(errs.failed()[1].label, "4.1-4-1a")
        self.assertEqual(errs.failed()[2].label, "4.1-4-1b")

        os.mkdir(os.path.join(self.bag.data_dir, ".secret"))
        errs = self.valid8.test_metadata_tree(self.bag)
        self.assertEqual(len(errs.failed()), 4, "# of errors != 4: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertTrue(has_error(errs, "4.1-4-1a"))
        self.assertTrue(has_error(errs, "4.1-4-1b"))
        self.assertTrue(has_error(errs, "4.1-4-5"))
        
    def test_test_nerdm_validity(self):
        errs = self.valid8.test_nerdm_validity(self.bag)
        self.assertEqual(errs.failed(), [],
                      "False Positives: "+ str([str(e) for e in errs.failed()]))

        # set incorrect filepath
        mdf = os.path.join(self.bag.metadata_dir, "trial1.json", "nerdm.json")
        with open(mdf) as fd:
            gooddata = json.load(fd, object_pairs_hook=OrderedDict)
        data = OrderedDict(gooddata)
        data['filepath'] = "goober/gurn"
        with open(mdf,'w') as fd:
            json.dump(data, fd, indent=2, separators=(',', ': '))

        errs = self.valid8.test_nerdm_validity(self.bag)
        self.assertEqual(len(errs.failed()), 1, "# of errors != 1: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-2f")
        
        # give data file wrong @type
        data = OrderedDict(gooddata)
        data['@type'] = ["nerdm:GooberMan"]
        with open(mdf,'w') as fd:
            json.dump(data, fd, indent=2, separators=(',', ': '))

        errs = self.valid8.test_nerdm_validity(self.bag)
        self.assertEqual(len(errs.failed()), 1, "# of errors != 1: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-2c")

        # give subcollection wrong @type
        mdf = os.path.join(self.bag.metadata_dir, "trial3", "nerdm.json")
        with open(mdf) as fd:
            gooddata2 = json.load(fd, object_pairs_hook=OrderedDict)
        data = OrderedDict(gooddata2)
        data['@type'] = ["nerdm:GooberMan"]
        with open(mdf,'w') as fd:
            json.dump(data, fd, indent=2, separators=(',', ': '))

        errs = self.valid8.test_nerdm_validity(self.bag)
        self.assertEqual(len(errs.failed()), 2, "# of errors != 2: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-2c")
        self.assertEqual(errs.failed()[1].label, "4.1-4-2d")

        # make metadata invalid
        data['filepath'] = [ data['filepath'] ]
        with open(mdf,'w') as fd:
            json.dump(data, fd, indent=2, separators=(',', ': '))

        errs = self.valid8.test_nerdm_validity(self.bag)
        self.assertEqual(len(errs.failed()), 4, "# of errors != 4: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-2c")
        self.assertEqual(errs.failed()[1].label, "4.1-4-2f")
        self.assertEqual(errs.failed()[2].label, "4.1-4-2d")
        self.assertEqual(errs.failed()[3].label, "4.1-4-2b")

        # make metadata not legal
        with open(mdf,'w') as fd:
            fd.write('{["filepath": '+str(data['filepath'])+']}')

        errs = self.valid8.test_nerdm_validity(self.bag)
        self.assertEqual(len(errs.failed()), 2, "# of errors != 2: [\n  " +
                         "\n  ".join([str(e) for e in errs.failed()]) + "\n]")
        self.assertEqual(errs.failed()[0].label, "4.1-4-2c")
        self.assertEqual(errs.failed()[1].label, "4.1-4-2a")

        
        
        

if __name__ == '__main__':
    test.main()
