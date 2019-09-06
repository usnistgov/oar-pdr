# These unit tests test the nistoar.pdr.publish.mdserv.serv module, specifically
# the support for user updates to metadata
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
import nistoar.pdr.preserv.bagit as bagit
import nistoar.pdr.preserv.bagit.bag
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.publish.mdserv.serv as serv
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.utils import read_nerd, write_json
from nistoar.nerdm import CORE_SCHEMA_URI, PUB_SCHEMA_URI

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

simsrvrsrc = os.path.join(testdir, "sim_midas_srv.py")
port = 9091
baseurl = "http://localhost:{0}/".format(port)

def startService(archdir, authmeth=None):
    srvport = port
    if authmeth == 'header':
        srvport += 1
    tdir = os.path.dirname(archdir)
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3} --set-ph archive_dir={4} " 
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(simsrvrsrc), pidfile, archdir)
    os.system(cmd)

def stopService(archdir, authmeth=None):
    srvport = port
    pidfile = os.path.join(os.path.dirname(archdir),"simsrv"+str(srvport)+".pid")
    cmd = "uwsgi --stop {0}".format(pidfile)
    os.system(cmd)
    time.sleep(1)


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

class TestPrePubMetadataServiceUpdates(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

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
            'id_registry_dir': self.workdir,
            'update': {
                'updatable_properties': [ 'title', 'components[].goob' ]
            }
        }
        self.srv = serv.PrePubMetadataService(self.config)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        if not midas.MIDASMetadataBagger._AsyncFileExaminer.wait_for_all():
            raise RuntimeError("Trouble waiting for file examiner threads")
        self.srv = None
        self.tf.clean()

    def test_ctor(self):
        self.assertIsNone(self.srv._midascl)

    def test_item_with_id(self):
        ary = [
            {'@id': 'a1', "a": "b1"},
            {'@id': 'a2', "a": "b2"},
            {'@id': 'a3', "a": "b3"},
            {'@id': 'a4', "a": "b4"}
        ]
        self.assertEqual(self.srv._item_with_id(ary, 'a3'),
                         {'@id': 'a3', "a": "b3"})
        self.assertEqual(self.srv._item_with_id(ary, 'a4'),
                         {'@id': 'a4', "a": "b4"})
        self.assertEqual(self.srv._item_with_id(ary, 'a1'),
                         {'@id': 'a1', "a": "b1"})

    def test_pod4midas(self):
        self.srv.resolve_id(self.midasid)
        bagdir = os.path.join(self.config['working_dir'], self.midasid)
        bag = bagit.bag.NISTBag(bagdir)
        pod = self.srv._pod4midas(bag.pod_record())
        # self.assertNotIn('identifier', pod)

    def test_validate_nerdm(self):
        bagdir = os.path.join(self.config['working_dir'], self.midasid)
        nerdm = self.srv.resolve_id(self.midasid)

        errs = self.srv._validate_nerdm(nerdm, {})
        self.assertEqual(errs, [])

        nerdm['title'] = 3
        errs = self.srv._validate_nerdm(nerdm, {})
        self.assertGreater(len(errs), 0)
        
    def test_update_pod(self):
        bagdir = os.path.join(self.config['working_dir'], self.midasid)
        nerdm = self.srv.resolve_id(self.midasid)

        bbldr = bagit.builder.BagBuilder(self.config['working_dir'],
                                         self.midasid, {})
        nerdm['title'] = "Goober!"
        self.srv.update_pod(nerdm, bbldr)

        self.assertEqual(bbldr.bag.pod_record()['title'], "Goober!")

    def test_validate_update(self):
        nerdm = self.srv.resolve_id(self.midasid)
        bbldr = bagit.builder.BagBuilder(self.config['working_dir'],
                                         self.midasid, {})

        updata = {
            'title': "Goober!",
            'custom': 'data',
            'authors': [],
            'components': [
                {
                    "@id": "cmps/trial1.json",
                    "goob": "gurn",
                    "title": "Trial 1"
                }
            ]
        }

        updated = self.srv._validate_update(updata, nerdm, bbldr)
        self.assertEqual(updated['title'], "Goober!")
        self.assertEqual(updated['authors'], [])
        self.assertEqual(updated['custom'], "data")
        self.assertEqual(updated['description'], nerdm['description'])
        self.assertEqual(updated['bureauCode'], nerdm['bureauCode'])
        self.assertEqual(len(updated['components']), len(nerdm['components']))
        ucmp = self.srv._item_with_id(updated['components'], "cmps/trial1.json")
        self.assertEqual(ucmp['title'], "Trial 1")
        self.assertEqual(ucmp['filepath'], "trial1.json")
        self.assertEqual(ucmp['goob'], "gurn")

        with self.assertRaises(serv.InvalidRequest):
            self.srv._validate_update({'title': 3}, nerdm, bbldr)

    def test_filter_and_check_updates(self):
        self.srv.resolve_id(self.midasid)
        bbldr = bagit.builder.BagBuilder(self.config['working_dir'],
                                         self.midasid, {})

        updata = {
            'title': "Goober!",
            'custom': 'data',
            'authors': [],
            'components': [
                {
                    "@id": "cmps/trial1.json",
                    "goob": "gurn",
                    "title": "Trial 1"
                }
            ]
        }

        updated = self.srv._filter_and_check_updates(updata, bbldr)
        self.assertIn('', updated)
        self.assertIn('trial1.json', updated)
        self.assertEqual(updated['']['title'], "Goober!")
        self.assertNotIn('custom', updated[''])
        self.assertNotIn('authors', updated[''])
        self.assertNotIn('title', updated['trial1.json'])
        self.assertEqual(updated['trial1.json']['goob'], "gurn")

    def test_patch_id(self):
        bagdir = os.path.join(self.config['working_dir'], self.midasid)
        updata = {
            'title': "Goober!",
            'custom': 'data',
            'authors': [],
            'components': [
                {
                    "@id": "cmps/trial1.json",
                    "goob": "gurn",
                    "title": "Trial 1"
                }
            ]
        }

        updated = self.srv.patch_id(self.midasid, {'title': 'Big!'})
        self.assertEqual(updated['title'], 'Big!')
        self.assertIn('bureauCode', updated)
        self.assertIn('description', updated)
        self.assertIn('components', updated)
        self.assertEqual(len(updated['components']), 7)

        bag = bagit.bag.NISTBag(bagdir)
        nerdm = bag.nerdm_record(True)
        self.assertTrue(updated == nerdm, "Updated and cached NERDm not the same")

        nerdm = self.srv.resolve_id(self.midasid)
        self.assertTrue(updated == nerdm, "Updated and resolved NERDm not the same")

        updated = self.srv.patch_id(self.midasid, updata)
        self.assertEqual(updated['title'], 'Goober!')
        self.assertEqual(updated['bureauCode'], nerdm['bureauCode'])
        self.assertEqual(updated['description'], nerdm['description'])
        self.assertIn('components', updated)
        self.assertEqual(len(updated['components']), 7)
        
        ucmp = self.srv._item_with_id(updated['components'], "cmps/trial1.json")
        ncmp = self.srv._item_with_id(nerdm['components'], "cmps/trial1.json")
        self.assertEqual(ucmp['title'], ncmp['title'])
        self.assertEqual(ucmp['filepath'], "trial1.json")
        self.assertEqual(ucmp['goob'], "gurn")
        self.assertNotIn('goob', ncmp)
        

class TestPrePubMetadataServiceMidas(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"
    svcarch = None

    @classmethod
    def setUpClass(cls):
        cls.svcarch = os.path.join(tmpdir(), "simarch")
        if not os.path.exists(cls.svcarch):
            os.mkdir(cls.svcarch)
        startService(cls.svcarch)

    @classmethod
    def tearDownClass(cls):
        stopService(cls.svcarch)

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("mdserv")
        self.bagparent = self.workdir
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.pubcache = self.tf.mkdir("headcache")
        
        shutil.copyfile(os.path.join(datadir, "pdr2210_pod.json"),
                        os.path.join(self.svcarch, "pdr2210.json"))
        shutil.copyfile(os.path.join(self.revdir, "1491", "_pod.json"),
                        os.path.join(self.svcarch, self.midasid+".json"))

        self.config = {
            'working_dir':     self.workdir,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.workdir,
            'update': {
                'updatable_properties': [ 'title', 'components[].goob' ],
                'midas_service': {
                    'service_endpoint': baseurl,
                    'auth_key': 'svcsecret'
                }
            }
        }
        self.srv = serv.PrePubMetadataService(self.config)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        if not midas.MIDASMetadataBagger._AsyncFileExaminer.wait_for_all():
            raise RuntimeError("Trouble waiting for file examiner threads")
        self.srv = None
        self.tf.clean()

    def test_ctor(self):
        self.assertIsNotNone(self.srv._midascl)
        self.assertTrue(self.srv._midascl._authkey)
        self.assertEqual(self.srv._midascl.baseurl, baseurl)

    def test_midas_update(self):
        bagdir = os.path.join(self.config['working_dir'], self.midasid)
        updata = {
            'title': "Goober!",
            'custom': 'data',
            'authors': [],
            'components': [
                {
                    "@id": "cmps/trial1.json",
                    "goob": "gurn",
                    "title": "Trial 1"
                }
            ]
        }

        # test open assumption
        with open(os.path.join(self.svcarch, self.midasid+".json")) as fd:
            midaspod = json.load(fd)
        self.assertNotEqual(midaspod['title'], 'Big!')

        updated = self.srv.patch_id(self.midasid, {'title': 'Big!'})
        self.assertEqual(updated['title'], 'Big!')
        with open(os.path.join(self.svcarch, self.midasid+".json")) as fd:
            midaspod = json.load(fd)
        self.assertEqual(midaspod['title'], 'Big!')

        updated = self.srv.patch_id(self.midasid, updata)
        self.assertEqual(updated['title'], 'Goober!')
        with open(os.path.join(self.svcarch, self.midasid+".json")) as fd:
            midaspod = json.load(fd)
        self.assertEqual(midaspod['title'], 'Goober!')
        for dist in midaspod['distribution']:
            self.assertNotIn('goob', dist)
        

if __name__ == '__main__':
    test.main()
