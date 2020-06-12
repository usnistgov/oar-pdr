# These unit tests test the nistoar.pdr.publish.mdserv.serv module.  These tests
# do not include support for accessing metadata that represent an update to a 
# previously published dataset (via use of the UpdatePrepService class).  
# Because testing support for updates require simulated RMM and distribution 
# services to be running, they have been seperated out into test_serv_update.py.
#
import os, sys, pdb, shutil, logging, json, time, signal
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
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.publish.mdserv.serv as serv
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.utils import read_nerd, write_json

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')
# datadir = nistoar/preserv/tests/data
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")
jqlibdir = def_jq_libdir
schemadir = os.path.join(os.path.dirname(jqlibdir), "model")
if not os.path.exists(schemadir) and os.environ.get('OAR_HOME'):
    schemadir = os.path.join(os.environ['OAR_HOME'], "etc", "schemas")
basedir = os.path.dirname(os.path.dirname(os.path.dirname(
                                                 os.path.dirname(pdrmoddir))))
distarchdir = os.path.join(pdrmoddir, "distrib", "data")
descarchdir = os.path.join(pdrmoddir, "describe", "data")

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
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
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

def to_dict(odict):
    out = dict(odict)
    for prop in out:
        if isinstance(out[prop], OrderedDict):
            out[prop] = to_dict(out[prop])
        if isinstance(out[prop], (list, tuple)):
            for i in range(len(out[prop])):
                if isinstance(out[prop][i], OrderedDict):
                    out[prop][i] = to_dict(out[prop][i])
    return out

class TestPrePubMetadataService(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def assertEqualOD(self, od1, od2, message=None):
        d1 = to_dict(od1)
        d2 = to_dict(od2)
        self.assertEqual(d1, od2, message)
    
    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("mdserv")
        self.bagparent = self.workdir
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.pubcache = self.tf.mkdir("headcache")
        
        self.config = {
            'working_dir':     self.workdir,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.workdir
        }
        self.srv = serv.PrePubMetadataService(self.config)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        if not midas.MIDASMetadataBagger._AsyncFileExaminer.wait_for_all():
            raise RuntimeError("Trouble waiting for file examiner threads")
        self.srv = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEquals(self.srv.workdir, self.workdir)
        self.assertEquals(self.srv.uploaddir, self.upldir)
        self.assertEquals(self.srv.reviewdir, self.revdir)
        self.assertEquals(os.path.dirname(self.srv._minter.registry.store),
                          self.workdir)

        self.assertIsNone(self.srv.prepsvc)  # update support turned off

    def test_normalize_id(self):
        self.assertEqual(self.midasid, self.srv.normalize_id(self.midasid))
        self.assertEqual(self.arkid, self.srv.normalize_id(self.arkid))
        self.assertEqual(self.arkid, self.srv.normalize_id(self.arkid[11:]))

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
        self.assertNotIn("inventory", data)

        self.assertEqual(len(data['components']), 7)
        # self.assertEqual(data['inventory'][0]['forCollection'], "")
        # self.assertEqual(len(data['inventory']), 2)
        # self.assertEqual(data['inventory'][0]['childCount'], 5)
        # self.assertEqual(data['inventory'][0]['descCount'], 7)

        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == 'sim.json':
                    continue
                self.assertTrue(comp['downloadURL'].startswith('https://data.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/'),
                                "{0} does not start with https://data.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/".format(comp['downloadURL']))
        self.assertEquals(dlcount, 5)
        
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
        self.assertNotIn("inventory", data)

        self.assertEqual(len(data['components']), 7)
        # self.assertEqual(data['inventory'][0]['forCollection'], "")
        # self.assertEqual(len(data['inventory']), 2)
        # self.assertEqual(data['inventory'][0]['childCount'], 5)
        # self.assertEqual(data['inventory'][0]['descCount'], 7)
        
        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == 'sim.json':
                    continue
                self.assertTrue(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
        self.assertEquals(dlcount, 5)

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
        self.assertEquals(dlcount, 5)

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
        self.assertNotIn("inventory", data)
        self.assertIn("authors", data)
        self.assertEqual(data['ediid'], ediid)
        self.assertEqual(data['foo'], "bar")

        self.assertEqual(len(data['components']), 7)
        trial1 = [c for c in data['components']
                    if 'filepath' in c and c['filepath'] == "trial1.json"][0]
        self.assertIn('previewURL', trial1)
        self.assertTrue(trial1['previewURL'].endswith("trial1.json/preview"))
        
        
    def test_resolve_id(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        mdata = self.srv.resolve_id(self.midasid)
        self.assertIn("ediid", mdata)

        # just for testing purposes, a pdr_status property will appear
        # in the record if this dataset is an update to a previous
        # release.  
        self.assertNotIn("pdr_status", mdata)  

        loader = ejs.SchemaLoader.from_directory(schemadir)
        val = ejs.ExtValidator(loader, ejsprefix='_')
        val.validate(mdata, False, True)

        # resolve_id() is not indepodent with async file examination turned on!
        #
        ## resolve_id() needs to be indepodent
        #data = self.srv.resolve_id(self.midasid)
        #self.assertEqualOD(data, mdata)

        with self.assertRaises(serv.IDNotFound):
            self.srv.resolve_id("asldkfjsdalfk")

    def test_resolve_arkid(self):
        indir = os.path.join(self.workdir, os.path.basename(self.testsip))
        shutil.copytree(self.testsip, indir)
        self.upldir = os.path.join(indir, "upload")
        self.revdir = os.path.join(indir, "review")

        podf = os.path.join(self.upldir,"1491","_pod.json")
        with open(podf) as fd:
            pod = json.load(fd)
        pod['identifier'] = self.arkid
        with open(podf, 'w') as fd:
            json.dump(pod, fd, indent=2)
        podf = os.path.join(self.revdir,"1491","_pod.json")
        with open(podf, 'w') as fd:
            json.dump(pod, fd, indent=2)

        self.config = {
            'working_dir':     self.workdir,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.workdir,
            'bagger': {
                'bag_builder': { 'validate_id': r'(pdr\d)|(mds[01])' }
            }
        }
        self.srv = serv.PrePubMetadataService(self.config)
        self.bagdir = os.path.join(self.bagparent, self.arkid[11:])

        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(metadir))

        mdata = self.srv.resolve_id(self.arkid)
        self.assertIn("ediid", mdata)
        self.assertEquals(mdata['ediid'], self.arkid)
        self.assertEquals(mdata['@id'], self.arkid)

        # just for testing purposes, a pdr_status property will appear
        # in the record if this dataset is an update to a previous
        # release.  
        self.assertNotIn("pdr_status", mdata)  

        loader = ejs.SchemaLoader.from_directory(schemadir)
        val = ejs.ExtValidator(loader, ejsprefix='_')
        val.validate(mdata, False, True)

        # resolve_id() is not indepodent with async file examination turned on!
        #
        ## resolve_id() needs to be indepodent
        #data = self.srv.resolve_id(self.arkid)
        #self.assertEqualOD(data, mdata)

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
