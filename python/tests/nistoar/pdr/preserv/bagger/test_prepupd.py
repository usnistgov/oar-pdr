from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib, shutil
from collections import OrderedDict
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.bagger import prepupd
from nistoar.pdr.exceptions import IDNotFound
from nistoar.pdr.utils import checksum_of
from nistoar.pdr.distrib import DistribResourceNotFound

bagsrcdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
mdsrcdir = os.path.join(os.path.dirname(os.path.dirname(bagsrcdir)), "describe", "data")

loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_simsrv.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    rmtmpdir()

class SimRMMClient(object):
    # This is a substitute for accessing the remote RMM service

    def __init__(self, cache):
        self.dir = cache
    def describe(self, id):
        nf = os.path.join(self.dir, id+".json")
        if os.path.exists(nf):
            with open(nf) as fd:
                data = json.load(fd, object_pairs_hook=OrderedDict)
            return data

        raise IDNotFound(id)

    @classmethod
    def fill_cache(cls, cachedir):
        shutil.copyfile(os.path.join(mdsrcdir, "pdr02d4t.json"),
                        os.path.join(cachedir, "ABCDEFG.json"))
        shutil.copyfile(os.path.join(mdsrcdir, "pdr02d4t.json"),
                        os.path.join(cachedir, "pdr02d4t.json"))

class SimDistClient(object):

    def __init__(self, cache):
        self.dir = cache

    def get_json(self, relurl):
        parts = relurl.split("/")
        if len(parts) != 5 or parts[-1] != "head":
            raise RuntimeError("Unexpected call to simulated distrib service: "+
                               relurl)
        out = { "hashtype": "sha256", "id": parts[0] }

        ver = parts[3]
        if ver == "latest":
            ver = "2"
        seq = (int(ver) > 1 and "4") or "2"

        name = "{0}.{1}.mbag0_4-{2}.zip".format(parts[0], ver, seq)
        loc = os.path.join(self.dir, name)
        if not os.path.exists(loc):
            raise DistribResourceNotFound(loc)
        
        out.update({'name': name, 'version': ver, 'size': os.stat(loc).st_size,
                    'hash': checksum_of(loc) })
        return [out]
        

    def retrieve_file(self, relurl, filepath):
        src = os.path.join(self.dir, relurl.split('/')[-1])
        if os.path.exists(src):
            shutil.copy(src, filepath)
        else:
            raise DistribResourceNotFound(relurl, "Not found")

    @classmethod
    def fill_cache(cls, cachedir):
        src = os.path.join(bagsrcdir, "samplembag")
        dest = os.path.join(cachedir, "ABCDEFG.1.mbag0_4-2.zip")
        oldwd = os.getcwd()
        os.chdir(bagsrcdir)
        try:
            cmd = "zip -qr {0} {1}".format(dest, "samplembag")
            os.system(cmd)
        finally:
            os.chdir(oldwd)
        out = checksum_of(dest)
        shutil.copy(dest, os.path.join(cachedir, "ABCDEFG.2.mbag0_4-4.zip"))
        return out
                    

class TestSimServices(test.TestCase):

    def setUp(self):
        self.cachedir = tmpdir()
        if os.path.isdir(self.cachedir):
            rmtmpdir()
        os.mkdir(self.cachedir)

    def tearDown(self):
        rmtmpdir()

    def test_rmm(self):
        SimRMMClient.fill_cache(self.cachedir)
        cli = SimRMMClient(self.cachedir)

        data = cli.describe("pdr02d4t")
        self.assertIn("@id", data)
        data = cli.describe("ABCDEFG")
        self.assertIn("@id", data)

    def test_distrib(self):
        hash = SimDistClient.fill_cache(self.cachedir)
        cli = SimDistClient(self.cachedir)

        data = cli.get_json("ABCDEFG/_bags/_v/latest/head")
        self.assertEqual(data, [{"id": "ABCDEFG", "hashtype": "sha256",
                                 "name": "ABCDEFG.2.mbag0_4-4.zip",
                                 "version": "2", "size": 9715,
                                 "hash": hash }])

        data = cli.get_json("ABCDEFG/_bags/_v/1/head")
        self.assertEqual(data, [{"id": "ABCDEFG", "hashtype": "sha256",
                                 "name": "ABCDEFG.1.mbag0_4-2.zip",
                                 "version": "1", "size": 9715,
                                 "hash": hash}])

        dest = os.path.join(self.cachedir, "local")
        os.mkdir(dest)
        cli.retrieve_file("ABCDEFG.1.mbag0_4-2.zip", dest)

        dest = os.path.join(dest, "ABCDEFG.1.mbag0_4-2.zip")
        self.assertTrue(os.path.exists(dest))
        self.assertEqual(checksum_of(dest), hash)
        
        

class TestUpdatePrepService(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("mdserv")
        self.headcache = self.tf.mkdir("headcache")
        self.config = {
            "headbag_cache": self.headcache,
            "dist_service": {
                "service_endpoint": "http://dummy/ds"
            },
            "metadata_service": {
                "service_endpoint": "http://dummy/rmm"
            }
        }
        self.prepsvc = prepupd.UpdatePrepService(self.config)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.prepsvc.cfg)
        self.assertEqual(self.prepsvc.sercache, self.config['headbag_cache'])

        with self.assertRaises(prepupd.ConfigurationException):
            prepupd.UpdatePrepService({})


    def test_prepper_for(self):
        prepper = self.prepsvc.prepper_for("ABCDEFG", "2.0")
        self.assertEqual(prepper.cacher.cachedir, self.config['headbag_cache'])
        self.assertEqual(prepper.aipid, "ABCDEFG")

        nerdcache = os.path.join(self.config['headbag_cache'],"_nerd")
        self.assertEqual(prepper.mdcache, nerdcache)
        self.assertTrue(os.path.exists(nerdcache))

class TestUpdatePrepper(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("mdserv")
        self.headcache = self.tf.mkdir("headcache")
        self.bagsdir = self.tf.mkdir("bags")
        self.nerddir = self.tf.mkdir("nerds")

        SimDistClient.fill_cache(self.bagsdir)
        SimRMMClient.fill_cache(self.nerddir)
        self.distcli = SimDistClient(self.bagsdir)
        self.mdcli = SimRMMClient(self.nerddir)

        self.config = {
            "working_dir": self.workdir,
            "headbag_cache": self.headcache,
            "distrib_service": {
                "service_endpoint": "http://dummy/ds"
            },
            "metadata_service": {
                "service_endpoint": "http://dummy/rmm"
            }
        }
        self.prepsvc = prepupd.UpdatePrepService(self.config)
        self.prepr = self.prepsvc.prepper_for("ABCDEFG")
        self.prepr.mdcli = self.mdcli
        self.prepr.cacher.distsvc = self.distcli

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.prepr.aipid, "ABCDEFG")
        self.assertIsNone(self.prepr.version)

    def test_cache_headbag(self):
        cached = os.path.join(self.headcache, "ABCDEFG.2.mbag0_4-4.zip")
        self.assertTrue(not os.path.exists(cached))

        self.assertEqual(self.prepr.cache_headbag(), cached)
        self.assertTrue(os.path.exists(cached))

    def test_cache_nerdm_rec(self):
        cached = os.path.join(self.headcache,"_nerd","ABCDEFG.json")
        self.assertTrue(not os.path.exists(cached))

        self.assertEqual(self.prepr.cache_nerdm_rec(), cached)
        self.assertTrue(os.path.exists(cached))

    def test_unpack_bag_as(self):
        root = self.tf.track("goober")
        self.assertTrue(not os.path.exists(root))
        bagzip = os.path.join(self.bagsdir, "ABCDEFG.2.mbag0_4-4.zip")
        
        self.prepr._unpack_bag_as(bagzip, root)
        self.assertTrue(os.path.exists(root))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertIn("bagit.txt", contents)
        self.assertIn("bag-info.txt", contents)

    def test_create_from_headbag(self):
        headbag = os.path.join(self.bagsdir, "ABCDEFG.1.mbag0_4-2.zip")
        root = os.path.join(self.tf.mkdir("update"), "goober")
        self.assertTrue(not os.path.exists(root))

        self.prepr.create_from_headbag(headbag, root)
        self.assertTrue(os.path.isdir(root))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertNotIn("manifest-sha256.txt", contents)
        self.assertNotIn("bag-info.txt", contents)

    def test_create_from_nerdm(self):
        headbag = os.path.join(self.nerddir, "ABCDEFG.json")
        root = os.path.join(self.tf.mkdir("update"), "goober")
        self.assertTrue(not os.path.exists(root))

        self.prepr.create_from_nerdm(headbag, root)
        self.assertTrue(os.path.isdir(root))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertNotIn("manifest-sha256.txt", contents)
        self.assertNotIn("bag-info.txt", contents)

        self.assertTrue(os.path.isfile(os.path.join(root,"metadata","nerdm.json")))

    def test_create_new_update(self):
        headbag = os.path.join(self.bagsdir, "ABCDEFG.1.mbag0_4-2.zip")
        root = os.path.join(self.workdir, "ABCDEFG")
        self.assertTrue(not os.path.exists(root))

        self.assertTrue(self.prepr.create_new_update(root))
        self.assertTrue(os.path.isdir(root))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertNotIn("manifest-sha256.txt", contents)
        self.assertNotIn("bag-info.txt", contents)

        # test using headbag from local cache
        os.remove(headbag) # prevents retrieving headbag via dist service
        self.assertTrue(self.prepr.create_new_update(root))
        self.assertTrue(os.path.isdir(root))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertNotIn("manifest-sha256.txt", contents)
        self.assertNotIn("bag-info.txt", contents)

    def test_no_create_new_update(self):
        root = os.path.join(self.workdir, "goober")
        self.assertTrue(not os.path.exists(root))

        self.prepr = self.prepsvc.prepper_for("goober")
        self.prepr.mdcli = self.mdcli

        self.assertFalse(self.prepr.create_new_update(root))
        self.assertTrue(not os.path.isdir(root))

        

        
                              
                         

        
        
                    



if __name__ == '__main__':
    test.main()
