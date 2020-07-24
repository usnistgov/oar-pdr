from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib, shutil, yaml
from collections import Mapping
import unittest as test
import requests

from nistoar.testing import *
from nistoar.pdr.preserv import PreservationException
from nistoar.pdr.preserv.service import siphandler as sip
from nistoar.pdr.preserv.service import status
from nistoar.pdr.preserv.bagger import midas3 as midas
from nistoar.pdr.utils import read_nerd, read_json
from nistoar.pdr.exceptions import NERDError, ConfigurationException
from nistoar.nerdm import constants as nerdconst
import nistoar.pdr.doimint as dm

port = 9091
mockbaseurl = "http://localhost:{0}/dois".format(port)
dctbaseurl = "https://api.test.datacite.org/dois"
prefixes = ["10.80443"]

pdrdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
datadir = os.path.join(pdrdir, "describe", "data")
tstnerd = os.path.join(datadir, "pdr2210.json")

basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(pdrdir))))
ormdir = os.path.join(basedir, "oar-metadata")
mocksvr = os.path.join(ormdir, "python", "nistoar", "doi", "tests", "sim_datacite_srv.py")

presdatadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

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

class TestPreservationDOIMockSrvr(test.TestCase):
    # This version runs integrated preservation tests with doi minting turned on
    # against the mock datacite service.  (see also TestPreservationDOIDataCite below)

    @classmethod
    def setUpClass(cls):
        startService()

    @classmethod
    def tearDownClass(cls):
        stopService()

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("preserve")
        self.dmdir = os.path.join(self.workdir, "doimint")
        self.dmcfg = {
            'minting_naan':  prefixes[0],
            'data_dir':  self.dmdir,
            'publish': False,
            'datacite_api': {
                'service_endpoint': mockbaseurl,
                'user': 'user',
                'pass': 'pw'
            }
        }

    def tearDown(self):
        self.tf.clean()

    def test_minting(self):
        dmcli = dm.DOIMintingClient(self.dmcfg)

        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.80443/pdrut-1000"
        doipath = nerd['doi'][4:]
        dmcli.stage(nerd, publish=False, name="gurn")
        self.assertTrue(dmcli.is_staged("gurn"))

        doi = None
        try:
            dmcli.submit_staged("gurn")
            res = dmcli.find_named("gurn")
            self.assertNotIn('staged', res)
            self.assertTrue(os.path.exists(res['reserved']))
            self.assertNotIn('published', res)

            doi = dmcli.dccli.lookup("pdrut-1000", relax=True)
            self.assertTrue(doi.exists)
            self.assertEqual(doi.state, "draft")
            self.assertEqual(doi.attrs.get('url'), nerd['landingPage'])
            self.assertEqual(doi.attrs.get('doi'), doipath)

        finally:
            url = dmcli.dccli._ep
            if not url.endswith('/'):
                url += '/'
            url += doipath
            creds = (self.dmcfg['datacite_api']['user'], self.dmcfg['datacite_api']['pass'])
            res = requests.delete(url, auth=creds)

            doi = dmcli.dccli.lookup("pdrut-1000", relax=True)
            self.assertTrue(not doi.exists)

    testsip = os.path.join(presdatadir, "metadatabag")
    revdir = os.path.join(presdatadir, "midassip", "review")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def test_siphandler_minting(self):
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.dataroot = os.path.join(self.workdir, "data")
        os.mkdir(self.dataroot)
        self.datadir = os.path.join(self.dataroot, "1491")
        self.stagedir = os.path.join(self.workdir, "staging")
        self.storedir = os.path.join(self.workdir, "store")
        os.mkdir(self.storedir)
        self.statusdir = os.path.join(self.workdir, "status")
        os.mkdir(self.statusdir)
        self.bagparent = os.path.join(self.datadir, "_preserv")
        self.sipdir = os.path.join(self.mdbags, self.midasid)

        with open(os.path.join(presdatadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
            
        # set the config we'll use
        self.config = {
            'working_dir': self.workdir,
            'review_dir': self.dataroot,
            "staging_dir": self.stagedir,
            'store_dir': self.storedir,
            "status_manager": { "cachedir": self.statusdir },
            'bagger': baggercfg,
            "ingester": {
                "data_dir":  os.path.join(self.workdir, "ingest"),
                "submit": "none"
            },
            "multibag": {
                "max_headbag_size": 2000000,
#                "max_headbag_size": 100,
                "max_bag_size": 200000000
            },
            "doi_minter": {
                'minting_naan':  prefixes[0],
                'data_dir':  os.path.join(self.workdir, "doimint"),
                'publish': False,
                'datacite_api': {
                    'service_endpoint': mockbaseurl,
                    'user': 'user',
                    'pass': 'pw'
                }
            }
        }

        # copy the data files first
        shutil.copytree(os.path.join(self.revdir, "1491"), self.datadir)
        # os.mkdir(self.bagparent)

        # copy input bag to writable location
        shutil.copytree(self.testsip, self.sipdir)

        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, self.datadir)
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.done()

        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

        # Above was all setup; now run the test!
        self.assertIsNotNone(self.sip._doiminter)
        self.assertIsNotNone(self.sip._doiminter.dccli)
        self.assertIsNotNone(self.sip._doiminter.dccli._ep)
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertFalse(self.sip._is_preserved())
        doipath = "{0}/pdrut-T4SW26".format(prefixes[0])

        try:
            self.sip.bagit()
            self.assertTrue(self.sip._is_preserved())

            doi = self.sip._doiminter.dccli.lookup("pdrut-T4SW26", relax=True)
            self.assertTrue(doi.exists)
            self.assertEqual(doi.state, "draft")
            self.assertTrue(doi.attrs.get('url'))
            self.assertEqual(doi.attrs.get('doi'), doipath)

        finally:
            url = self.sip._doiminter.dccli._ep
            if not url.endswith('/'):
                url += '/'
            url += doipath
            creds = (self.dmcfg['datacite_api']['user'], self.dmcfg['datacite_api']['pass'])
            res = requests.delete(url, auth=creds)

            doi = self.sip._doiminter.dccli.lookup("pdrut-1000", relax=True)
            self.assertTrue(not doi.exists)
        


@test.skipIf(not os.environ.get("OAR_TEST_DATACITE_CREDS"),
             "No credentials provided")
class TestPreservationDOIDataCite(test.TestCase):
    # This version runs integrated preservation tests with doi minting turned on
    # against the official DataCite testing service.  (see also TestPreservationDOIMockSrvr above)
    creds = tuple(os.environ.get("OAR_TEST_DATACITE_CREDS","").split(':'))

    @classmethod
    def setUpClass(cls):
        startService()

    @classmethod
    def tearDownClass(cls):
        stopService()

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("preserve")
        self.dmdir = os.path.join(self.workdir, "doimint")
        self.dmcfg = {
            'minting_naan':  prefixes[0],
            'data_dir':  self.dmdir,
            'publish': False,
            'datacite_api': {
                'service_endpoint': dctbaseurl,
                'user': self.creds[0],
                'pass': self.creds[1]
            }
        }

    def tearDown(self):
        self.tf.clean()

    def test_minting(self):
        dmcli = dm.DOIMintingClient(self.dmcfg)

        nerd = read_nerd(tstnerd)
        nerd['doi'] = "doi:10.80443/pdrut-1000"
        doipath = nerd['doi'][4:]
        dmcli.stage(nerd, publish=False, name="gurn")
        self.assertTrue(dmcli.is_staged("gurn"))

        doi = None
        try:
            dmcli.submit_staged("gurn")
            res = dmcli.find_named("gurn")
            self.assertNotIn('staged', res)
            self.assertTrue(os.path.exists(res['reserved']))
            self.assertNotIn('published', res)

            doi = dmcli.dccli.lookup("pdrut-1000", relax=True)
            self.assertTrue(doi.exists)
            self.assertEqual(doi.state, "draft")
            self.assertEqual(doi.attrs.get('url'), nerd['landingPage'])
            self.assertEqual(doi.attrs.get('doi'), doipath)

        finally:
            url = dmcli.dccli._ep
            if not url.endswith('/'):
                url += '/'
            url += doipath
            creds = (self.dmcfg['datacite_api']['user'], self.dmcfg['datacite_api']['pass'])
            res = requests.delete(url, auth=creds)

            doi = dmcli.dccli.lookup("pdrut-1000", relax=True)
            self.assertTrue(not doi.exists)

    testsip = os.path.join(presdatadir, "metadatabag")
    revdir = os.path.join(presdatadir, "midassip", "review")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/80434/mds2-1491"

    def test_siphandler_minting(self):
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.dataroot = os.path.join(self.workdir, "data")
        os.mkdir(self.dataroot)
        self.datadir = os.path.join(self.dataroot, "1491")
        self.stagedir = os.path.join(self.workdir, "staging")
        self.storedir = os.path.join(self.workdir, "store")
        os.mkdir(self.storedir)
        self.statusdir = os.path.join(self.workdir, "status")
        os.mkdir(self.statusdir)
        self.bagparent = os.path.join(self.datadir, "_preserv")
        self.sipdir = os.path.join(self.mdbags, self.midasid)

        with open(os.path.join(presdatadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
            
        # set the config we'll use
        self.config = {
            'working_dir': self.workdir,
            'review_dir': self.dataroot,
            "staging_dir": self.stagedir,
            'store_dir': self.storedir,
            "status_manager": { "cachedir": self.statusdir },
            'bagger': baggercfg,
            "ingester": {
                "data_dir":  os.path.join(self.workdir, "ingest"),
                "submit": "none"
            },
            "multibag": {
                "max_headbag_size": 2000000,
#                "max_headbag_size": 100,
                "max_bag_size": 200000000
            },
            "doi_minter": {
                'minting_naan':  prefixes[0],
                'data_dir':  os.path.join(self.workdir, "doimint"),
                'publish': False,
                'datacite_api': {
                    'service_endpoint': dctbaseurl,
                    'user': self.creds[0],
                    'pass': self.creds[1]
                }
            }
        }

        # copy the data files first
        shutil.copytree(os.path.join(self.revdir, "1491"), self.datadir)
        # os.mkdir(self.bagparent)

        # copy input bag to writable location
        shutil.copytree(self.testsip, self.sipdir)

        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, self.datadir)
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.done()

        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

        # Above was all setup; now run the test!
        self.assertIsNotNone(self.sip._doiminter)
        self.assertIsNotNone(self.sip._doiminter.dccli)
        self.assertIsNotNone(self.sip._doiminter.dccli._ep)
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertFalse(self.sip._is_preserved())
        doipath = "{0}/pdrut-T4SW26".format(prefixes[0])

        try:
            self.sip.bagit()
            self.assertTrue(self.sip._is_preserved())

            doi = self.sip._doiminter.dccli.lookup("pdrut-T4SW26", relax=True)
            self.assertTrue(doi.exists)
            self.assertEqual(doi.state, "draft")
            self.assertTrue(doi.attrs.get('url'))
            self.assertEqual(doi.attrs.get('doi','').lower(), doipath.lower())

        finally:
            url = self.sip._doiminter.dccli._ep
            if not url.endswith('/'):
                url += '/'
            url += doipath
            creds = (self.dmcfg['datacite_api']['user'], self.dmcfg['datacite_api']['pass'])
            res = requests.delete(url, auth=creds)

            doi = self.sip._doiminter.dccli.lookup("pdrut-1000", relax=True)
            self.assertTrue(not doi.exists)
        


if __name__ == '__main__':
    test.main()

