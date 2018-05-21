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
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")
jqlibdir = def_jq_libdir
schemadir = os.path.join(os.path.dirname(jqlibdir), "model")
if not os.path.exists(schemadir) and os.environ.get('OAR_HOME'):
    schemadir = os.path.join(os.environ['OAR_HOME'], "etc", "schemas")

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
        self.workdir = self.tf.mkdir("mdserv")
        self.bagparent = self.workdir
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        config = {
            'working_dir':     self.workdir,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.workdir
        }
        self.srv = serv.PrePubMetadataService(config)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.srv = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEquals(self.srv.workdir, self.workdir)
        self.assertEquals(self.srv.uploaddir, self.upldir)
        self.assertEquals(self.srv.reviewdir, self.revdir)
        self.assertEquals(os.path.dirname(self.srv._minter.registry.store),
                          self.workdir)

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

        self.assertEqual(len(data['components']), 8)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 6)
        self.assertEqual(data['inventory'][0]['descCount'], 8)

        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == 'sim.json':
                    continue
                self.assertTrue(comp['downloadURL'].startswith('https://data.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/'),
                                "{0} does not start with https://data.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/".format(comp['downloadURL']))
        self.assertEquals(dlcount, 6)
        
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

        self.assertEqual(len(data['components']), 8)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 6)
        self.assertEqual(data['inventory'][0]['descCount'], 8)
        
        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == 'sim.json':
                    continue
                self.assertTrue(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
        self.assertEquals(dlcount, 6)

        datafiles = { "trial1.json": "blah/blah/trial1.json" }
        data = self.srv.make_nerdm_record(bagdir, datafiles, 
                                          baseurl='https://mdserv.nist.gov/')

        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == "trial1.json":
                    self.assertTrue(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
                else:
                    self.assertFalse(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
        self.assertEquals(dlcount, 6)

    def test_make_nerdm_record_withannots(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)
        self.assertTrue(os.path.exists(bagdir))

        data = self.srv.make_nerdm_record(bagdir)
        self.assertNotIn("authors", data)
        trial1 = [c for c in data['components']
                    if 'filepath' in c and c['filepath'] == "trial1.json"][0]
        self.assertNotIn('previewURL', trial1)
        ediid = data['ediid']
        
        # copy in some annotation files
        otherbag = os.path.join(datadir, "metadatabag")
        annotpath = os.path.join("metadata", "annot.json")
        self.assertTrue(os.path.exists(os.path.join(otherbag, annotpath)))
        shutil.copyfile(os.path.join(otherbag, annotpath),
                        os.path.join(self.bagdir, annotpath))
        self.assertTrue(os.path.exists(os.path.join(self.bagdir, annotpath)))
        annotpath = os.path.join("metadata", "trial1.json", "annot.json")
        self.assertTrue(os.path.exists(os.path.join(otherbag, annotpath)))
        shutil.copyfile(os.path.join(otherbag, annotpath),
                        os.path.join(self.bagdir, annotpath))
        self.assertTrue(os.path.exists(os.path.join(self.bagdir, annotpath)))

        data = self.srv.make_nerdm_record(bagdir)
        
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)
        self.assertIn("authors", data)
        self.assertEqual(data['ediid'], ediid)
        self.assertEqual(data['foo'], "bar")

        self.assertEqual(len(data['components']), 8)
        trial1 = [c for c in data['components']
                    if 'filepath' in c and c['filepath'] == "trial1.json"][0]
        self.assertIn('previewURL', trial1)
        self.assertTrue(trial1['previewURL'].endswith("trial1.json/preview"))
        
        
    def test_resolve_id(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        mdata = self.srv.resolve_id(self.midasid)

        loader = ejs.SchemaLoader.from_directory(schemadir)
        val = ejs.ExtValidator(loader, ejsprefix='_')
        val.validate(mdata, False, True)

        # resolve_id() needs to be indepodent
        data = self.srv.resolve_id(self.midasid)
        self.assertEqual(data, mdata)

        with self.assertRaises(serv.SIPDirectoryNotFound):
            self.srv.resolve_id("asldkfjsdalfk")

    def test_locate_data_file(self):
        loc = self.srv.locate_data_file(self.midasid, 'trial3/trial3a.json')
        self.assertEquals(len(loc), 2)
        self.assertEquals(loc[0], os.path.join(self.upldir,self.midasid[32:],
                                               'trial3/trial3a.json'))
        self.assertEquals(loc[1], "application/json")

        loc = self.srv.locate_data_file(self.midasid, 'trial1.json')
        self.assertEquals(len(loc), 2)
        self.assertEquals(loc[0], os.path.join(self.revdir,self.midasid[32:],
                                               'trial1.json'))
        self.assertEquals(loc[1], "application/json")

    def test_no_locate_data_file(self):
        loc = self.srv.locate_data_file(self.midasid, 'goober/trial3a.json')
        self.assertEquals(len(loc), 2)
        self.assertIsNone(loc[0])
        self.assertIsNone(loc[1])

        
        

if __name__ == '__main__':
    test.main()
