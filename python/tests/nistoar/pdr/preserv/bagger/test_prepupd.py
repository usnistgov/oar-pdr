from __future__ import absolute_import
import os, pdb, sys, json, requests, logging, time, re, hashlib, shutil
from collections import OrderedDict
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.bagger import prepupd
from nistoar.pdr.exceptions import IDNotFound
from nistoar.pdr.utils import checksum_of
from nistoar.pdr.distrib import DistribResourceNotFound
from nistoar.pdr.preserv.bagit import NISTBag
from nistoar.pdr.utils import read_nerd

bagsrcdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
mdsrcdir = os.path.join(os.path.dirname(os.path.dirname(bagsrcdir)), "describe", "data")
storedir = os.path.join(os.path.dirname(os.path.dirname(mdsrcdir)), "distrib", "data")

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
        shutil.copyfile(os.path.join(mdsrcdir, "pdr2210.json"),
                        os.path.join(cachedir, "pdr2210.json"))

class SimDistClient(object):

    def __init__(self, cache):
        self.dir = cache

    def get_json(self, relurl):
        parts = relurl.split("/")
        if len(parts) != 5 or parts[-1] != "_head":
            raise RuntimeError("Unexpected call to simulated distrib service: "+
                               relurl)
        out = { "checksum": {"algorithm": "sha256"}, "aipid": parts[0],
                "contentType": "application/zip", "serialization": "zip",
                "multibagProfileVersion": "0.4" }

        ver = parts[3]
        if ver == "latest":
            ver = "2"
        seq = (int(ver) > 1 and 4) or 2

        name = "{0}.{1}.mbag0_4-{2}.zip".format(parts[0], ver, seq)
        loc = os.path.join(self.dir, name)
        if not os.path.exists(loc):
            raise DistribResourceNotFound(loc)
        
        out.update({'name': name, 'sinceVersion': ver, "multibagSequence": seq,
                    'contentLength': os.stat(loc).st_size })
        out['checksum'].update({ 'hash': checksum_of(loc) })
        return out
        

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

        data = cli.get_json("ABCDEFG/_aip/_v/latest/_head")
        self.assertEqual(data, {"aipid": "ABCDEFG", "sinceVersion": "2", 
                                "contentLength": 10075, "multibagSequence" : 4,
                                "multibagProfileVersion" : "0.4",
                                "contentType": "application/zip",
                                "serialization": "zip",
                                "name": "ABCDEFG.2.mbag0_4-4.zip",
                                "checksum": {"algorithm":"sha256","hash": hash}})

        data = cli.get_json("ABCDEFG/_aip/_v/1/_head")
        self.assertEqual(data, {"aipid": "ABCDEFG", "sinceVersion": "1", 
                                "contentLength": 10075, "multibagSequence" : 2,
                                "multibagProfileVersion" : "0.4",
                                "contentType": "application/zip",
                                "serialization": "zip",
                                "name": "ABCDEFG.1.mbag0_4-2.zip",
                                "checksum": {"algorithm":"sha256","hash": hash}})

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
        self.storedir = self.tf.mkdir("store")
        self.headcache = self.tf.mkdir("headcache")
        self.bagsdir = self.tf.mkdir("bags")
        self.nerddir = self.tf.mkdir("nerds")

        SimDistClient.fill_cache(self.bagsdir)
        SimRMMClient.fill_cache(self.nerddir)
        self.distcli = SimDistClient(self.bagsdir)
        self.mdcli = SimRMMClient(self.nerddir)

        self.config = {
            "working_dir": self.workdir,
            "store_dir": self.storedir,
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

    def test_aip_exists(self):
        self.assertTrue(self.prepr.aip_exists())

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

        bag = NISTBag(root)
        mdata = bag.nerdm_record(True)
        self.assertEquals(mdata['version'], "1.0.0+ (in edit)")
        self.assertIn('versionHistory', mdata)
        self.assertEquals(len(mdata['versionHistory']), 1)
        self.assertEquals(mdata['versionHistory'][0]['version'], "1.0.0")
        self.assertEquals(mdata['versionHistory'][0]['@id'], mdata["@id"])
        self.assertIn('issued', mdata['versionHistory'][0])

        depinfof = os.path.join(bag.dir, "multibag", "deprecated-info.txt")
        self.assertTrue(os.path.isfile(depinfof))
        info = bag.get_baginfo(depinfof)
        self.assertEquals(info['Multibag-Head-Version'], ["1.0"])

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

        nfile = os.path.join(root,"metadata","nerdm.json")
        self.assertTrue(os.path.isfile(nfile))

        md = read_nerd(nfile)
        self.assertEqual(md["_schema"],
                         "https://data.nist.gov/od/dm/nerdm-schema/v0.2#")
        self.assertEqual(md["references"][0]["_extensionSchemas"][0],
                         "https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/DCiteReference")
        self.assertEqual(md["references"][1]["_extensionSchemas"][0],
                         "https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/DCiteReference")
        
        depinfof = os.path.join(root, "multibag", "deprecated-info.txt")
        self.assertTrue(not os.path.isfile(depinfof))
        
    def test_create_new_update(self):
        headbag = os.path.join(self.bagsdir, "ABCDEFG.2.mbag0_4-4.zip")
        cached = os.path.join(self.headcache, "ABCDEFG.2.mbag0_4-4.zip")
        root = os.path.join(self.workdir, "ABCDEFG")
        self.assertTrue(not os.path.exists(root))
        self.assertTrue(not os.path.exists(cached))

        self.assertTrue(self.prepr.create_new_update(root))
        self.assertTrue(os.path.isdir(root))
        self.assertTrue(os.path.exists(cached))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertNotIn("manifest-sha256.txt", contents)
        self.assertNotIn("bag-info.txt", contents)
        self.assertIn("multibag", contents)

        # test using headbag made from nerdm record
        shutil.rmtree(root)  # reset
        os.remove(headbag)   # prevents retrieving headbag via dist service
        os.remove(cached)    # prevents using cached version
        self.assertTrue(not os.path.isdir(root))
        self.assertTrue(self.prepr.create_new_update(root))
        self.assertTrue(os.path.isdir(root))

        contents = [f for f in os.listdir(root)]
        self.assertIn("metadata", contents)
        self.assertIn("data", contents)
        self.assertNotIn("manifest-sha256.txt", contents)
        self.assertNotIn("bag-info.txt", contents)
        self.assertNotIn("multibag", contents)

        bag = NISTBag(root)
        mdata = bag.nerdm_record(True)
        self.assertEquals(mdata['version'], "1.0.0+ (in edit)")


    def test_no_create_new_update(self):
        root = os.path.join(self.workdir, "goober")
        self.assertTrue(not os.path.exists(root))

        self.prepr = self.prepsvc.prepper_for("goober")
        self.prepr.mdcli = self.mdcli

        self.assertFalse(self.prepr.create_new_update(root))
        self.assertTrue(not os.path.isdir(root))

    def test_find_bag_in_store(self):
        sf12_7 = os.path.join(self.storedir, "ABCDEFG.12_7.mbag0_3-2.zip")

        # The way we will test if the file was retreive from the
        # store dir is by making that copy an empty file
        with open(sf12_7,'w') as fd:
            pass

        sf12_8 = os.path.join(self.storedir, "ABCDEFG.12_8.mbag0_3-4.zip")
        with open(sf12_8,'w') as fd:
            pass
        sf12_8 = os.path.join(self.storedir, "ABCDEFG.12_8.mbag0_3-5.zip.sha256")
        with open(sf12_8,'w') as fd:
            pass
        sf12_8 = os.path.join(self.storedir, "ABCDEFG.12_8.mbag0_3-5.zip")
        with open(sf12_8,'w') as fd:
            pass
        sf0 = os.path.join(self.storedir, "ABCDEFG.mbag0_3-5.zip")
        with open(sf0,'w') as fd:
            pass

        self.assertEqual(self.prepr.find_bag_in_store("12.7"), sf12_7)
        self.assertEqual(self.prepr.find_bag_in_store("12.8"), sf12_8)
        self.assertEqual(self.prepr.find_bag_in_store("0"), sf0)

    def test_create_new_update_fromstore(self):
        shutil.copy(os.path.join(storedir, "pdr2210.3_1_3.mbag0_3-5.zip"),
                    self.storedir)
        with open(os.path.join(self.storedir,
                               "pdr2210.3_1_3.mbag0_3-5.zip.sha256"),'w') as fd:
            pass
    
        cachedbag = os.path.join(self.headcache, "pdr2210.3_1_3.mbag0_3-5.zip")

        self.prepr = self.prepsvc.prepper_for("pdr2210")
        self.prepr.mdcli = self.mdcli
        self.prepr.cacher.distsvc = self.distcli

        root = os.path.join(self.workdir, "pdr2210")
        self.assertTrue(not os.path.exists(cachedbag))
        self.assertTrue(not os.path.exists(root))

        self.assertTrue(self.prepr.create_new_update(root))
        self.assertTrue(os.path.isdir(root))

        # these demonstrates that it came from the stored version
        self.assertTrue(os.path.isdir(os.path.join(root,"multibag")))
        self.assertTrue(not os.path.isfile(cachedbag))

        bag = NISTBag(root)
        mdata = bag.nerdm_record(True)
        self.assertEquals(mdata['version'], "3.1.3+ (in edit)")

        
                              
                         

        
        
                    



if __name__ == '__main__':
    test.main()
