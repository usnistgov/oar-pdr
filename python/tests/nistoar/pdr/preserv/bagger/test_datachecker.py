from __future__ import print_function
import os, sys, pdb, shutil, logging, json, time, re

import unittest as test

from nistoar.testing import *
from nistoar.pdr.distrib import client as dcli
from nistoar.pdr.preserv.bagit.bag import NISTBag
import nistoar.pdr.preserv.bagger.datachecker as dc
from nistoar.pdr import utils

storedir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "distrib", "data")
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(storedir))))))

port = 9091
baseurl = "http://localhost:{0}/".format(port)

def startService(authmeth=None):
    tdir = tmpdir()
    srvport = port
    if authmeth == 'header':
        srvport += 1
    pidfile = os.path.join(tdir,"simsrv"+str(srvport)+".pid")
    
    wpy = "python/tests/nistoar/pdr/distrib/sim_distrib_srv.py"
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --pidfile {3}"
    cmd = cmd.format(os.path.join(tdir,"simsrv.log"), srvport,
                     os.path.join(basedir, wpy), pidfile)
    status = os.system(cmd) == 0
    time.sleep(0.5)
    return status

def stopService(authmeth=None):
    tdir = tmpdir()
    srvport = port
    if authmeth == 'header':
        srvport += 1
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
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_simsrv.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

def mk_dlurls_local(bagdir):
    # convert the download urls so that they point to the local
    # sim dist service
    datadotnist = re.compile(r'^https://data.nist.gov/')

    mddir = os.path.join(bagdir, "metadata")
    for (dpath, dirs, files) in os.walk(mddir):
        if 'nerdm.json' not in files:
            continue
        nf = os.path.join(dpath, 'nerdm.json')
        nerd = utils.read_json(nf)
        if 'downloadURL' in nerd:
            nerd['downloadURL'] = \
                datadotnist.sub('http://localhost:9091/',nerd['downloadURL'])
            utils.write_json(nerd, nf)
        
class TestDataChecker(test.TestCase):

    hbagsrc = os.path.join(storedir, "pdr2210.3_1_3.mbag0_3-5.zip")

    def setUp(self):
        self.tf = Tempfiles()
        bagp = self.tf.mkdir("preserv")
        
        uz = "cd %s && unzip -q %s" % (bagp, self.hbagsrc)
        if os.system(uz) != 0:
            raise RuntimeError("Failed to unpack sample bag")
        self.hbag = os.path.join(bagp, os.path.basename(self.hbagsrc[:-4]))
        mk_dlurls_local(self.hbag)

        self.config = { 'store_dir': storedir }
        self.ckr = dc.DataChecker(NISTBag(self.hbag), self.config,
                                  logging.getLogger("datachecker"))

    def tearDown(self):
        self.ckr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.ckr.bag.name, "pdr2210.3_1_3.mbag0_3-5")
        self.assertTrue(self.ckr.log)
        self.assertFalse(self.ckr._distsvc)

    def test_available_in_bag(self):
        self.assertTrue(self.ckr.available_in_bag('trial1.json'))
        self.assertTrue(not self.ckr.available_in_bag('trial2.json'))
        self.assertTrue(not self.ckr.available_in_bag('trial3/trial3a.json'))
        self.assertTrue(not self.ckr.available_in_bag('goob.txt'))

        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertTrue(self.ckr.available_in_bag(cmp))
        del cmp['filepath']
        self.assertTrue(not self.ckr.available_in_bag(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertTrue(not self.ckr.available_in_bag(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertTrue(not self.ckr.available_in_bag(cmp))

    def test_bag_location(self):
        self.assertEqual(self.ckr.bag_location('trial1.json'),
                         "pdr2210.3_1_3.mbag0_3-5")
        self.assertEqual(self.ckr.bag_location('trial2.json'),
                         "pdr2210.1_0.mbag0_3-1")
        self.assertEqual(self.ckr.bag_location('trial3/trial3a.json'),
                         "pdr2210.2.mbag0_3-2")
        self.assertIsNone(self.ckr.bag_location('goob.txt'));

        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertEqual(self.ckr.bag_location(cmp), "pdr2210.3_1_3.mbag0_3-5")
        del cmp['filepath']
        self.assertIsNone(self.ckr.bag_location(cmp));
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertEqual(self.ckr.bag_location(cmp), "pdr2210.1_0.mbag0_3-1")
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertEqual(self.ckr.bag_location(cmp), "pdr2210.2.mbag0_3-2")

    def test_located_here(self):
        self.assertTrue(self.ckr.located_here('trial1.json'))
        self.assertTrue(not self.ckr.located_here('trial2.json'))
        self.assertTrue(not self.ckr.located_here('trial3/trial3a.json'))
        self.assertTrue(not self.ckr.located_here('goob.txt'))

        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertTrue(self.ckr.located_here(cmp))
        del cmp['filepath']
        self.assertTrue(not self.ckr.located_here(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertTrue(not self.ckr.located_here(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertTrue(not self.ckr.located_here(cmp))

    def test_availabe_in_cached_bag(self):
        self.assertTrue(self.ckr.available_in_cached_bag('trial1.json'))
        self.assertTrue(self.ckr.available_in_cached_bag('trial2.json'))
        self.assertTrue(self.ckr.available_in_cached_bag('trial3/trial3a.json'))
        self.assertTrue(not self.ckr.available_in_cached_bag('goob.txt'))

        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertTrue(self.ckr.available_in_cached_bag(cmp))
        del cmp['filepath']
        self.assertTrue(not self.ckr.available_in_cached_bag(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertTrue(self.ckr.available_in_cached_bag(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertTrue(self.ckr.available_in_cached_bag(cmp))

        cmp['filepath'] = "goob.txt"
        self.assertFalse(self.ckr.available_in_cached_bag(cmp))

        with open(os.path.join(self.ckr.bag.dir,"multibag","file-lookup.tsv"),
                  'a') as fd:
            fd.write("data/goob.txt\t"+self.ckr.bag.name+"\n")
        self.ckr = dc.DataChecker(NISTBag(self.hbag), self.config,
                                  logging.getLogger("datachecker"))
        self.assertTrue(self.ckr.bag_location("goob.txt"))
        self.assertFalse(self.ckr.available_in_cached_bag(cmp))

    def test_has_pdr_url(self):
        self.assertTrue(self.ckr.has_pdr_url("http://localhost:8888/od/ds/blah"))
        self.assertFalse(self.ckr.has_pdr_url("http://localhost:8888/goob/blah"))

        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertTrue(self.ckr.has_pdr_url(cmp))
        del cmp['downloadURL']
        self.assertTrue(not self.ckr.has_pdr_url(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertTrue(self.ckr.has_pdr_url(cmp))
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertTrue(self.ckr.has_pdr_url(cmp))

    def test_unindexed_files(self):
        self.assertEqual(len(self.ckr.unindexed_files()), 0)
        self.assertTrue(self.ckr.all_files_indexed())
        
    def test_unindexed_files_false(self):
        self.assertTrue(self.ckr.all_files_indexed())

        shutil.copytree(os.path.join(self.ckr.bag.metadata_dir, "trial1.json"),
                        os.path.join(self.ckr.bag.metadata_dir, "goob.json"))
        nerdm = self.ckr.bag.nerd_metadata_for("goob.json")
        nerdm['filepath'] = "goob.json"
        nerdm['downloadURL'] = re.sub(r'trial1.json','goob.json',
                                      nerdm['downloadURL'])
        with open(os.path.join(self.ckr.bag.metadata_dir, "goob.json",
                               "nerdm.json"), 'w') as fd:
            json.dump(nerdm, fd, indent=2)

        self.assertEqual(self.ckr.unindexed_files(), ['goob.json'])
        self.assertFalse(self.ckr.all_files_indexed())
        self.assertFalse(self.ckr.available_in_cached_bag(nerdm))
        self.assertEqual(self.ckr.unavailable_files(), ['goob.json'])
        self.assertFalse(self.ckr.all_files_available())
        
        
class TestDataCheckerWithService(test.TestCase):

    hbagsrc = os.path.join(storedir, "pdr2210.3_1_3.mbag0_3-5.zip")
    hbag = None

    @classmethod
    def setUpClass(cls):
        if not startService():
            raise RuntimeError("Failed to start mock service")

    @classmethod
    def tearDownClass(cls):
        stopService()

    def setUp(self):
        self.tf = Tempfiles()
        bagp = self.tf.mkdir("preserv")
        
        uz = "cd %s && unzip -q %s" % (bagp, self.hbagsrc)
        if os.system(uz) != 0:
            raise RuntimeError("Failed to unpack sample bag")
        self.hbag = os.path.join(bagp, os.path.basename(self.hbagsrc[:-4]))
        mk_dlurls_local(self.hbag)

        self.config = {
            'store_dir': storedir,
            'repo_access': {
                'distrib_service': {
                    'service_endpoint': 'http://localhost:9091/'
                }
            }
        }
        self.ckr = dc.DataChecker(NISTBag(self.hbag), self.config,
                                  logging.getLogger("datachecker"))

    def tearDown(self):
        self.ckr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.ckr.bag.name, "pdr2210.3_1_3.mbag0_3-5")
        self.assertTrue(self.ckr.log)
        self.assertTrue(self.ckr._distsvc)

    def test_head_url(self):
        (stat, msg) = dc.DataChecker.head_url(
                        "http://localhost:9091/od/ds/_aip/pdr1010.mbag0_3-1.zip")
        self.assertEqual(stat, 200, msg)
        (stat, msg) = dc.DataChecker.head_url(
                        "http://localhost:9091/_aip/pdr1010.mbag0_3-1.zip")
        self.assertEqual(stat, 200, msg)

    def test_available_via_url(self):
        self.assertTrue(self.ckr.available_via_url(
                      "http://localhost:9091/od/ds/_aip/pdr1010.mbag0_3-1.zip"))
        self.assertTrue(self.ckr.available_via_url(
                        "http://localhost:9091/_aip/pdr1010.mbag0_3-1.zip"))

        ## mock server not capable of extracting distributions from bags
        ##
        # cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        # cmp['downloadURL'] = \
        #        re.sub(r'data\.nist\.gov', 'localhost:9091', cmp['downloadURL'])
        # self.assertTrue(self.ckr.available_via_url(cmp))

        # cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        # cmp['downloadURL'] = \
        #        re.sub(r'data\.nist\.gov', 'localhost:9091', cmp['downloadURL'])
        # self.assertTrue(self.ckr.available_via_url(cmp))

    def test_containing_bag_available(self):
        self.assertTrue(self.ckr.containing_bag_available("trial1.json"))
        self.assertTrue(self.ckr.containing_bag_available("trial2.json"))
        self.assertTrue(self.ckr.containing_bag_available("trial3/trial3a.json"))
        self.assertFalse(self.ckr.containing_bag_available("goober"))

        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertTrue(self.ckr.containing_bag_available(cmp))
        
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertTrue(self.ckr.containing_bag_available(cmp))
        
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertTrue(self.ckr.containing_bag_available(cmp))
        
        cmp['filepath'] = "goob/gurn.txt"
        self.assertFalse(self.ckr.containing_bag_available(cmp))
        

    def test_available_as(self):
        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertIs(self.ckr.available_as(cmp), self.ckr.AVAIL_IN_BAG)
        
        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertIs(self.ckr.available_as(cmp), self.ckr.AVAIL_IN_CACHED_BAG)
        
        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertIs(self.ckr.available_as(cmp), self.ckr.AVAIL_IN_CACHED_BAG)

        del cmp['filepath']
        self.assertIs(self.ckr.available_as(cmp, True), self.ckr.AVAIL_NOT)
        
    def test_available(self):
        cmp = self.ckr.bag.nerd_metadata_for('trial1.json')
        self.assertTrue(self.ckr.available(cmp))

        cmp = self.ckr.bag.nerd_metadata_for('trial2.json')
        self.assertTrue(self.ckr.available(cmp))

        cmp = self.ckr.bag.nerd_metadata_for('trial3/trial3a.json')
        self.assertTrue(self.ckr.available(cmp))

        del cmp['filepath']
        self.assertFalse(self.ckr.available(cmp, True))

    def test_unindexed_files_false(self):
        self.assertTrue(self.ckr.all_files_indexed())

        shutil.copytree(os.path.join(self.ckr.bag.metadata_dir, "trial1.json"),
                        os.path.join(self.ckr.bag.metadata_dir, "goob.json"))
        nerdm = self.ckr.bag.nerd_metadata_for("goob.json")
        nerdm['filepath'] = "goob.json"
        nerdm['downloadURL'] = re.sub(r'trial1.json','goob.json',
                                      nerdm['downloadURL'])
        with open(os.path.join(self.ckr.bag.metadata_dir, "goob.json",
                               "nerdm.json"), 'w') as fd:
            json.dump(nerdm, fd, indent=2)

        self.assertEqual(self.ckr.unindexed_files(), ['goob.json'])
        self.assertFalse(self.ckr.all_files_indexed())
        self.assertFalse(self.ckr.available_in_cached_bag(nerdm))
        self.assertEqual(self.ckr.unavailable_files(), ['goob.json'])
        self.assertFalse(self.ckr.all_files_available())
        
    def test_unavailable_files(self):
        self.assertEqual(len(self.ckr.unavailable_files()), 0)
        self.assertTrue(self.ckr.all_files_available())
        
        

if __name__ == '__main__':
    test.main()
