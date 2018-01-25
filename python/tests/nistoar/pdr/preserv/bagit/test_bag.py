import os, sys, pdb, shutil, logging, json, subprocess
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.bag as bag
import nistoar.pdr.preserv.bagit.exceptions as bagex
import nistoar.pdr.exceptions as exceptions

# datadir = nistoar/pdr/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )
bagdir = os.path.join(datadir, "samplembag")

baghier = [
    {
        "filepath": "trial1.json"
    },
    {
        "filepath": "trial2.json"
    },
    {
        "filepath": "trial3",
        "children": [
            {
                "filepath": "trial3/trial3a.json"
            }
        ]
    }
]

class TestNISTBag(test.TestCase):

    def setUp(self):
        self.bag = bag.NISTBag(bagdir)

    def tearDown(self):
        self.bag = None

    def test_ctor(self):
        self.assertEqual(self.bag.dir, bagdir)
        self.assertEqual(self.bag.name, "samplembag")
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

    def test_nerdm_component(self):
        data = self.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertEqual(data['filepath'], 'trial3/trial3a.json')
        self.assertEqual(data['mediaType'], "application/json")

        with self.assertRaises(bagex.ComponentNotFound):
            self.bag.nerd_metadata_for('goober')
        
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

        # FIX: order is significant!
        #
        # self.assertEqual(data['dataHierarchy'], baghier)
        #
        self.assertEqual(len(data['dataHierarchy']), len(baghier))
        for comp in data['dataHierarchy']:
            self.assertIn(comp, baghier)

    def test_comp_exists(self):
        self.assertTrue( self.bag.comp_exists("trial1.json") )
        self.assertTrue( self.bag.comp_exists("trial2.json") )
        self.assertTrue( self.bag.comp_exists("trial3") )
        self.assertTrue( self.bag.comp_exists("trial3/trial3a.json") )
        self.assertFalse( self.bag.comp_exists("trial4") )

    def test_is_data_file(self):
        self.assertTrue( self.bag.is_data_file("trial1.json") )
        self.assertTrue( self.bag.is_data_file("trial2.json") )
        self.assertFalse( self.bag.is_data_file("trial3") )
        self.assertTrue( self.bag.is_data_file("trial3/trial3a.json") )
        self.assertFalse( self.bag.is_data_file("trial4") )

    def test_is_subcoll(self):
        self.assertFalse( self.bag.is_subcoll("trial1.json") )
        self.assertFalse( self.bag.is_subcoll("trial2.json") )
        self.assertTrue( self.bag.is_subcoll("trial3") )
        self.assertFalse( self.bag.is_subcoll("trial3/trial3a.json") )
        self.assertFalse( self.bag.is_subcoll("trial4") )

        self.assertTrue( self.bag.is_subcoll("") )

    def test_subcoll_children(self):
        # pdb.set_trace()
        children = self.bag.subcoll_children("")
        self.assertEqual(len(children), 3)
        for child in "trial1.json trial2.json trial3".split():
            self.assertIn(child, children)

        children = self.bag.subcoll_children("trial3")
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], "trial3a.json")

        with self.assertRaises(bag.BadBagRequest):
            self.bag.subcoll_children("trial1.json")
        with self.assertRaises(bag.BadBagRequest):
            self.bag.subcoll_children("trial4")

    def test_iter_fetch_records(self):
        fdata = [t for t in self.bag.iter_fetch_records()]
        self.assertEqual(len(fdata), 3)
        self.assertEqual(len([i[0] for i in fdata
                                  if i[0].startswith('http://example.org/')]), 3)
        self.assertEqual(len([i[1] for i in fdata if int(i[1])]), 3)
        self.assertEqual(fdata[0][2], "data/trial1.json")
        self.assertEqual(fdata[1][2], "data/trial2.json")
        self.assertEqual(fdata[2][2], "data/trial3/trial3a.json")

    def test_get_baginfo(self):
        data = self.bag.get_baginfo()

        self.assertEqual(len(data.keys()), 17)
        for key in ["Source-Organization", "Organization-Address",
                    "External-Description", "Bag-Count"]:
            self.assertIn(key, data)

        self.assertEqual(len([data[k] for k in data
                                      if not isinstance(data[k], list)]), 0)
        for k in [ "Organization-Address", "External-Description", "Bag-Count"]:
            self.assertEqual(len(data[k]), 1)
        self.assertEqual(len(data['Source-Organization']), 2)
        self.assertEqual(data['Source-Organization'],
                         [ "National Institute of Standards and Technology",
                           "Office of Data and Informatics" ])
        self.assertEqual(data['Organization-Address'],
                         [ "100 Bureau Drive, Mail Stop 1000, " +
                           "Gaithersburg, MD 20899" ])
        self.assertEqual(data['External-Description'],
                         [ "This is a test bag created for testing bag "+
                           "access.  It contains no data files, but it "+
                           "includes various other metadata files." ])
        self.assertEqual(data['Bag-Count'], [ "1 of 1" ])

    def test_bagit_version(self):
        self.assertEqual(self.bag.bagit_version, "0.97")
        self.assertEqual(self.bag.tag_encoding, "UTF-8")
    
    def test_tag_encoding(self):
        self.assertEqual(self.bag.tag_encoding, "UTF-8")
        self.assertEqual(self.bag.bagit_version, "0.97")

    def test_multibag_dir(self):
        self.assertEqual(self.bag.multibag_dir,
                         os.path.join(self.bag.dir,"multibag"))

    def test_is_headbag(self):
        self.assertTrue(self.bag.is_headbag())
                         
                         

if __name__ == '__main__':
    test.main()
