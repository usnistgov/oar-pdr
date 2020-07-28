from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib, shutil
from collections import Mapping
import unittest as test

from nistoar.testing import *
import nistoar.pdr.doimint as dm
from nistoar.pdr.utils import read_nerd, read_json
from nistoar.pdr.exceptions import NERDError, ConfigurationException
from nistoar.nerdm import constants as nerdconst

port = 9091
baseurl = "http://localhost:{0}/dois".format(port)
prefixes = ["10.88434", "20.88434"]

pdrdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(pdrdir, "describe", "data")
tstnerd = os.path.join(datadir, "pdr2210.json")

basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(pdrdir))))
ormdir = os.path.join(basedir, "oar-metadata")
mocksvr = os.path.join(ormdir, "python", "nistoar", "doi", "tests", "sim_datacite_srv.py")

def startService():
    tdir = tmpdir()
    srvport = port
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    wpy = "python/nistoar/doi/tests/sim_datacite_srv.py"
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3} --set-ph prefixes={4}"
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport, mocksvr,
                     pidfile, ",".join(prefixes))
    os.system(cmd)
    time.sleep(0.2)

def stopService():
    tdir = tmpdir()
    srvport = port
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                                 "simsrv"+str(srvport)+".pid"))
    os.system(cmd)
    time.sleep(1)

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_doimint.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)
#    startService()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
#    stopService()
    shutil.rmtree(tmpdir())

class TestDOIMintingClientQuiet(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("doimint")
        self.cfg = {
            'minting_naan':  prefixes[1],
            'jq_lib': os.path.join(ormdir, "jq"),
            'data_dir':  self.workdir
        }
        self.dmcli = dm.DOIMintingClient(self.cfg)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertIsNone(self.dmcli.dccli)
        self.assertIsNotNone(self.dmcli.log)
        self.assertIsNotNone(self.dmcli._jqt)
        self.assertEqual(self.dmcli.naan, prefixes[1])
        self.assertTrue(self.dmcli._publish_by_default)
        for dirn in "inprogress staging published reserved failed".split():
            ddir = os.path.join(self.workdir, dirn)
            self.assertTrue(os.path.isdir(ddir), "Data directory not created: "+ddir)

    def test_nerd2dc(self):
        nerd = { "@id": "ark:/88434/mds3-1000" }
        with self.assertRaises(NERDError):
            dcmd = self.dmcli._nerd2dc(nerd)

        nerd['_schema'] = "goob"
        with self.assertRaises(NERDError):
            dcmd = self.dmcli._nerd2dc(nerd)

        nerd['_schema'] = nerdconst.CORE_SCHEMA_URI+"#"
        with self.assertRaises(NERDError):
            dcmd = self.dmcli._nerd2dc(nerd)

        nerd['doi'] = "doi:10.88888/goob"
        with self.assertRaises(NERDError):
            dcmd = self.dmcli._nerd2dc(nerd)

        nerd['doi'] = "doi:10.88888/goob"
        with self.assertRaises(NERDError):
            dcmd = self.dmcli._nerd2dc(nerd)

        with self.assertRaises(NERDError):
            dcmd = self.dmcli._nerd2dc(nerd, True)

        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        dcmd = self.dmcli._nerd2dc(nerd, True)
        self.assertEqual(dcmd['doi'], "10.88888/goob")
        self.assertEqual(dcmd['titles'], [{'title': nerd['title']}])
        self.assertEqual(dcmd['contributors'],
                         [{'name': 'Zachary Levine', 'nameType': "Personal", 'contributorType': 'ContactPerson'}])
        self.assertEqual(dcmd['url'], nerd['landingPage'])
        self.assertEqual(dcmd['relatedIdentifiers'],
                         [{"relatedIdentifier": 'https://doi.org/10.1364/OE.24.014100',
                           "relationType": "IsReferencedBy", "relatedIdentifierType": "DOI"}])

        dcmd = self.dmcli._nerd2dc(nerd)  # without validation
        self.assertEqual(dcmd['doi'], "10.88888/goob")
        self.assertEqual(dcmd['titles'], [{'title': nerd['title']}])
        self.assertEqual(dcmd['contributors'],
                         [{'name': 'Zachary Levine', 'nameType': "Personal", 'contributorType': 'ContactPerson'}])
        self.assertEqual(dcmd['url'], nerd['landingPage'])
        self.assertEqual(dcmd['relatedIdentifiers'],
                         [{"relatedIdentifier": 'https://doi.org/10.1364/OE.24.014100',
                           "relationType": "IsReferencedBy", "relatedIdentifierType": "DOI"}])
        
    def test_stage(self):
        nerd = {  }
        with self.assertRaises(NERDError):
            dcmd = self.dmcli.stage(nerd)

        nerd = { "@id": "ark:/88434/mds3-1000" }
        with self.assertRaises(NERDError):
            dcmd = self.dmcli.stage(nerd)

        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        
        self.dmcli.stage(nerd, name=os.path.splitext(os.path.basename(tstnerd))[0])

        out = os.path.join(self.workdir, "staging", os.path.basename(tstnerd))
        self.assertTrue(os.path.exists(out))
        dcmd = read_json(out)
        self.assertEqual(dcmd['doi'], "10.88888/goob")
        self.assertEqual(dcmd['titles'], [{'title': nerd['title']}])
        self.assertEqual(dcmd['url'], nerd['landingPage'])
        self.assertEqual(dcmd['event'], "publish")

        nerd['@id'] = "ark:/88888/{0}".format(os.path.splitext(os.path.basename(tstnerd))[0])
        self.dmcli.stage(nerd, False)

        out = os.path.join(self.workdir, "staging", os.path.basename(tstnerd))
        self.assertTrue(os.path.exists(out))
        dcmd = read_json(out)
        self.assertEqual(dcmd['doi'], "10.88888/goob")
        self.assertEqual(dcmd['titles'], [{'title': nerd['title']}])
        self.assertEqual(dcmd['url'], nerd['landingPage'])
        self.assertNotIn('event', dcmd)

    def test_stage_names(self):
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        
        self.dmcli.stage(nerd, name="gurn")
        self.dmcli.stage(nerd, name="goob")

        names = self.dmcli.staged_names()
        self.assertIn("gurn", names)
        self.assertIn("goob", names)
        self.assertEqual(len(names), 2)

    def test_is_staged(self):
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        
        self.dmcli.stage(nerd, name="gurn")
        self.assertTrue(self.dmcli.is_staged("gurn"))
        self.assertTrue(not self.dmcli.is_staged("goob"))
        
        self.dmcli.stage(nerd, name="goob")
        self.assertTrue(self.dmcli.is_staged("gurn"))
        self.assertTrue(self.dmcli.is_staged("goob"))

    def test_submit_rec(self):
        # submit_rec() should fail because the datacite service hasn't been configured
        
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        dcmd = self.dmcli._nerd2dc(nerd, True)
        self.assertEqual(dcmd['url'], nerd['landingPage'])

        with self.assertRaises(ConfigurationException):
            self.dmcli.submit_rec(dcmd)

    def test_submit_staged(self):
        # submit_rec() should fail because the datacite service hasn't been configured

        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        self.dmcli.stage(nerd, name="gurn")
        self.assertTrue(self.dmcli.is_staged("gurn"))

        with self.assertRaises(ConfigurationException):
            self.dmcli.submit_staged("gurn")

        with self.assertRaises(ConfigurationException):
            self.dmcli.submit_all()

        with self.assertRaises(ConfigurationException):
            self.dmcli.submit("gurn")

    def test_find_named(self):
        stagedir = os.path.join(self.workdir, "staging")
        reservedir = os.path.join(self.workdir, "reserved")
        faildir = os.path.join(self.workdir, "failed")
        
        sfile = os.path.join(stagedir, "bru.json")
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88888/goob"
        self.dmcli.stage(nerd, name="bru")
        self.assertTrue(os.path.exists(sfile))
        self.assertEqual(self.dmcli.staged_names(), ["bru"])

        found = self.dmcli.find_named("bru")
        self.assertTrue(isinstance(found, Mapping))
        self.assertEqual(len(found), 1)
        self.assertIn('staged', found)
        self.assertEqual(found['staged'], sfile)

        shutil.copy(sfile, os.path.join(reservedir, "bru.json"))
        found = self.dmcli.find_named("bru")
        self.assertEqual(len(found), 2)
        self.assertIn('staged', found)
        self.assertIn('reserved', found)
        self.assertEqual(found['staged'], sfile)
        self.assertEqual(found['reserved'],
                         os.path.join(reservedir, "bru.json"))

        shutil.copy(sfile, os.path.join(faildir, "bru.json"))
        found = self.dmcli.find_named("bru")
        self.assertEqual(len(found), 3)
        self.assertIn('staged', found)
        self.assertIn('failed', found)
        self.assertIn('reserved', found)
        self.assertEqual(found['staged'], sfile)
        self.assertEqual(found['failed'], os.path.join(faildir, "bru.json"))

        

class TestDOIMintingClientMockSrvr(test.TestCase):

    @classmethod
    def setUpClass(cls):
        startService()

    @classmethod
    def tearDownClass(cls):
        stopService()

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("doimint")
        self.cfg = {
            'minting_naan':  prefixes[0],
            'data_dir':  self.workdir,
            'publish': True,
            'datacite_api': {
                'service_endpoint': baseurl,
                'user': 'user',
                'pass': 'pw'
            }
        }
        self.dmcli = dm.DOIMintingClient(self.cfg)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertIsNotNone(self.dmcli.dccli)
        self.assertIsNotNone(self.dmcli.log)
        self.assertIsNotNone(self.dmcli._jqt)
        self.assertEqual(self.dmcli.naan, prefixes[0])
        self.assertTrue(self.dmcli._publish_by_default)
        for dirn in "inprogress staging published reserved failed".split():
            ddir = os.path.join(self.workdir, dirn)
            self.assertTrue(ddir, "Data directory not created: "+ddir)

    def test_mocksvc(self):
        doi = self.dmcli.dccli.lookup("mds2-1000", relax=True)
        self.assertFalse(doi.exists)

    def test_submit_rec(self):
        # submit_rec() should fail because the datacite service hasn't been configured
        
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88434/goob1"
        dcmd = self.dmcli._nerd2dc(nerd, True)
        self.assertEqual(dcmd['url'], nerd['landingPage'])

        self.dmcli.submit_rec(dcmd)
            
        doi = self.dmcli.dccli.lookup("goob1", relax=True)
        self.assertTrue(doi.exists)
        self.assertEqual(doi.state, "draft")
        self.assertEqual(doi.attrs.get('url'), dcmd['url'])

        dcmd['url'] = "http://ex.com/"
        dcmd['event'] = "publish"
        self.dmcli.submit_rec(dcmd)
            
        doi = self.dmcli.dccli.lookup("goob1", relax=True)
        self.assertTrue(doi.exists)
        self.assertEqual(doi.state, "findable")
        self.assertEqual(doi.attrs.get('url'), "http://ex.com/")

    def test_submit_staged(self):
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88434/goob2"
        self.dmcli.stage(nerd, publish=False, name="gurn")
        self.assertTrue(self.dmcli.is_staged("gurn"))
        res = self.dmcli.find_named("gurn")
        self.assertTrue(os.path.exists(res['staged']))
        self.assertNotIn('reserved', res)
        self.assertNotIn('published', res)

        self.dmcli.submit_staged("gurn")
        res = self.dmcli.find_named("gurn")
        self.assertNotIn('staged', res)
        self.assertTrue(os.path.exists(res['reserved']))
        self.assertNotIn('published', res)

        doi = self.dmcli.dccli.lookup("goob2", relax=True)
        self.assertTrue(doi.exists)
        self.assertEqual(doi.state, "draft")
        self.assertEqual(doi.attrs.get('url'), nerd['landingPage'])

        nerd['landingPage'] = "http://example.com/"
        self.dmcli.stage(nerd, name="gurn")
        self.assertTrue(self.dmcli.is_staged("gurn"))
        res = self.dmcli.find_named("gurn")
        self.assertTrue(os.path.exists(res['staged']))
        self.assertTrue(os.path.exists(res['reserved']))
        self.assertNotIn('published', res)

        self.dmcli.submit_staged("gurn")
        res = self.dmcli.find_named("gurn")
        self.assertNotIn('staged', res)
        self.assertTrue(os.path.exists(res['reserved']))
        self.assertTrue(os.path.exists(res['published']))

        doi.refresh()
        self.assertTrue(doi.exists)
        self.assertEqual(doi.state, "findable")
        self.assertEqual(doi.attrs.get('url'), "http://example.com/")

    def test_submit_all(self):
        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.88434/goob3"
        self.dmcli.stage(nerd, publish=False, name="gurn")
        self.assertTrue(self.dmcli.is_staged("gurn"))
        res = self.dmcli.find_named("gurn")
        self.assertTrue(os.path.exists(res['staged']))
        self.assertNotIn('reserved', res)
        self.assertNotIn('published', res)

        nerd['landingPage'] = "http://example.com/"
        self.dmcli.stage(nerd, publish=False, name="goob")
        self.assertTrue(self.dmcli.is_staged("goob"))
        res = self.dmcli.find_named("goob")
        self.assertTrue(os.path.exists(res['staged']))
        self.assertNotIn('reserved', res)
        self.assertNotIn('published', res)

        res = self.dmcli.submit_all()
        self.assertIn('gurn', res['succeeded'])
        self.assertIn('goob', res['succeeded'])
        self.assertEqual(len(res['succeeded']), 2)
        self.assertEqual(len(res['failed']), 0)
        self.assertEqual(len(res['skipped']), 0)
        
        doi = self.dmcli.dccli.lookup("goob3", relax=True)
        self.assertTrue(doi.exists)
        self.assertEqual(doi.state, "draft")


if __name__ == '__main__':
    test.main()

