import os, sys, pdb, shutil, logging, json, re
from cStringIO import StringIO
from shutil import copy2 as filecopy, rmtree
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.builder2 as bldr
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.utils import read_nerd

# datadir = tests/nistoar/pdr/preserv/data
datadir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "simplesip"
)

loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
#    logging.basicConfig(filename=os.path.join(tmpdir(),"test_builder.log"),
#                        level=logging.INFO)
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_builder.log"))
    loghdlr.setLevel(logging.DEBUG)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestBuilder2(test.TestCase):

    testsip = os.path.join(datadir, "simplesip")

    def setUp(self):
        self.tf = Tempfiles()
        self.cfg = {
            "init_bag_info": {
                'NIST-BagIt-Version': "X.3",
                "Organization-Address": ["100 Bureau Dr.",
                                         "Gaithersburg, MD 20899"]
            }
        }

        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.tf.track("testbag")
        self.tf.track("issued-ids.json")

    def tearDown(self):
        self.bag._unset_logfile()
        self.bag = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bag.bagname, "testbag")
        self.assertEqual(self.bag.bagdir, os.path.join(self.tf.root, "testbag"))
        self.assertTrue(self.bag.log)
        self.assertFalse(self.bag._loghdlr)
        self.assertEqual(self.bag.logname, "preserv.log")
        self.assertIsNone(self.bag.id)
        self.assertIsNone(self.bag.bag)
        self.assertIsNone(self.bag.ediid)

        baginfo = self.bag.cfg['init_bag_info']
        try:
            self.assertEqual(baginfo['NIST-BagIt-Version'], 'X.3')
            self.assertEqual(baginfo['Contact-Email'], ["datasupport@nist.gov"],
                             "Failed to load default config params")
        except KeyError as ex:
            self.fail("Failed to load default config params: missing params")

        self.assertFalse(self.bag._has_resmd())

    def test_ctor_on_existng_dir(self):
        bagdir = os.path.join(self.tf.root, "testbag")
        if not os.path.exists(bagdir):
            os.mkdir(bagdir)
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)

        self.assertEqual(self.bag.bagname, "testbag")
        self.assertEqual(self.bag.bagdir, os.path.join(self.tf.root, "testbag"))
        self.assertTrue(self.bag.log)
        self.assertTrue(self.bag._loghdlr)
        self.assertEqual(self.bag.logname, "preserv.log")
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "preserv.log")))
        self.assertIsNone(self.bag.id)
        self.assertIsNotNone(self.bag.bag)
        self.assertEqual(self.bag.bag.dir, self.bag.bagdir)
        self.assertIsNone(self.bag.ediid)
        self.assertFalse(self.bag._has_resmd())

    def test_ctor_with_id(self):
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg,
                                   id="edi00hw91c")

        self.assertEqual(self.bag.bagname, "testbag")
        self.assertEqual(self.bag.bagdir, os.path.join(self.tf.root, "testbag"))
        self.assertTrue(self.bag.log)
        self.assertIsNone(self.bag._loghdlr)
        self.assertEqual(self.bag.logname, "preserv.log")
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.assertEqual(self.bag.id, "ark:/88434/edi00hw91c")
        self.assertIsNone(self.bag.bag)
        self.assertIsNone(self.bag.ediid)
        self.assertFalse(self.bag._has_resmd())

    def test_fix_id(self):
        self.assertIsNone(self.bag._fix_id(None))
        self.assertEqual(self.bag._fix_id("ARK:/88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        self.assertEqual(self.bag._fix_id("/88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        self.assertEqual(self.bag._fix_id("88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        self.assertEqual(self.bag._fix_id("edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/goober/foo")
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/88434/edi00hw91d")

        self.cfg['validate_id'] = False
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.assertEqual(self.bag._fix_id("ark:/88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        self.assertEqual(self.bag._fix_id("ark:/88434/edi00hw91d"),
                         "ark:/88434/edi00hw91d")
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/goober/foo")
        
        self.cfg['require_ark_id'] = False
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.assertEqual(self.bag._fix_id("edi00hw91c"), "edi00hw91c")
        self.assertEqual(self.bag._fix_id("ark:/88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/goober/foo")
        

    def test_ensure_bagdir(self):
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.assertFalse(self.bag._loghdlr)
        self.assertIsNone(self.bag.bag)
        self.assertIsNone(self.bag.id)

        self.bag.ensure_bagdir()
        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertIsNotNone(self.bag.bag)
        self.assertEqual(self.bag.bag.dir, self.bag.bagdir)
        self.assertIsNone(self.bag.id)
        self.assertIsNone(self.bag.ediid)

    def test_ensure_bag_structure(self):
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.bag.ensure_bag_structure()

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))

        # test indepodence and extra directories
        self.bag.cfg['extra_tag_dirs'] = ['metameta']
        self.bag.ensure_bag_structure()

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metameta")))
        
    def test_ensure_metadata_dirs(self):
        path = os.path.join("trial1","gold")
        self.bag.ensure_metadata_dirs(path)

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,
                                                     "data",path)))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "metadata",path)))

        # is indepotent
        self.bag.ensure_metadata_dirs(path)
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "metadata",path)))

        # test illegal paths
        with self.assertRaises(ValueError):
            self.bag.ensure_metadata_dirs("/foo/bar")
        with self.assertRaises(ValueError):
            self.bag.ensure_metadata_dirs("foo/../../bar")

    def test_ensure_ansc_collmd(self):
        path = os.path.join("trial1","gold")
        self.bag.ensure_ansc_collmd(path)

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,
                                                     "data",path)))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                              "metadata","trial1","nerdm.json")))
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,
                                                     "metadata",path)))

        md = read_nerd(os.path.join(self.bag.bagdir,
                                    "metadata","trial1","nerdm.json"))
        self.assertEqual(md['filepath'], "trial1")
        self.assertIn("nrdp:Subcollection", md['@type'])

        # is indepotent
        self.bag.ensure_ansc_collmd(path)
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,
                                                     "data",path)))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                              "metadata","trial1","nerdm.json")))
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,
                                                     "metadata",path)))

        # test illegal paths
        with self.assertRaises(ValueError):
            self.bag.ensure_ansc_collmd("/foo/bar")
        with self.assertRaises(ValueError):
            self.bag.ensure_ansc_collmd("foo/../../bar")


    def test_create_init_md_for(self):
        md = self.bag._create_init_md_for("", None)
        self.assertEqual(md['_schema'],
                         "https://data.nist.gov/od/dm/nerdm-schema/v0.2#")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/PublicDataResource"])
        self.assertEqual(md['@type'], ["nrdp:PublicDataResource"])
        self.assertIn("@context", md)

        md = self.bag._create_init_md_for("foo/bar", "DataFile")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/DataFile"])
        self.assertEqual(md['@type'],
                 ["nrdp:DataFile", "nrdp:DownloadableFile", "dcat:Distribution"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo/bar")
        self.assertEqual(md['filepath'], "foo/bar")
        self.assertNotIn('downloadURL', md)

        md = self.bag._create_init_md_for("foo/bar.sha256", "ChecksumFile")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/ChecksumFile"])
        self.assertEqual(md['@type'],
            ["nrdp:ChecksumFile", "nrdp:DownloadableFile", "dcat:Distribution"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo/bar.sha256")
        self.assertEqual(md['filepath'], "foo/bar.sha256")
        self.assertNotIn('downloadURL', md)

        md = self.bag._create_init_md_for("foo/", "Subcollection")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/Subcollection"])
        self.assertEqual(md['@type'], ["nrdp:Subcollection"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo")
        self.assertEqual(md['filepath'], "foo")
        self.assertNotIn('downloadURL', md)

        md = self.bag._create_init_md_for("@id:cmps/foo/", "Subcollection")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/Subcollection"])
        self.assertEqual(md['@type'], ["nrdp:Subcollection"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo")
        self.assertEqual(md['filepath'], "foo")
        self.assertNotIn('downloadURL', md)

        with self.assertRaises(bldr.BagWriteError):
            self.bag._create_init_md_for("@id:cmps/foo/", "Goober")
        with self.assertRaises(ValueError):
            self.bag._create_init_md_for("@id:foo/bar", "DataFile")

    def test_replace_metadata_for_file(self):
        input = { "foo": "bar", "hank": "herb" }
        md = self.bag.replace_metadata_for("readme.txt", input)
        for p in md:
            self.assertIn(p, md)

        written = read_nerd(self.bag.bag.nerd_file_for("readme.txt"))
        self.assertEqual(written, md)
        self.assertEqual(md['foo'], 'bar')
        self.assertEqual(md['hank'], 'herb')
        self.assertEqual(len(md), 2)
                         
        input = { "bar": "foo", "herb": "hank" }
        md = self.bag.replace_metadata_for("@id:cmps/readme.txt", input)
        for p in md:
            self.assertIn(p, md)
        self.assertNotIn("foo", md)
        self.assertNotIn("hank", md)

        written = read_nerd(self.bag.bag.nerd_file_for("readme.txt"))
        self.assertEqual(written, md)
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 2)

        with self.assertRaises(bldr.BadBagRequest):
            self.bag.replace_metadata_for("", input)
                         
    def test_replace_metadata_for_nonfile(self):
        input = { "foo": "bar", "hank": "herb" }
        md = self.bag.replace_metadata_for("@id:#readme", input)
        for p in md:
            self.assertIn(p, md)
        self.assertEqual(md['@id'], "#readme")

        written = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 1)
        written = comps[0]
        self.assertEqual(written, md)
        self.assertEqual(md['foo'], 'bar')
        self.assertEqual(md['hank'], 'herb')
        self.assertEqual(len(md), 3)
                         
        input = { "bar": "foo", "herb": "hank" }
        md = self.bag.replace_metadata_for("@id:#readme", input)
        for p in md:
            self.assertIn(p, md)
        self.assertNotIn("foo", md)
        self.assertNotIn("hank", md)

        written = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 1)
        written = comps[0]
        self.assertEqual(written, md)
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 3)
                         
        md = self.bag.replace_metadata_for("@id:#goob", input)
        written = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 2)
        written = comps[1]
        self.assertEquals(md['@id'], "#goob")
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 3)

    def test_define_component_file(self):
        md = self.bag.define_component("readme.txt", "DataFile", "i did it!")
        
        written = read_nerd(self.bag.bag.nerd_file_for("readme.txt"))
        self.assertEqual(written, md)
        self.assertEqual(md['@id'], "cmps/readme.txt")
        self.assertIn('_schema', md)
        self.assertIn('_extensionSchemas', md)
        self.assertEqual(md['@type'][0], "nrdp:DataFile")
        self.assertEqual(md['filepath'], "readme.txt")

        with open(os.path.join(self.bag.bagdir, "preserv.log")) as fd:
            lines = [l for l in fd]
        self.assertIn("i did it!", lines[-1])
        
        md = self.bag.define_component("trial", "Subcollection")
        
        written = read_nerd(self.bag.bag.nerd_file_for("trial"))
        self.assertEqual(written, md)
        self.assertEqual(md['@id'], "cmps/trial")
        self.assertIn('_schema', md)
        self.assertIn('_extensionSchemas', md)
        self.assertEqual(md['@type'][0], "nrdp:Subcollection")
        self.assertEqual(md['filepath'], "trial")
        
        with open(os.path.join(self.bag.bagdir, "preserv.log")) as fd:
            lines = [l for l in fd]
        self.assertIn("new", lines[-1])

    def test_define_component_subfile(self):
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,
                                                     "metadata","trial")))
        md = self.bag.define_component("trial/readme.txt", "DataFile")
        self.assertEqual(md['filepath'], 'trial/readme.txt')
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                       "metadata/trial/readme.txt/nerdm.json")))
        self.assertTrue(self.bag.bag.is_subcoll("trial"))

        with self.assertRaises(bldr.BadBagRequest):
            self.bag.define_component("trial/readme.txt/foo/bar",
                                      "Subcollection")

    def test_define_component_nonfile(self):
        resnerdf = os.path.join(self.bag.bagdir, "metadata","nerdm.json")
        self.assertFalse(os.path.exists(resnerdf))
        md = self.bag.define_component("@id:#doi", "nrd:Hidden")

        resmd = bldr.read_nerd(resnerdf)
        comps = resmd['components']
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[-1]['@id'], "#doi")

        md = self.bag.define_component("@id:#doi", "nrd:Hidden")

        resmd = bldr.read_nerd(resnerdf)
        comps = resmd['components']
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[-1]['@id'], "#doi")

        md = self.bag.define_component("@id:#gurn", "nrdg:Goober")

        resmd = bldr.read_nerd(resnerdf)
        comps = resmd['components']
        self.assertEqual(len(comps), 2)
        self.assertEqual(comps[-1]['@id'], "#gurn")

        with self.assertRaises(bldr.StateException):
            self.bag.define_component("@id:#doi", "nrd:Goober")

    def test_update_md(self):
        md = {}
        self.bag._update_md(md, {"foo": "bar"})
        self.assertEquals(md, {"foo": "bar"})

        self.bag._update_md(md, {"hank": "herb"})
        self.assertEquals(md, {"foo": "bar", "hank": "herb"})

        self.bag._update_md(md, {"hank": "aaron"})
        self.assertEquals(md, {"foo": "bar", "hank": "aaron"})

        self.bag._update_md(md, {"hank": ["herb", "aaron"]})
        self.assertEquals(md, {"foo": "bar", "hank": ["herb", "aaron"]})

        self.bag._update_md(md, {"hank": {"herb": "aaron"}})
        self.assertEquals(md, {"foo": "bar", "hank": {"herb": "aaron"}})

        self.bag._update_md(md, {"hank": {"a": "b"}})
        self.assertEquals(md, {"foo": "bar",
                               "hank": {"herb": "aaron", "a": "b"}})

        self.bag._update_md(md, {"hank": {"a": "c"}})
        self.assertEquals(md, {"foo": "bar",
                               "hank": {"herb": "aaron", "a": "c"}})

    def test_update_metadata_for_file(self):
        md = self.bag.define_component("trial/readme.txt", "DataFile")
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertNotIn("foo", md)

        md = self.bag.update_metadata_for("trial/readme.txt",
                                          {"foo": "bar", "goob": "gurn"})
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)

        md = self.bag.update_metadata_for("trial/readme.txt",
                                          {"foo": "gurn", "goob": "bar"})
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertNotIn("hand", md)
        
        md = self.bag.update_metadata_for("trial/readme.txt",
                                          {"hand": "eye"})
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertEqual(md['hand'], "eye")
        
        written = read_nerd(self.bag.bag.nerd_file_for("trial/readme.txt"))
        self.assertEqual(md, written)

        md = self.bag.update_metadata_for("@id:cmps/trial/readme.txt",
                                          {"hand": "ear"}, "DataFile")
        self.assertEqual(md['hand'], "ear")
        written = read_nerd(self.bag.bag.nerd_file_for("trial/readme.txt"))
        self.assertEqual(md, written)

        with self.assertRaises(bldr.StateException):
            self.bag.update_metadata_for("trial/readme.txt",
                                         {"hand": "ear"}, "ChecksumFile")

    def test_update_metadata_for_nonfile(self):
        md = self.bag.define_component("@id:#readme.txt", "grn:Goober")
        self.assertEqual(md['@id'], "#readme.txt")
        self.assertNotIn("foo", md)

        md = self.bag.update_metadata_for("@id:#readme.txt",
                                          {"foo": "bar", "goob": "gurn"})
        self.assertEqual(md['@id'], "#readme.txt")
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)

        md = self.bag.update_metadata_for("@id:#readme.txt",
                                          {"foo": "gurn", "goob": "bar"})
        self.assertEqual(md['@id'], "#readme.txt")
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertNotIn("hand", md)
        
        md = self.bag.update_metadata_for("@id:#readme.txt", {"hand": "eye"})
        self.assertEqual(md['@id'], "#readme.txt")
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertEqual(md['hand'], "eye")
        
        written = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 1)
        written = comps[0]
        self.assertEqual(md, written)

    def test_update_metadata_for_resource(self):
        md = self.bag.define_component("", "Resource")
        self.assertNotIn("foo", md)

        md = self.bag.update_metadata_for("", {"foo": "bar", "goob": "gurn"})
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)

        written = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(md, written)

        


    def test_matches_type(self):
        types = ["nrdp:DataFile", "Downloadable", "dcat:Distribution"]
        self.assertTrue(bldr.matches_type(types, "DataFile"))
        self.assertTrue(bldr.matches_type(types, "dcat:Distribution"))
        self.assertTrue(bldr.matches_type(types, "Downloadable"))
        self.assertTrue(not bldr.matches_type(types, "Hidden"))
        self.assertTrue(not bldr.matches_type(types, "goob:DataFile"))

    def test_metadata_matches_type(self):
        mdata = {"@type": ["nrdp:DataFile", "Downloadable", "dcat:Distribution"]}
        self.assertTrue(bldr.metadata_matches_type(mdata, "DataFile"))
        self.assertTrue(bldr.metadata_matches_type(mdata, "dcat:Distribution"))
        self.assertTrue(bldr.metadata_matches_type(mdata, "Downloadable"))
        self.assertTrue(not bldr.metadata_matches_type(mdata, "Hidden"))
        self.assertTrue(not bldr.metadata_matches_type(mdata, "goob:DataFile"))
        
        mdata = {"type": ["nrdp:DataFile", "Downloadable", "dcat:Distribution"]}
        self.assertTrue(not bldr.metadata_matches_type(mdata, "DataFile"))





if __name__ == '__main__':
    test.main()
