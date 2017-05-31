import os, sys, pdb, shutil, logging, json
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy
import ejsonschema as ejs

from nistoar.testing import *
from nistoar.pdr import def_jq_libdir
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.publish.mdserv.serv as serv
import nistoar.pdr.exceptions as exceptions

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')
# datadir = nistoar/preserv/tests/data
pdrmoddir = os.path.dirname(os.path.dirname(os.path.dirname(testdir)))
datadir = os.path.join(pdrmoddir, "preserv", "tests", "data")
jqlibdir = def_jq_libdir
schemadir = os.path.join(os.path.dirname(jqlibdir), "model")

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

class TestPrePubMetadataService(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("publish")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        config = {
            'working_dir':     self.bagparent,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.bagparent
        }
        self.srv = serv.PrePubMetadataService(config)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.srv = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEquals(self.srv.workdir, self.bagparent)
        self.assertEquals(self.srv.uploaddir, self.upldir)
        self.assertEquals(self.srv.reviewdir, self.revdir)
        self.assertEquals(os.path.dirname(self.srv._minter.registry.store),
                          self.bagparent)

    def test_prepare_metadata_bag(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)

        self.assertTrue(os.path.exists(os.path.join(metadir, "pod.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir, "nerdm.json")))

        # has file metadata
        self.assertTrue(os.path.exists(metadir))
        datafiles = "trial1.json trial2.json trial3 trial3/trial3a.json".split()
        for filepath in datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))

        # has subcollection metadata
        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        
    def test_make_nerdm_record(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)
        self.assertTrue(os.path.exists(bagdir))

        data = self.srv.make_nerdm_record(bagdir)
        
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)

        self.assertEqual(len(data['components']), 5)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 4)
        self.assertEqual(data['inventory'][0]['descCount'], 5)

        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                self.assertTrue(comp['downloadURL'].startswith('https://www.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/'))
        self.assertEquals(dlcount, 3)
        
    def test_make_nerdm_record_cvt_dlurls(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)
        self.assertTrue(os.path.exists(bagdir))

        data = self.srv.make_nerdm_record(bagdir,
                                          baseurl='https://mdserv.nist.gov/')
        
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)

        self.assertEqual(len(data['components']), 5)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 4)
        self.assertEqual(data['inventory'][0]['descCount'], 5)
        
        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                self.assertTrue(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
        self.assertEquals(dlcount, 3)
        
    def test_resolve_id(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        mdata = self.srv.resolve_id(self.midasid)

        loader = ejs.SchemaLoader.from_directory(schemadir)
        val = ejs.ExtValidator(loader, ejsprefix='_')
        val.validate(mdata, False, True)

        data = self.srv.resolve_id(self.midasid)
        self.assertEqual(data, mdata)

        with self.assertRaises(serv.SIPDirectoryNotFound):
            self.srv.resolve_id("asldkfjsdalfk")

    def test_locate_data_file(self):
        loc = self.srv.locate_data_file(self.midasid, 'trial3/trial3a.json')
        self.assertEquals(len(loc), 2)
        self.assertEquals(loc[0], os.path.join(self.upldir,self.midasid,
                                               'trial3/trial3a.json'))
        self.assertEquals(loc[1], "application/json")

        loc = self.srv.locate_data_file(self.midasid, 'trial1.json')
        self.assertEquals(len(loc), 2)
        self.assertEquals(loc[0], os.path.join(self.revdir,self.midasid,
                                               'trial1.json'))
        self.assertEquals(loc[1], "application/json")

    def test_no_locate_data_file(self):
        loc = self.srv.locate_data_file(self.midasid, 'goober/trial3a.json')
        self.assertEquals(len(loc), 2)
        self.assertIsNone(loc[0])
        self.assertIsNone(loc[1])

class TestMimeTypeLoading(test.TestCase):

    def test_defaults(self):

        self.assertEquals(serv.def_ext2mime['json'], "application/json")
        self.assertEquals(serv.def_ext2mime['txt'], "text/plain")
        self.assertEquals(serv.def_ext2mime['xml'], "text/xml")

    def test_update_mimetypes_from_file(self):
        map = serv.update_mimetypes_from_file(None,
                                  os.path.join(testdatadir, "nginx-mime.types"))
        self.assertEquals(map['mml'], "text/mathml")
        self.assertEquals(map['jpg'], "image/jpeg")
        self.assertEquals(map['jpeg'], "image/jpeg")

        map = serv.update_mimetypes_from_file(map,
                                  os.path.join(testdatadir, "comm-mime.types"))
        self.assertEquals(map['zip'], "application/zip")
        self.assertEquals(map['xml'], "application/xml")
        self.assertEquals(map['xsd'], "application/xml")
        self.assertEquals(map['mml'], "text/mathml")
        self.assertEquals(map['jpg'], "image/jpeg")
        self.assertEquals(map['jpeg'], "image/jpeg")

    def test_build_mime_type_map(self):
        map = serv.build_mime_type_map([])
        self.assertEquals(map['txt'], "text/plain")
        self.assertEquals(map['xml'], "text/xml")
        self.assertEquals(map['json'], "application/json")
        self.assertNotIn('mml', map)
        self.assertNotIn('xsd', map)
        
        map = serv.build_mime_type_map(
            [os.path.join(testdatadir, "nginx-mime.types"),
             os.path.join(testdatadir, "comm-mime.types")])
        self.assertEquals(map['txt'], "text/plain")
        self.assertEquals(map['mml'], "text/mathml")
        self.assertEquals(map['xml'], "application/xml")
        self.assertEquals(map['xsd'], "application/xml")
        
        

if __name__ == '__main__':
    test.main()
