import os, sys, pdb, shutil, logging, json, time, re
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils, ARK_NAAN
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit.bag import NISTBag
import nistoar.pdr.preserv.bagger.midas3 as midas
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.preserv import AIPValidationError

# datadir = nistoar/pdr/preserv/data
testdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(testdir), 'data')
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
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
    startServices()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
            loghdlr.flush()
            loghdlr.close()
        loghdlr = None
    stopServices()
    rmtmpdir()

distarchive = os.path.join(tmpdir(), "distarchive")
mdarchive = os.path.join(tmpdir(), "mdarchive")

def startServices():
    tdir = tmpdir()
    archdir = distarchive
    shutil.copytree(distarchdir, archdir)
    shutil.copyfile(os.path.join(archdir,"1491.1_0.mbag0_4-0.zip"),
                    os.path.join(archdir,"3A1EE2F169DD3B8CE0531A570681DB5D1491.1_0.mbag0_4-0.zip"))

    srvport = 9091
    pidfile = os.path.join(tdir,"simdistrib"+str(srvport)+".pid")
    wpy = "python/tests/nistoar/pdr/distrib/sim_distrib_srv.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simdistrib.log"), srvport,
                     os.path.join(basedir, wpy), archdir, pidfile)
    os.system(cmd)

    archdir = mdarchive
    shutil.copytree(descarchdir, archdir)
    nerd = utils.read_nerd(os.path.join(archdir, "pdr02d4t.json"))
    nerd['ediid'] = "3A1EE2F169DD3B8CE0531A570681DB5D1491"
    utils.write_json(nerd, os.path.join(archdir, "3A1EE2F169DD3B8CE0531A570681DB5D1491.json"))

    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    wpy = "python/tests/nistoar/pdr/describe/sim_describe_svc.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simrmm.log"), srvport,
                     os.path.join(basedir, wpy), archdir, pidfile)
    os.system(cmd)
    time.sleep(0.5)

def stopServices():
    tdir = tmpdir()
    srvport = 9091
    pidfile = os.path.join(tdir,"simdistrib"+str(srvport)+".pid")
    
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                               "simdistrib"+str(srvport)+".pid"))
    os.system(cmd)

    # sometimes stopping with uwsgi doesn't work
    try:
        with open(pidfile) as fd:
            pid = int(fd.read().strip())
        os.kill(pid, signal.SIGTERM)
    except:
        pass

    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                               "simrmm"+str(srvport)+".pid"))
    os.system(cmd)

    time.sleep(1)

    # sometimes stopping with uwsgi doesn't work
    try:
        with open(pidfile) as fd:
            pid = int(fd.read().strip())
        os.kill(pid, signal.SIGTERM)
    except:
        pass


class TestUpdateMetadataBagger(test.TestCase):
    
    testsip = os.path.join(datadir, "midassip")
    prevmidasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    midasid = "ark:/"+ARK_NAAN+"/mds8-8888"

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("bagger")
        self.mddir = os.path.join(self.workdir, "mddir")
        os.mkdir(self.mddir)
        self.pubcache = self.tf.mkdir("headcache")

        testsip = os.path.join(self.testsip, "review")
        self.revdir = os.path.join(self.workdir, "review")
        self.sipdir = os.path.join(self.revdir, "8888")
        shutil.copytree(testsip, self.revdir)
        now = time.time()
        for base, dirs, files in os.walk(self.revdir):
            for f in files+dirs:
                os.utime(os.path.join(base,f), (now, now))
        shutil.copytree(os.path.join(self.revdir, "1491"), self.sipdir)
        
        self.config = {
            'relative_to_indir': True,
            'bag_builder': {
                'copy_on_link_failure': False,
                'init_bag_info': {
                    'Source-Organization':
                        "National Institute of Standards and Technology",
                    'Contact-Email': ["datasupport@nist.gov"],
                    'Organization-Address': [
                        "100 Bureau Dr., Gaithersburg, MD 20899"],
                    'NIST-BagIt-Version': "0.4",
                    'Multibag-Version': "0.4"
                }
            },
            'repo_access': {
                'headbag_cache':   self.pubcache,
                'distrib_service': {
                    'service_endpoint': "http://localhost:9091/"
                },
                'metadata_service': {
                    'service_endpoint': "http://localhost:9092/"
                }
            },
            'store_dir': distarchdir
        }

        self.bagr = None
        self.updbagdir = os.path.join(self.mddir, "mds8-8888")
        self.replbagdir = os.path.join(self.mddir, self.prevmidasid)

    def tearDown(self):
        if self.bagr:
            self.bagr.bagbldr._unset_logfile()
            self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.mddir, self.revdir,
                                                        config=self.config, replaces=None)
        self.assertIsNone(self.bagr.previd)
        prepr = self.bagr.get_prepper()
        self.assertEqual(prepr.aipid, "mds8-8888")
        self.assertEqual(prepr._prevaipid, prepr.aipid)

        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.mddir, self.revdir,
                                                        config=self.config, replaces=self.prevmidasid)
        self.assertIsNotNone(self.bagr.previd)
        self.assertNotEqual(self.bagr.previd, self.bagr.midasid)
        prepr = self.bagr.get_prepper()
        self.assertEqual(prepr.aipid, "mds8-8888")
        self.assertEqual(prepr._prevaipid, self.prevmidasid)

    def test_ensure_base_bag_onupdate(self):
        self.assertTrue(not os.path.exists(self.updbagdir))
        self.assertTrue(not os.path.exists(self.replbagdir))
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.mddir, self.revdir,
                                                        config=self.config, replaces=self.prevmidasid)
        self.bagr.ensure_base_bag()
        
        self.assertTrue(not os.path.exists(self.replbagdir))
        self.assertTrue(os.path.exists(self.updbagdir))
        self.assertTrue(os.path.exists(os.path.join(self.updbagdir,"metadata","__bagger-midas3.json")))
        bmd = utils.read_json(os.path.join(self.updbagdir,"metadata","__bagger-midas3.json"))
        self.assertEqual(bmd.get("replacedEDI"), self.prevmidasid)

        bag = NISTBag(self.updbagdir)
        nerdm = bag.nerdm_record(True)
        self.assertEqual(nerdm['ediid'], self.midasid)
        self.assertEqual(len(nerdm.get('replaces',[])), 1)
        self.assertEqual(nerdm['replaces'][0]['ediid'], self.prevmidasid)
        self.assertTrue(nerdm['replaces'][0]['@id'].startswith("doi:"))
        self.assertEqual(nerdm['@id'], 'ark:/88434/edi00hw91c')

    def test_ensure_base_bag_onupdate2(self):
        self.assertTrue(not os.path.exists(self.updbagdir))
        self.assertTrue(not os.path.exists(self.replbagdir))

        # prep under old SIP dir
        
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.prevmidasid, self.mddir, self.revdir,
                                                        config=self.config)
        self.bagr.ensure_base_bag()
        self.assertTrue(os.path.exists(self.replbagdir))
        self.assertTrue(not os.path.exists(self.updbagdir))
        self.assertTrue(os.path.exists(os.path.join(self.replbagdir,"metadata","__bagger-midas3.json")))
        bmd = utils.read_json(os.path.join(self.replbagdir,"metadata","__bagger-midas3.json"))
        self.assertFalse(bmd.get("replacedEDI"))

        # this file will be used to prove that the previous bag was moved to create the new bag
        open(os.path.join(self.replbagdir, "test.json"), 'a').close()
        
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.mddir, self.revdir,
                                                        config=self.config, replaces=self.prevmidasid)
        self.bagr.ensure_base_bag()
        
        self.assertTrue(not os.path.exists(self.replbagdir))
        self.assertTrue(os.path.exists(self.updbagdir))
        self.assertTrue(os.path.exists(os.path.join(self.updbagdir, "test.json")))
        self.assertTrue(os.path.exists(os.path.join(self.updbagdir,"metadata","__bagger-midas3.json")))
        bmd = utils.read_json(os.path.join(self.updbagdir,"metadata","__bagger-midas3.json"))
        self.assertEqual(bmd.get("replacedEDI"), self.prevmidasid)

        bag = NISTBag(self.updbagdir)
        nerdm = bag.nerdm_record(True)
        self.assertEqual(nerdm['ediid'], self.midasid)
        self.assertEqual(len(nerdm.get('replaces',[])), 1)
        self.assertIn('ediid', nerdm['replaces'][0])
        self.assertEqual(nerdm['replaces'][0]['ediid'], self.prevmidasid)
        self.assertTrue(nerdm['replaces'][0]['@id'].startswith("doi:"))
        self.assertEqual(nerdm['@id'], 'ark:/88434/edi00hw91c')

    def test_apply_pod_onupdate(self):
        self.assertTrue(not os.path.exists(self.replbagdir))
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.mddir, self.revdir,
                                                        config=self.config, replaces=self.prevmidasid)

        pod = utils.read_json(os.path.join(self.testsip, "review", "1491", "_pod.json"))
        # POD record will have new MIDAS ID, new DOI, and new download URLs 
        pod['identifier'] = self.midasid
        for dist in pod['distribution']:
            if 'downloadURL' in dist and '/od/ds/' in dist['downloadURL']:
                dist['downloadURL'] = re.sub(self.prevmidasid, self.midasid, dist['downloadURL'])
            elif 'accessURL' in dist and 'doi.org' in dist['accessURL']:
                dist['accessURL'] = re.sub(r'/[^/]+$', '/mds8-8888', dist['accessURL'])
        self.bagr.apply_pod(pod)

        bag = NISTBag(self.updbagdir)
        nerdm = bag.nerdm_record(True)
        self.assertEqual(nerdm['ediid'], self.midasid)
        self.assertEqual(len(nerdm.get('replaces',[])), 1)
        self.assertEqual(nerdm['replaces'][0]['ediid'], self.prevmidasid)
        self.assertTrue(nerdm['replaces'][0]['@id'].startswith("doi:"))
        self.assertEqual(nerdm['@id'], 'ark:/88434/edi00hw91c')
        self.assertEqual(nerdm['doi'], 'doi:10.80443/mds8-8888')

        for cmp in nerdm['components']:
            if 'downloadURL' in cmp and '/od/ds/' in cmp['downloadURL']:
                self.assertIn('mds8-8888', cmp['downloadURL'])
        self.assertEqual(len(nerdm['components']), len(pod['distribution'])+1)
        
        

if __name__ == '__main__':
    test.main()
