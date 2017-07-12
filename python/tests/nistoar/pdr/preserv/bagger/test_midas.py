import os, sys, pdb, shutil, logging, json
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.exceptions as exceptions

# datadir = nistoar/preserv/tests/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
#    logging.basicConfig(filename=os.path.join(tmpdir(),"test_builder.log"),
#                        level=logging.INFO)
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_builder.log"))
    loghdlr.setLevel(logging.INFO)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestMIDASMetadataBaggerMixed(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, self.upldir)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "review")
        self.assertEqual(len(self.bagr._indirs), 2)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.revdir, self.midasid))
        self.assertEqual(self.bagr._indirs[1],
                         os.path.join(self.upldir, self.midasid))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))
        self.assertFalse(os.path.exists(self.bagdir))

    def test_find_pod_file(self):
        self.assertEqual(self.bagr.find_pod_file(),
                         os.path.join(self.upldir,self.midasid,'_pod.json'))
        self.assertIsNone(self.bagr.inpodfile)

    def test_set_pod_file(self):
        self.assertIsNone(self.bagr.inpodfile)
        self.bagr._set_pod_file()
        self.assertEqual(self.bagr.inpodfile,
                         os.path.join(self.upldir,self.midasid,'_pod.json'))

    def test_ensure_res_metadata(self):
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.inpodfile)
        
        self.bagr.ensure_res_metadata()
        
        self.assertTrue(os.path.exists(self.bagdir))
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertTrue(os.path.exists(metadir))
        self.assertTrue(os.path.exists(os.path.join(metadir, "pod.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir, "nerdm.json")))
        self.assertEqual(self.bagr.inpodfile,
                         os.path.join(self.upldir, self.midasid, "_pod.json"))

        data = midas.read_pod(os.path.join(metadir, "pod.json"))
        self.assertIsInstance(data, OrderedDict)
        src = midas.read_pod(self.bagr.inpodfile)
        self.assertEqual(data, src)
        self.assertEqual(data.keys(), src.keys())  # confirms same order

        self.assertIsNotNone(self.bagr.resmd)
        data = midas.read_nerd(os.path.join(metadir, "nerdm.json"))
        self.assertEqual(len(data['components']), 1)
        self.assertIsInstance(data, OrderedDict)
        self.assertNotIn('inventory', data)
        src = deepcopy(self.bagr.resmd)
        del data['components']
        del src['components']
        del src['inventory']
        self.assertEqual(data, src)
        self.assertEqual(data.keys(), src.keys())  # same order

        # spot check some key NERDm properties
        data = self.bagr.resmd
        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertEqual(data['doi'], "doi:10.18434/T4SW26")
        self.assertEqual(len(data['components']), 4)
        self.assertEqual(data['components'][3]['@type'][0], 'nrd:Hidden')
        self.assertIsInstance(data['@context'], list)
        self.assertEqual(len(data['@context']), 2)
        self.assertEqual(data['@context'][1]['@base'], data['@id'])

    def test_data_file_inventory(self):
        uplsip = os.path.join(self.upldir, self.midasid)
        revsip = os.path.join(self.revdir, self.midasid)

        datafiles = self.bagr.data_file_inventory()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 3)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        # copy of trial3a.json in upload overrides
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))

    def test_ensure_file_metadata(self):
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.bagbldr.ediid)
        self.bagr.bagbldr.ediid = "gurn"

        destpath = os.path.join("trial3", "trial3a.json")
        dlurl = "https://www.nist.gov/od/ds/gurn/"+destpath
        dfile = os.path.join(self.upldir, self.midasid, destpath)
        self.bagr.ensure_file_metadata(dfile, destpath)

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))

        data = midas.read_nerd(mdfile)
        self.assertEqual(data['size'], 70)
        self.assertTrue(data['hash']['value'])
        self.assertEqual(data['downloadURL'], dlurl)
        self.assertNotIn('description', data)

    def test_ensure_file_metadata_resmd(self):
        self.assertFalse(os.path.exists(self.bagdir))

        self.bagr.ensure_res_metadata()

        destpath = os.path.join("trial3", "trial3a.json")
        dfile = os.path.join(self.upldir, self.midasid, destpath)
        self.bagr.ensure_file_metadata(dfile, destpath, self.bagr.resmd)

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))

        data = midas.read_nerd(mdfile)
        self.assertEqual(data['size'], 70)
        self.assertTrue(data['hash']['value'])
        self.assertTrue(data['downloadURL'])
        self.assertTrue(data['description'])

    def test_ensure_data_files(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        self.assertIsNotNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))
        
    def test_ensure_data_files_wremove(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        self.assertIsNotNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))

        self.bagr.bagbldr.init_filemd_for( os.path.join("gold","trial5.json"),
                                           write=True,
                                           examine=os.path.join(self.revdir,
                                                                self.midasid,
                                                                "trial1.json") )
        t5path = os.path.join( metadir,"gold","trial5.json","nerdm.json")
        self.assertTrue(os.path.exists(t5path))

        self.bagr.ensure_data_files()
        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))
        self.assertFalse(os.path.exists(t5path))
        
        
    def test_ensure_subcoll_metadata(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_subcoll_metadata()

        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        mdata = midas.read_nerd(mdfile)
        self.assertEqual(mdata['filepath'], "trial3")
        self.assertIn("nrdp:Subcollection", mdata['@type'])

    def test_ensure_preparation(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_preparation()

        # has resource-level metadata
        self.assertTrue(os.path.exists(os.path.join(metadir, "pod.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir, "nerdm.json")))

        # has file metadata
        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))

        # has subcollection metadata
        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        mdata = midas.read_nerd(mdfile)
        self.assertEqual(mdata['filepath'], "trial3")
        self.assertIn("nrdp:Subcollection", mdata['@type'])
        
    def test_ensure_preparation(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.prepare()
        self.assertTrue( os.path.exists(self.bagdir + ".lock") )
        
class TestMIDASMetadataBaggerReview(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.revdir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "review")
        self.assertEqual(len(self.bagr._indirs), 1)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.revdir, self.midasid))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))

    def test_find_pod_file(self):
        self.assertEquals(self.bagr.find_pod_file(),
                          os.path.join(self.revdir,self.midasid,'_pod.json'))

    def test_data_file_inventory(self):
        revsip = os.path.join(self.revdir, self.midasid)

        datafiles = self.bagr.data_file_inventory()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 3)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)

        # files are only found in the review area
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(revsip, "trial3/trial3a.json"))


class TestMIDASMetadataBaggerUpload(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              None, self.upldir)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "upload")
        self.assertEqual(len(self.bagr._indirs), 1)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.upldir, self.midasid))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))

    def test_find_pod_file(self):
        self.assertEquals(self.bagr.find_pod_file(),
                          os.path.join(self.upldir,self.midasid,'_pod.json'))

    def test_data_file_inventory(self):
        uplsip = os.path.join(self.upldir, self.midasid)

        datafiles = self.bagr.data_file_inventory()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 3)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)

        # files are only found in the upload area
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(uplsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(uplsip, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))




if __name__ == '__main__':
    test.main()
