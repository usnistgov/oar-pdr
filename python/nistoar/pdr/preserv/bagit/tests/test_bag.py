import os, sys, pdb, shutil, logging, json, subprocess
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.tests import *
import nistoar.pdr.preserv.bagit.bag as bag
import nistoar.pdr.preserv.exceptions as exceptions

# datadir = nistoar/preserv/tests/data
datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "tests", "data"
)
bagdir = os.path.join(datadir, "metadatabag")

class TestNISTBag(test.TestCase):

    def setUp(self):
        self.bag = bag.NISTBag(bagdir)

    def tearDown(self):
        self.bag = None

    def test_ctor(self):
        self.assertEqual(self.bag.dir, bagdir)
        self.assertEqual(self.bag.name, "metadatabag")
        self.assertEqual(self.bag.data_dir, os.path.join(bagdir, "data"))
        self.assertEqual(self.bag.metadata_dir, os.path.join(bagdir, "metadata"))
        self.assertEqual(self.bag.pod_file(),
                         os.path.join(bagdir, "metadata", "pod.json"))

    def test_nerd_file_for(self):
        self.assertEqual(self.bag.nerd_file_for(""),
                         os.path.join(bagdir, "metadata", "nerdm.json"))
        self.assertEqual(self.bag.nerd_file_for("trial1.json"),
                         os.path.join(bagdir, "metadata", "trial1.json",
                                      "nerdm.json"))
        self.assertEqual(self.bag.nerd_file_for("trial2.json"),
                         os.path.join(bagdir, "metadata", "trial2.json",
                                      "nerdm.json"))
        self.assertEqual(self.bag.nerd_file_for("trial3"),
                         os.path.join(bagdir, "metadata", "trial3",
                                      "nerdm.json"))
        self.assertEqual(self.bag.nerd_file_for("trial3/trial3a.json"),
                         os.path.join(bagdir, "metadata", "trial3", 
                                      "trial3a.json", "nerdm.json"))
        
    def test_nerd_metadata_for(self):
        data = self.bag.nerd_metadata_for("")
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertNotIn("inventory", data)

        data = self.bag.nerd_metadata_for("trial3/trial3a.json")
        self.assertIn("@type", data)
        self.assertIn("nrdp:DataFile", data['@type'])

    def test_nerdm_record(self):
        data = self.bag.nerdm_record()
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)

        self.assertEqual(len(data['components']), 5)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 4)
        self.assertEqual(data['inventory'][0]['descCount'], 5)
        


if __name__ == '__main__':
    test.main()
