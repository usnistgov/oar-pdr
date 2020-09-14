import os, sys, pdb, shutil, logging, json, re
from cStringIO import StringIO
from shutil import copy2 as filecopy, rmtree
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.builder as bldr
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
    global loghdlr
    global rootlog
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
            rootlog.removeHandler(loghdlr)
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
        self.bag.disconnect_logfile()
        self.bag = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bag.bagname, "testbag")
        self.assertEqual(self.bag.bagdir, os.path.join(self.tf.root, "testbag"))
        self.assertTrue(self.bag.log)
        self.assertFalse(self.bag._log_handlers)
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

    def test_with_disconnect(self):
        logtag = self.bag.plog.name
        baglog = logging.getLogger(logtag)
        self.assertEqual(len(baglog.handlers), 0)
        self.bag.disconnect_logfile()

        with bldr.BagBuilder(self.tf.root, "testbag", self.cfg) as self.bag:
            self.assertEqual(len(self.bag.plog.handlers), 0)
            self.assertEqual(len(baglog.handlers), 0)
            self.bag.ensure_bagdir()
            self.assertEqual(len(self.bag.plog.handlers), 1)
            self.assertEqual(len(baglog.handlers), 1)
            
        self.assertEqual(len(baglog.handlers), 0)
        self.assertEqual(len(self.bag.plog.handlers), 0)

    def test_ctor_on_existng_dir(self):
        bagdir = os.path.join(self.tf.root, "testbag")
        if not os.path.exists(bagdir):
            os.mkdir(bagdir)
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)

        self.assertEqual(self.bag.bagname, "testbag")
        self.assertEqual(self.bag.bagdir, os.path.join(self.tf.root, "testbag"))
        self.assertTrue(self.bag.log)
        self.assertTrue(self.bag.logfile_is_connected())
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
        self.assertFalse(self.bag.logfile_is_connected())
        self.assertFalse(self.bag._log_handlers)
        self.assertEqual(self.bag.logname, "preserv.log")
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.assertEqual(self.bag.id, "ark:/88434/edi00hw91c")
        self.assertIsNone(self.bag.bag)
        self.assertIsNone(self.bag.ediid)
        self.assertFalse(self.bag._has_resmd())

    def test_fix_id(self):
        self.bag.cfg['validate_id'] = True
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
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/88434/mds2-4193")

        self.cfg['validate_id'] = False
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.assertEqual(self.bag._fix_id("ark:/88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        self.assertEqual(self.bag._fix_id("ark:/88434/edi00hw91d"),
                         "ark:/88434/edi00hw91d")
        self.assertEqual(self.bag._fix_id("ark:/88434/mds2-4193"),
                         "ark:/88434/mds2-4193")
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/goober/foo")

        self.cfg['validate_id'] = r'(edi\d)|(mds[01])'
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        with self.assertRaises(ValueError):
            # validate this one
            self.bag._fix_id("ark:/88434/edi00hw91d")

        # don't validate this these
        self.assertEqual(self.bag._fix_id("ark:/88434/pdr00hw91c"),
                         "ark:/88434/pdr00hw91c")
        self.assertEqual(self.bag._fix_id("ark:/88434/mds2-4193"),
                         "ark:/88434/mds2-4193")

        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/goober/foo")
        
        self.cfg['validate_id'] = r'(edi\d)|(mds[01])'
        self.cfg['require_ark_id'] = False
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.assertEqual(self.bag._fix_id("edi00hw91c"), "edi00hw91c")
        self.assertEqual(self.bag._fix_id("ark:/88434/edi00hw91c"),
                         "ark:/88434/edi00hw91c")
        with self.assertRaises(ValueError):
            self.bag._fix_id("ark:/goober/foo")
        

    def test_assign_id(self):
        self.assertIsNone(self.bag.id)
        with self.assertRaises(ValueError):
            self.bag.assign_id(None)
        with self.assertRaises(ValueError):
            self.bag.assign_id("")

        self.bag.assign_id("edi00hw91c")
        self.assertEqual(self.bag.id, "ark:/88434/edi00hw91c")

        resmd = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(resmd['@id'], "ark:/88434/edi00hw91c")
        self.assertTrue(isinstance(resmd['@context'], list))
        self.assertEqual(resmd['@context'][1]['@base'], "ark:/88434/edi00hw91c")

    def test_log_disconnect(self):
        self.assertTrue(not self.bag.logfile_is_connected())
        self.bag.ensure_bagdir()
        self.assertTrue(self.bag.logfile_is_connected())

        self.bag.disconnect_logfile()
        self.assertTrue(not self.bag.logfile_is_connected())
        self.bag.record("i did it!")
        
        with open(os.path.join(self.bag.bagdir, "preserv.log")) as fd:
            lines = [l for l in fd]
        self.assertNotIn("i did it!", lines[-1])

        self.bag.ensure_bagdir()
        self.bag.record("i did it!")
        self.assertTrue(self.bag.logfile_is_connected())

        with open(os.path.join(self.bag.bagdir, "preserv.log")) as fd:
            lines = [l for l in fd]
        self.assertIn("i did it!", lines[-1])

    def test_ensure_bagdir(self):
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.assertTrue(not self.bag.logfile_is_connected())
        self.assertFalse(self.bag._log_handlers)
        self.assertIsNone(self.bag.bag)
        self.assertIsNone(self.bag.id)

        self.bag.ensure_bagdir()
        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertIsNotNone(self.bag.bag)
        self.assertEqual(self.bag.bag.dir, self.bag.bagdir)
        self.assertIsNone(self.bag.id)
        self.assertIsNone(self.bag.ediid)
        self.assertTrue(self.bag.logfile_is_connected())
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"preserv.log")))

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

    def test_ensure_datafile_dirs(self):
        ddir = os.path.join("trial1","gold")
        path = os.path.join(ddir,"file.dat")
        self.bag.ensure_datafile_dirs(path)

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "data",ddir)))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "metadata",path)))

        # is indepotent
        self.bag.ensure_datafile_dirs(path)
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "data",ddir)))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,
                                                    "metadata",path)))

        # test illegal paths
        with self.assertRaises(Exception):
            self.bag.ensure_datafile_dirs("/foo/bar")
        with self.assertRaises(Exception):
            self.bag.ensure_datafile_dirs("foo/../../bar")

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
                         "https://data.nist.gov/od/dm/nerdm-schema/v0.3#")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#/definitions/PublicDataResource"])
        self.assertEqual(md['@type'], ["nrdp:PublicDataResource"])
        self.assertIn("@context", md)

        md = self.bag._create_init_md_for("foo/bar", "DataFile")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.3#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#/definitions/DataFile"])
        self.assertEqual(md['@type'],
                 ["nrdp:DataFile", "nrdp:DownloadableFile", "dcat:Distribution"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo/bar")
        self.assertEqual(md['filepath'], "foo/bar")
        self.assertNotIn('downloadURL', md)

        md = self.bag._create_init_md_for("foo/bar.sha256", "ChecksumFile")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.3#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#/definitions/ChecksumFile"])
        self.assertEqual(md['@type'],
            ["nrdp:ChecksumFile", "nrdp:DownloadableFile", "dcat:Distribution"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo/bar.sha256")
        self.assertEqual(md['filepath'], "foo/bar.sha256")
        self.assertNotIn('downloadURL', md)

        md = self.bag._create_init_md_for("foo/", "Subcollection")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.3#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#/definitions/Subcollection"])
        self.assertEqual(md['@type'], ["nrdp:Subcollection"])
        self.assertIn("@context", md)
        self.assertEqual(md['@id'], "cmps/foo")
        self.assertEqual(md['filepath'], "foo")
        self.assertNotIn('downloadURL', md)

        md = self.bag._create_init_md_for("@id:cmps/foo/", "Subcollection")
        self.assertEqual(md['_schema'],
          "https://data.nist.gov/od/dm/nerdm-schema/v0.3#/definitions/Component")
        self.assertEqual(md['_extensionSchemas'],
                         ["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#/definitions/Subcollection"])
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

        md = self.bag.replace_metadata_for("", input)
        written = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertEqual(md, written)
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 2)
                         
    def test_replace_metadata_for_nonfile(self):
        input = { "foo": "bar", "hank": "herb" }
        md = self.bag.replace_metadata_for("@id:#readme", input)
        for p in input:
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
        for p in input:
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

        with self.assertRaises(ValueError):
            self.bag.define_component("@id:#res", "Resource")

    def test_remove_file_component(self):
        path = os.path.join("trial1","gold","trial1.json")
        bagfilepath = os.path.join(self.bag.bagdir, 'data',path)
        bagmdpath = os.path.join(self.bag.bagdir, 'metadata',path,"nerdm.json")
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertFalse( os.path.exists(bagmdpath) )
        self.assertFalse( os.path.exists(os.path.dirname(bagmdpath)) )
        self.assertFalse( os.path.exists(os.path.dirname(bagfilepath)) )

        # add and remove data and metadata
        self.bag.add_data_file(path, os.path.join(datadir,"trial1.json"))
        self.assertTrue( os.path.exists(bagfilepath) )
        self.assertTrue( os.path.exists(bagmdpath) )

        self.assertTrue(self.bag.remove_component(path))
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertFalse( os.path.exists(bagmdpath) )
        self.assertFalse( os.path.exists(os.path.dirname(bagmdpath)) )
        self.assertTrue( os.path.exists(os.path.dirname(bagfilepath)) )

        # add and remove just metadata
        self.bag.register_data_file(path, os.path.join(datadir,"trial1.json"))
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertTrue( os.path.exists(bagmdpath) )

        self.assertTrue(self.bag.remove_component(path))
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertFalse( os.path.exists(bagmdpath) )
        self.assertFalse( os.path.exists(os.path.dirname(bagmdpath)) )
        self.assertTrue( os.path.exists(os.path.dirname(bagfilepath)) )

        # just a data file exists
        self.assertFalse( os.path.exists(os.path.join(self.bag.bagdir,
                                                      "data", "trial1.json")) )
        filecopy(os.path.join(datadir,"trial1.json"),
                 os.path.join(self.bag.bagdir, "data", "trial1.json"))
        self.assertTrue( os.path.exists(os.path.join(self.bag.bagdir,
                                                      "data", "trial1.json")) )
        self.assertTrue(self.bag.remove_component("trial1.json"))
        self.assertFalse( os.path.exists(os.path.join(self.bag.bagdir,
                                                      "data", "trial1.json")) )

    def test_remove_nonfile_component(self):
        self.bag.define_component("@id:goober", "nrd:Goober")
        self.bag.define_component("@id:#readme.txt", "nrd:Hidden")
        md = self.bag.bag.nerd_metadata_for("")
        self.assertIn("components", md)
        self.assertEqual(len(md['components']), 2)

        self.assertTrue( self.bag.remove_component("@id:goober") )
        md = self.bag.bag.nerd_metadata_for("")
        self.assertIn("components", md)
        self.assertEqual(len(md['components']), 1)

        self.assertTrue( self.bag.remove_component("@id:#readme.txt") )
        md = self.bag.bag.nerd_metadata_for("")
        self.assertIn("components", md)
        self.assertEqual(len(md['components']), 0)
        
    def test_remove_file_component_trim(self):
        gold = os.path.join("trial1","gold")
        golddir = os.path.join(self.bag.bagdir, "data", gold)
        t1path = os.path.join(gold, "trial1.json")
        t2path = os.path.join("trial1","trial2.json")
        t1bagfilepath = os.path.join(self.bag.bagdir, 'data',t1path)
        t1bagmdpath = os.path.join(self.bag.bagdir, 'metadata',
                                   t1path,"nerdm.json")
        t2bagfilepath = os.path.join(self.bag.bagdir, 'data',t2path)
        t2bagmdpath = os.path.join(self.bag.bagdir, 'metadata',
                                   t2path,"nerdm.json")
        self.assertFalse( os.path.exists(t1bagfilepath) )
        self.assertFalse( os.path.exists(t1bagmdpath) )
        self.assertFalse( os.path.exists(os.path.dirname(t1bagmdpath)) )
        self.assertFalse( os.path.exists(os.path.dirname(t1bagfilepath)) )

        self.bag.add_data_file(t1path, os.path.join(datadir,"trial1.json"))
        self.bag.add_data_file(t2path, os.path.join(datadir,"trial2.json"))
        self.assertTrue( os.path.exists(t1bagfilepath) )
        self.assertTrue( os.path.exists(t1bagmdpath) )
        self.assertTrue( os.path.exists(t2bagfilepath) )
        self.assertTrue( os.path.exists(t2bagmdpath) )

        self.assertTrue(self.bag.remove_component(t1path, True))

        self.assertFalse( os.path.exists(t1bagfilepath) )
        self.assertFalse( os.path.exists(t1bagmdpath) )
        self.assertFalse( os.path.exists(os.path.dirname(t1bagmdpath)) )
        self.assertFalse( os.path.exists(os.path.dirname(t1bagfilepath)) )
        self.assertFalse( os.path.exists(os.path.dirname(os.path.dirname(t1bagmdpath))) )

        self.assertFalse( os.path.exists( golddir ) )
        self.assertTrue( os.path.exists(t2bagfilepath) )
        self.assertTrue( os.path.exists(t2bagmdpath) )

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

    def test_replace_annotation_for_file(self):
        input = { "foo": "bar", "hank": "herb" }
        md = self.bag.replace_annotations_for("readme.txt", input)
        for p in md:
            self.assertIn(p, md)

        written = read_nerd(self.bag.bag.annotations_file_for("readme.txt"))
        self.assertEqual(written, md)
        self.assertEqual(md['foo'], 'bar')
        self.assertEqual(md['hank'], 'herb')
        self.assertEqual(len(md), 2)
                         
        md = self.bag.define_component("readme.txt", "DataFile")
        self.assertNotIn('foo', md)
        self.assertNotIn('hank', md)
        written = read_nerd(self.bag.bag.annotations_file_for("readme.txt"))
        self.assertEqual(written['foo'], 'bar')
        self.assertEqual(written['hank'], 'herb')

        input = { "bar": "foo", "herb": "hank" }
        md = self.bag.replace_annotations_for("@id:cmps/readme.txt", input)
        for p in md:
            self.assertIn(p, md)
        self.assertNotIn("foo", md)
        self.assertNotIn("hank", md)

        written = read_nerd(self.bag.bag.annotations_file_for("readme.txt"))
        self.assertEqual(written, md)
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 2)

    def test_replace_annotations_for_nonfile(self):
        input = { "foo": "bar", "hank": "herb" }
        md = self.bag.replace_annotations_for("@id:#readme", input)
        for p in input:
            self.assertIn(p, md)
        self.assertEqual(md['@id'], "#readme")

        written = read_nerd(self.bag.bag.annotations_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 1)
        written = comps[0]
        self.assertEqual(written, md)
        self.assertEqual(md['foo'], 'bar')
        self.assertEqual(md['hank'], 'herb')
        self.assertEqual(len(md), 3)
                         
        input = { "bar": "foo", "herb": "hank" }
        md = self.bag.replace_annotations_for("@id:#readme", input)
        for p in input:
            self.assertIn(p, md)
        self.assertNotIn("foo", md)
        self.assertNotIn("hank", md)

        written = read_nerd(self.bag.bag.annotations_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 1)
        written = comps[0]
        self.assertEqual(written, md)
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 3)
                         
        md = self.bag.replace_annotations_for("@id:#goob", input)
        written = read_nerd(self.bag.bag.annotations_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 2)
        written = comps[1]
        self.assertEquals(md['@id'], "#goob")
        self.assertEqual(md['bar'], 'foo')
        self.assertEqual(md['herb'], 'hank')
        self.assertEqual(len(md), 3)


    def test_update_annotations_for_file(self):
        md = self.bag.update_annotations_for("trial/readme.txt",
                                             {"foo": "bar", "goob": "gurn"})
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)
        self.assertNotIn("filepath", md)
        self.assertEqual(len(md), 2)

        # demonstrate that default metadata have been created for this comp
        # and that it is unaffected by the annotations
        md = self.bag.bag.nerd_metadata_for("trial/readme.txt",
                                            merge_annots=False)
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertNotIn("foo", md)
        self.assertNotIn("goob", md)
        md = self.bag.update_metadata_for("trial/readme.txt", {'goob':"garb"},
                                          "DataFile")
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertNotIn("foo", md)
        self.assertEqual(md['goob'], "garb")
        md = self.bag.bag.annotations_metadata_for("trial/readme.txt")
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)
        self.assertNotIn("filepath", md)
        self.assertEqual(len(md), 2)
        md = self.bag.bag.nerd_metadata_for("trial/readme.txt",
                                            merge_annots=True)
        self.assertEqual(md['filepath'], "trial/readme.txt")
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        
        # more updates
        md = self.bag.update_annotations_for("trial/readme.txt",
                                          {"foo": "gurn", "goob": "bar"})
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertNotIn("hand", md)
        
        md = self.bag.update_annotations_for("trial/readme.txt",
                                          {"hand": "eye"})
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertEqual(md['hand'], "eye")
        
        written= read_nerd(self.bag.bag.annotations_file_for("trial/readme.txt"))
        self.assertEqual(md, written)

        md = self.bag.update_annotations_for("@id:cmps/trial/readme.txt",
                                             {"hand": "ear"}, "DataFile")
        self.assertEqual(md['hand'], "ear")
        written= read_nerd(self.bag.bag.annotations_file_for("trial/readme.txt"))
        self.assertEqual(md, written)

        with self.assertRaises(bldr.StateException):
            self.bag.update_annotations_for("trial/readme.txt",
                                            {"hand": "ear"}, "ChecksumFile")

    def test_update_annotations_for_nonfile(self):
        md = self.bag.update_annotations_for("@id:#readme.txt",
                                             {"foo": "bar", "goob": "gurn"},
                                             "nrd:Hidden")
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)
        self.assertNotIn("@type", md)
        self.assertEqual(len(md), 3)

        # demonstrate that default metadata have been created for this comp
        # and that it is unaffected by the annotations
        md = self.bag.bag.nerd_metadata_for("", merge_annots=False)
        self.assertEquals(len(md.get('components',[])), 1)
        md = md['components'][-1]
        self.assertEqual(md['@type'], ["nrd:Hidden"])
        self.assertNotIn("foo", md)
        self.assertNotIn("goob", md)
        md = self.bag.bag.annotations_metadata_for("")
        self.assertEquals(len(md.get('components',[])), 1)
        md = md['components'][-1]
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertEqual(len(md), 3)
        md = self.bag.bag.nerd_metadata_for("", merge_annots=True)
        self.assertEquals(len(md.get('components',[])), 1)
        md = md['components'][-1]
        self.assertEqual(md['@type'], ["nrd:Hidden"])
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")

        md = self.bag.update_annotations_for("@id:#readme.txt",
                                             {"foo": "gurn", "goob": "bar"})
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertNotIn("hand", md)
        
        md = self.bag.update_annotations_for("@id:#readme.txt", {"hand": "eye"})
        self.assertEqual(md['foo'],  "gurn")
        self.assertEqual(md['goob'], "bar")
        self.assertEqual(md['hand'], "eye")
        
        written = read_nerd(self.bag.bag.annotations_file_for(""))
        self.assertEqual(len(written), 1)
        comps = written['components']
        self.assertEqual(len(comps), 1)
        written = comps[0]
        self.assertEqual(md, written)

    def test_update_metadata_for_resource(self):
        md = self.bag.update_annotations_for("", {"foo": "bar", "goob": "gurn"})
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        self.assertNotIn("hank", md)

        written = read_nerd(self.bag.bag.annotations_file_for(""))
        self.assertEqual(md, written)

        md = read_nerd(self.bag.bag.nerd_file_for(""))
        self.assertNotIn("foo", md)
        self.assertNotIn("goob", md)
        self.assertNotIn("hank", md)
        md = self.bag.update_metadata_for("", {"goob": "garb"})
        md = self.bag.bag.nerd_metadata_for("", merge_annots=False)
        self.assertNotIn("foo", md)
        self.assertNotIn("hank", md)
        self.assertEqual(md['goob'], "garb")
        md = self.bag.bag.nerd_metadata_for("", merge_annots=True)
        self.assertEqual(md['foo'],  "bar")
        self.assertEqual(md['goob'], "gurn")
        
    def test_rename_bag(self):
        bagdir = os.path.join(self.tf.root, "testbag")
        self.assertEqual(self.bag.bagname, "testbag")
        self.assertEqual(self.bag.bagdir, bagdir)
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.assertIsNone(self.bag._bag)

        self.bag.rename_bag("goobbag")
        bagdir = os.path.join(self.tf.root, "goobbag")
        self.assertEqual(self.bag.bagname, "goobbag")
        self.assertEqual(self.bag.bagdir, bagdir)
        self.assertTrue(not os.path.exists(bagdir))
        self.assertIsNone(self.bag._bag)

        self.bag.ensure_bagdir()
        self.assertTrue(os.path.exists(bagdir))
        self.assertEqual(self.bag.bagname, "goobbag")
        self.assertEqual(self.bag.bagdir, bagdir)
        self.assertIsNotNone(self.bag._bag)
        self.assertEqual(self.bag._bag.dir, bagdir)

        self.bag.rename_bag("foobag")
        self.assertEqual(self.bag.bagname, "foobag")
        self.assertTrue(not os.path.exists(bagdir))
        bagdir = os.path.join(self.tf.root, "foobag")
        self.assertTrue(os.path.exists(bagdir))
        self.assertEqual(self.bag.bagdir, bagdir)
        self.assertIsNotNone(self.bag._bag)
        self.assertEqual(self.bag._bag.dir, bagdir)

    def test_determine_file_comp_type(self):
        self.assertEquals(self.bag._determine_file_comp_type("goob.txt"),
                          "DataFile")
        self.assertEquals(self.bag._determine_file_comp_type("goob.txt.sha256"),
                          "ChecksumFile")
        self.assertEquals(self.bag._determine_file_comp_type("goob.txt.sha512"),
                          "ChecksumFile")
        self.assertEquals(self.bag._determine_file_comp_type("goob.txt.md5"),
                          "ChecksumFile")
        self.assertEquals(self.bag._determine_file_comp_type("goob.txt.sha"),
                          "DataFile")

    def test_describe_data_file(self):
        srcfile = os.path.join(datadir, "trial1.json")

        md = self.bag.describe_data_file(srcfile, "goob/trial1.json")
        self.assertEqual(md['filepath'], "goob/trial1.json")
        self.assertEqual(md['@id'], "cmps/goob/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)
        self.assertIn("nrdp:DataFile", md['@type'])
        self.assertEqual(md['checksum'], {"algorithm": {'@type': 'Thing',
                                                        "tag": "sha256" },
    "hash": "d155d99281ace123351a311084cd8e34edda6a9afcddd76eb039bad479595ec9"})
        self.assertNotIn('downloadURL', md)  # because bag does not exist

        md = self.bag.describe_data_file(srcfile, "goob/trial1.json", False)
        self.assertEqual(md['filepath'], "goob/trial1.json")
        self.assertEqual(md['@id'], "cmps/goob/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)
        self.assertIn("nrdp:DataFile", md['@type'])
        self.assertNotIn("checksum", md)

        md = self.bag.describe_data_file(srcfile, "goob/trial1.json",
                                         False, "ChecksumFile")
        self.assertEqual(md['filepath'], "goob/trial1.json")
        self.assertEqual(md['@id'], "cmps/goob/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)
        self.assertNotIn("nrdp:DataFile", md['@type'])
        self.assertIn("nrdp:ChecksumFile", md['@type'])
        self.assertNotIn("checksum", md)

        md = self.bag.describe_data_file(srcfile)
        self.assertEqual(md['filepath'], "trial1.json")
        self.assertEqual(md['@id'], "cmps/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)
        self.assertIn("nrdp:DataFile", md['@type'])
        self.assertEqual(md['checksum'], {"algorithm": {'@type': 'Thing',
                                                        "tag": "sha256" },
    "hash": "d155d99281ace123351a311084cd8e34edda6a9afcddd76eb039bad479595ec9"})

        # if bag exists, downloadURL will be set
        self.bag.ensure_bagdir()
        self.bag.ediid = "goober"
        md = self.bag.describe_data_file(srcfile, "foo/trial1.json")
        self.assertEqual(md['filepath'], "foo/trial1.json")
        self.assertIn('downloadURL', md)
        self.assertTrue(md['downloadURL'].endswith("/od/ds/goober/foo/trial1.json"))

        self.bag.ediid = "ark:/88434/goober"
        md = self.bag.describe_data_file(srcfile)
        self.assertEqual(md['filepath'], "trial1.json")
        self.assertIn('downloadURL', md)
        self.assertTrue(md['downloadURL'].endswith("/od/ds/goober/trial1.json"))

        # don't override existing metadata
        exturl = "https://example.com/goober/trial1.json"
        md['downloadURL'] = exturl
        md['title'] = "a fine file"
        self.bag.update_metadata_for("trial1.json", md)
        md = self.bag.describe_data_file(srcfile)
        self.assertEqual(md['filepath'], "trial1.json")
        self.assertIn('downloadURL', md)
        self.assertEqual(md['downloadURL'], exturl)
        self.assertEqual(md['title'], "a fine file")

        # override existing metadata when told to
        self.bag.update_metadata_for("trial1.json", md)
        md = self.bag.describe_data_file(srcfile, "foo/trial1.json", asupdate=False)
        self.assertEqual(md['filepath'], "foo/trial1.json")
        self.assertIn('downloadURL', md)
        self.assertNotIn('title', md)
        self.assertTrue(md['downloadURL'].endswith("/od/ds/goober/foo/trial1.json"))

    def test_register_data_file(self):
        srcfile = os.path.join(datadir, "trial1.json")
        mddir = os.path.join(self.bag.bagdir, "metadata")
        mdfile = os.path.join(mddir, "goob", "trial1.json", "nerdm.json")
        self.assertTrue(not os.path.exists(mdfile))
        self.assertTrue(not os.path.exists(mddir))

        md = self.bag.register_data_file("goob/trial1.json", srcfile)
        self.assertEqual(md['filepath'], "goob/trial1.json")
        self.assertEqual(md['@id'], "cmps/goob/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)
        self.assertIn("nrdp:DataFile", md['@type'])
        self.assertEqual(md['checksum'], {"algorithm": {'@type': 'Thing',
                                                        "tag": "sha256" },
    "hash": "d155d99281ace123351a311084cd8e34edda6a9afcddd76eb039bad479595ec9"})

        self.assertTrue(os.path.exists(mddir))
        self.assertTrue(os.path.exists(mdfile))
        md = read_nerd(mdfile)
        self.assertEqual(md['filepath'], "goob/trial1.json")
        self.assertEqual(md['@id'], "cmps/goob/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)
        self.assertIn("nrdp:DataFile", md['@type'])
        self.assertEqual(md['checksum'], {"algorithm": {'@type': 'Thing',
                                                        "tag": "sha256" },
    "hash": "d155d99281ace123351a311084cd8e34edda6a9afcddd76eb039bad479595ec9"})

        md = self.bag.register_data_file("goob/trial2.json")
        self.assertEqual(md['filepath'], "goob/trial2.json")
        self.assertEqual(md['@id'], "cmps/goob/trial2.json")
        self.assertEqual(md['mediaType'], "application/json")

    def test_add_data_file(self):
        srcfile = os.path.join(datadir, "trial1.json")
        ddir = os.path.join(self.bag.bagdir, "data")
        mdir = os.path.join(self.bag.bagdir, "metadata")
        self.assertTrue(not os.path.exists(ddir))
        self.assertTrue(not os.path.exists(mdir))

        self.bag.add_data_file("goob/trial1.json", srcfile, False)
        self.assertTrue(os.path.exists(ddir))
        self.assertTrue(not os.path.exists(os.path.join(mdir,
                                                 "goob/trial1.json/nerdm.json")))
        self.assertTrue(os.path.isfile(os.path.join(ddir, "goob/trial1.json")))

        self.bag.add_data_file("gurn/trial1.json", srcfile)
        self.assertTrue(os.path.exists(ddir))
        self.assertTrue(os.path.isdir(os.path.join(mdir,"gurn/trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(mdir,
                                                 "gurn/trial1.json/nerdm.json")))
        self.assertTrue(os.path.isfile(os.path.join(mdir,"gurn/nerdm.json")))
        self.assertTrue(os.path.isfile(os.path.join(ddir,"gurn/trial1.json")))

        md = self.bag.bag.nerd_metadata_for("gurn/trial1.json")
        self.assertEqual(md['filepath'], "gurn/trial1.json")
        self.assertEqual(md['@id'], "cmps/gurn/trial1.json")
        self.assertEqual(md['mediaType'], "application/json")
        self.assertEqual(md['size'], 69)

        md = self.bag.bag.nerd_metadata_for("gurn")
        self.assertEqual(md['filepath'], "gurn")
        self.assertEqual(md['@id'], "cmps/gurn")
                        
    def test_update_ediid(self):
        self.assertIsNone(self.bag.ediid)
        self.bag.ediid = "9999"
        self.assertIsNone(self.bag.bag)
        self.assertFalse(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        
        with open(os.path.join(datadir, "_nerdm.json")) as fd:
            mdata = json.load(fd)
        self.bag.add_res_nerd(mdata)
        self.assertIsNotNone(self.bag.ediid)
        self.assertIsNotNone(self.bag.bag)

        destpath = "foo/bar.json"
        dlurl = "https://data.nist.gov/od/ds/"+self.bag.ediid+'/'+destpath
        self.bag.register_data_file(destpath)
        with open(self.bag.bag.nerd_file_for(destpath)) as fd:
            mdata = json.load(fd)
        self.assertTrue(mdata['downloadURL'], dlurl)

        self.bag.ediid = "gurn"

        with open(self.bag.bag.nerd_file_for("")) as fd:
            mdata = json.load(fd)
        self.assertEqual(mdata['ediid'], 'gurn')
        dlurl = "https://data.nist.gov/od/ds/gurn/"+destpath
        with open(self.bag.bag.nerd_file_for(destpath)) as fd:
            mdata = json.load(fd)
        self.assertEqual(mdata['downloadURL'], dlurl)

    def test_add_res_nerd(self):
        self.assertIsNone(self.bag.ediid)
        with open(os.path.join(datadir, "_nerdm.json")) as fd:
            mdata = json.load(fd)

        self.bag.add_res_nerd(mdata)
        self.assertEqual(self.bag.ediid, mdata['ediid'])
        ddir = os.path.join(self.bag.bagdir,"data")
        mdir = os.path.join(self.bag.bagdir,"metadata")
        nerdfile = os.path.join(mdir,"nerdm.json")
        self.assertTrue(os.path.isdir(ddir))
        self.assertTrue(os.path.isdir(mdir))
        self.assertTrue(os.path.exists(nerdfile))
#        self.assertTrue(os.path.exists(os.path.join(ddir,
#                                "1491_optSortSphEvaluated20160701.cdf")))
        self.assertTrue(os.path.exists(os.path.join(mdir,
                          "1491_optSortSphEvaluated20160701.cdf","nerdm.json")))
#        self.assertTrue(os.path.exists(os.path.join(ddir,
#                                "1491_optSortSphEvaluated20160701.cdf.sha256")))
        self.assertTrue(os.path.exists(os.path.join(mdir,
                    "1491_optSortSphEvaluated20160701.cdf.sha256","nerdm.json")))
        self.assertEqual(len([f for f in os.listdir(mdir)
                                if not f.startswith('.') and
                                   not f.endswith('.json')]), 6)
        
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEqual(data['ediid'], '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(len(data['components']), 1)
        self.assertNotIn('inventory', data)
        self.assertNotIn('dataHierarchy', data)

        with open(os.path.join(mdir,
                  "1491_optSortSphEvaluated20160701.cdf","nerdm.json")) as fd:
            data = json.load(fd)
        self.assertEqual(data['filepath'],"1491_optSortSphEvaluated20160701.cdf")
            
    def test_add_ds_pod(self):
        self.assertIsNone(self.bag.ediid)
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        self.bag.add_ds_pod(poddata, convert=False)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertIsNone(self.bag.ediid)
        with open(self.bag.bag.pod_file()) as fd:
            data = json.load(fd)
        self.assertEqual(data, poddata)
        self.assertFalse(os.path.exists(self.bag.bag.nerd_file_for("")))
        self.assertFalse(os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))
        self.assertFalse(os.path.exists(self.bag.bag.nerd_file_for("trial3/trial3a.json")))

    def test_add_ds_pod_convert(self):
        self.assertIsNone(self.bag.ediid)
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        self.bag.add_ds_pod(poddata, convert=True, savefilemd=False)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertEqual(self.bag.ediid, poddata['identifier'])

        nerdfile = self.bag.bag.nerd_file_for("")
        self.assertTrue(os.path.exists(nerdfile))
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEqual(data['modified'], poddata['modified'])
        # self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertNotIn('@id', data)
        self.assertFalse(os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))
        self.assertFalse(os.path.exists(self.bag.bag.nerd_file_for("trial3/trial3a.json")))

        # special check for theme processing
        self.assertEqual(poddata['theme'][0], "Optical physics")
        self.assertEqual(len(poddata['theme']), 1)
        self.assertEqual(len(data['topic']), 1)
        self.assertEqual(data['topic'][0]['tag'], "Physics: Optical physics")
        self.assertEqual(len(data['theme']), 1)
        self.assertEqual(data['theme'][0], "Physics: Optical physics")

    def test_add_ds_pod_filemd(self):
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        #pdb.set_trace()
        self.bag.add_ds_pod(poddata, convert=True, savefilemd=True)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))

        nerdfile = self.bag.bag.nerd_file_for("")
        self.assertTrue(os.path.exists(nerdfile))
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEqual(data['modified'], poddata['modified'])
#        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertNotIn('@id', data)
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("trial3/trial3a.json")))
        nerdfile = self.bag.bag.nerd_file_for("trial3/trial3a.json")
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEquals(data['filepath'], "trial3/trial3a.json")
        self.assertEquals(data['@id'], "cmps/trial3/trial3a.json")

    def test_save_pod(self):
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)

        self.assertTrue(not os.path.exists(self.bag.bagdir))
        self.bag.save_pod(poddata)
        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("")))

        with open(self.bag.bag.pod_file()) as fd:
            saved = json.load(fd)
        self.assertEqual(poddata, saved)
        
    def test_save_pod_from_file(self):
        podfile = os.path.join(datadir, "_pod.json")
        self.assertTrue(not os.path.exists(self.bag.bagdir))
        
        self.bag.save_pod(podfile)
        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("")))

        with open(podfile) as fd:
            srcdata = fd.read()
        with open(self.bag.bag.pod_file()) as fd:
            saved = fd.read()
        self.assertEqual(srcdata, saved)

    def test_update_from_pod(self):
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        self.assertTrue(not os.path.exists(self.bag.bagdir))

        self.bag.update_from_pod(poddata, False, False)
        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(not os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("")))

        with open(self.bag.bag.nerd_file_for("")) as fd:
            saved = json.load(fd)
        self.assertEqual(poddata['identifier'], saved['ediid'])
        self.assertTrue(saved['title'])
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))

        # because we did not save the pod, this altered value will get overridden
        saved['title'] = "Goobed!"
        with open(self.bag.bag.nerd_file_for(""), 'w') as fd:
            json.dump(saved, fd)

        self.bag.update_from_pod(poddata, True, False)
        self.assertTrue(not os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("")))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))
        
        with open(self.bag.bag.nerd_file_for("")) as fd:
            saved = json.load(fd)
        self.assertEqual(poddata['identifier'], saved['ediid'])
        self.assertNotEqual(saved['title'], "Goobed!")

        # Because updfilemd=False, this will not get overridden
        with open(self.bag.bag.nerd_file_for("trial1.json")) as fd:
            saved = json.load(fd, object_pairs_hook=OrderedDict)
        saved['title'] = "Goobed!"
        with open(self.bag.bag.nerd_file_for("trial1.json"), 'w') as fd:
            json.dump(saved, fd)

        self.bag.update_from_pod(poddata, False, True)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("")))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))

        with open(self.bag.bag.nerd_file_for("trial1.json")) as fd:
            saved = json.load(fd)
        self.assertEqual(saved['title'], "Goobed!")

        # Because the POD has not changed, the trial1 metadata is not overridden
        self.bag.update_from_pod(poddata, True, True)
        with open(self.bag.bag.nerd_file_for("trial1.json")) as fd:
            saved = json.load(fd)
        self.assertEqual(saved['title'], "Goobed!")
        self.bag.update_from_pod(poddata, True, True, force=True)
        with open(self.bag.bag.nerd_file_for("trial1.json")) as fd:
            saved = json.load(fd)
        self.assertNotEqual(saved['title'], "Goobed!")

        with open(self.bag.bag.pod_file()) as fd:
            saved = json.load(fd, object_pairs_hook=OrderedDict)
        saved['distribution'][0]['title'] = "Gurned!"
        with open(self.bag.bag.pod_file(), 'w') as fd:
            json.dump(saved, fd)

        self.bag.update_from_pod(poddata, True, True)
        with open(self.bag.bag.nerd_file_for("trial1.json")) as fd:
            saved = json.load(fd, object_pairs_hook=OrderedDict)
        self.assertNotEqual(saved['title'], "Goobed!")
        self.assertNotEqual(saved['title'], "Gurned!")

        # test deleting componetnts
        del poddata['distribution'][0]
        self.bag.update_from_pod(poddata)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("")))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("trial2.json")))
        
        # test deleting all componetnts (via non-existent distribution property)
        del poddata['distribution']
        self.bag.update_from_pod(poddata)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for("")))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("trial1.json")))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("trial2.json")))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("trial3/trial3a.json")))
        self.assertTrue(not os.path.exists(self.bag.bag.nerd_file_for("trial3")))
        


    def test_trim_metadata_folders(self):
        manfile = os.path.join(self.bag.bagdir, "manifest-sha256.txt")
        datafiles = [ "trial1.json", "trial2.json", 
                      os.path.join("trial3", "trial3a.json") ]
        for df in datafiles:
            self.bag.add_data_file(df, os.path.join(datadir, df))
        metadir = os.path.join(self.bag.bagdir,"metadata")
        t3dir = os.path.join(metadir,"trial3")

        empties = [ os.path.join(t3dir,"cal","volt"),
                    os.path.join(t3dir,"cal","temp"),
                    os.path.join(metadir,"trial1.json","special") ]
        for d in empties:
            os.makedirs(d)

        for d in empties:
            self.assertTrue(os.path.isdir(d))

        self.bag.trim_metadata_folders()

        for d in empties:
            self.assertTrue(not os.path.exists(d))
        self.assertTrue(not os.path.exists(os.path.join(t3dir,"cal")))
        
    def test_trim_data_folders(self):
        manfile = os.path.join(self.bag.bagdir, "manifest-sha256.txt")
        datafiles = [ "trial1.json", "trial2.json", 
                      os.path.join("trial3", "trial3a.json") ]
        bdatadir = os.path.join(self.bag.bagdir,"data")
        metadir = os.path.join(self.bag.bagdir,"metadata")
        t3dir = os.path.join(bdatadir,"trial3")
        for df in datafiles:
            self.bag.add_data_file(df, os.path.join(datadir, df))

        # create some empty data directories
        empties = [ os.path.join("trial3","cal","volt"),
                    os.path.join("trial3","cal","temp") ]
        for d in empties:
            os.makedirs(os.path.join(bdatadir, d))
        os.makedirs(os.path.join(metadir,"cal","volt"))
        
        # remove a data file so we are left with just its metadata
        t2mdir = os.path.join(metadir, "trial2.json")
        os.remove(os.path.join(bdatadir, "trial2.json"))
        os.remove(os.path.join(bdatadir, "trial3", "trial3a.json"))

        for d in empties:
            self.assertTrue(os.path.isdir(os.path.join(bdatadir, d)))
        for df in datafiles:
            self.assertTrue(os.path.isdir(os.path.join(metadir,df)))

        self.bag.trim_data_folders(False)

        for d in empties:
            self.assertTrue(not os.path.exists(os.path.join(bdatadir, d)))
            self.assertTrue(not os.path.exists(os.path.join(metadir, d)))
        self.assertTrue(not os.path.exists(os.path.join(t3dir,"cal")))

        for df in datafiles:
            self.assertTrue(os.path.isdir(os.path.join(metadir,df)))
        self.assertTrue(os.path.isdir(os.path.join(metadir,"trial2.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir,
                                                    "trial3","trial3a.json")))

        # try again with rmmeta=True
        for d in empties:
            d = os.path.join(bdatadir, d)
            if not os.path.exists(d):
                os.makedirs(d)

        self.bag.trim_data_folders(True)
        
        for d in empties:
            self.assertTrue(not os.path.exists(os.path.join(bdatadir, d)))
            self.assertTrue(not os.path.exists(os.path.join(metadir, d)))
        self.assertTrue(not os.path.exists(os.path.join(t3dir,"cal")))

        self.assertTrue(os.path.isdir(os.path.join(metadir,"trial1.json")))
        self.assertTrue(os.path.isdir(os.path.join(metadir,"trial2.json")))
        self.assertTrue(not os.path.exists(os.path.join(bdatadir, "trial3")))
        self.assertTrue(not os.path.exists(os.path.join(metadir, "trial3")))

    def test_ensure_comp_metadata(self):
        manfile = os.path.join(self.bag.bagdir, "manifest-sha256.txt")
        datafiles = [ "trial1.json", "trial2.json" ]
        nomd_datafile = os.path.join("trial3", "trial3a.json") 
        bdatadir = os.path.join(self.bag.bagdir,"data")
        metadir = os.path.join(self.bag.bagdir,"metadata")
        t3dir = os.path.join(bdatadir,"trial3")
        for df in datafiles:
            self.bag.add_data_file(df, os.path.join(datadir, df))
        self.bag.add_data_file(nomd_datafile,
                               os.path.join(datadir, nomd_datafile),
                               register=False)
        self.bag.update_metadata_for("trial2.json", {"size": 5})

        for df in datafiles + [nomd_datafile]:
            self.assertTrue( os.path.isfile(os.path.join(bdatadir, df)) )
        for df in datafiles:
            self.assertTrue( os.path.isfile(os.path.join(metadir, df,
                                                         "nerdm.json")) )
        self.assertFalse( os.path.exists(os.path.join(metadir, nomd_datafile,
                                                      "nerdm.json")) )

        self.bag.ensure_comp_metadata()

        for df in datafiles:
            mdfile = os.path.join(metadir, df, "nerdm.json")
            self.assertTrue( os.path.isfile(mdfile) )

        # check to see that the size for trial2.json was not updated
        data = read_nerd(mdfile)
        self.assertEqual(data['size'], 5)
        
        mdfile = os.path.join(metadir, nomd_datafile, "nerdm.json")
        self.assertTrue( os.path.isfile(mdfile) )

        # check that if the checksum is missing, it will get filled in.
        data = read_nerd(mdfile)
        for prop in "@id @type filepath mediaType checksum size".split():
            self.assertIn(prop, data)
        del data['checksum']

        self.bag.ensure_comp_metadata()
        data = read_nerd(mdfile)
        self.assertIn("checksum", data)

        # now try it with updstats=True
        self.bag.ensure_comp_metadata(True)

        mdfile = os.path.join(metadir, "trial2.json", "nerdm.json")
        data = read_nerd(mdfile)
        self.assertNotEqual(data['size'], 5)

    def test_ensure_bagit_ver(self):
        self.assertTrue(not os.path.exists( self.bag.bagdir ))
        self.bag.ensure_bagit_ver()
        bagitf = os.path.join(self.bag.bagdir, "bagit.txt") 
        self.assertTrue(os.path.exists(bagitf))
            
        with open(bagitf) as fd:
            lines = fd.readlines()

        self.assertTrue(any([r for r in lines if "BagIt_Version:"]))
        self.assertTrue(any([r for r in lines if "Tag-File-Character-Encoding:"]))

    def test_write_data_manifest(self):
        manfile = os.path.join(self.bag.bagdir, "manifest-sha256.txt")
        datafiles = [ "trial1.json", "trial2.json", 
                      os.path.join("trial3", "trial3a.json") ]
        for df in datafiles:
            self.bag.add_data_file(df, os.path.join(datadir, df))

        self.bag.write_data_manifest(False)
        self.assertTrue(os.path.exists(manfile))
        c = 0
        fc = {}
        with open(manfile) as fd:
            for line in fd:
                c += 1
                parts = line.strip().split(' ', 1)
                self.assertEqual(len(parts), 2,
                                 "Bad manifest file syntax, line %d: %s" %
                                 (c, line.rstrip()))
                self.assertTrue(parts[1].startswith('data/'),
                                "Incorrect path name: "+parts[1])
                self.assertIn(parts[1][5:], datafiles)
                dfp = os.path.join(self.bag.bagdir, parts[1])
                self.assertTrue(os.path.exists(dfp),
                                "Datafile not found: "+parts[1])
                self.assertEqual(parts[0], bldr.checksum_of(dfp))
        self.assertEqual(c, len(datafiles))

        self.bag.write_data_manifest(True)
        self.assertTrue(os.path.exists(manfile))
        c = 0
        fc = {}
        with open(manfile) as fd:
            for line in fd:
                c += 1
                parts = line.strip().split(' ', 1)
                self.assertEqual(len(parts), 2,
                                 "Bad manifest file syntax, line %d: %s" %
                                 (c, line.rstrip()))
                self.assertTrue(parts[1].startswith('data/'),
                                "Incorrect path name: "+parts[1])
                self.assertIn(parts[1][5:], datafiles)
                dfp = os.path.join(self.bag.bagdir, parts[1])
                self.assertTrue(os.path.exists(dfp),
                                "Datafile not found: "+parts[1])
                self.assertEqual(parts[0], bldr.checksum_of(dfp))
        self.assertEqual(c, len(datafiles))

    def test_write_baginfo_data(self):
        data = self.bag.cfg['init_bag_info']
        infofile = os.path.join(self.bag.bagdir,"bag-info.txt")
        self.assertFalse(os.path.exists(infofile))

        # Make sure we can handle unicode data
        data['Description'] = u"The data is at \u03bb = 20cm."
        
        self.bag.write_baginfo_data(data, overwrite=True)

        self.assertTrue(os.path.exists(infofile))
        with open(infofile) as fd:
            lines = fd.readlines()
        self.assertIn("Source-Organization: "+
                      "National Institute of Standards and Technology\n",
                      lines)
        self.assertIn("Contact-Email: datasupport@nist.gov\n", lines)
        self.assertIn("Multibag-Version: 0.4\n", lines)
        self.assertEqual(len([l for l in lines
                                if "Organization-Address: " in l]), 2)

        data = OrderedDict([
            ("Goober-Name", "Gurn Cranston"),
            ("Foo", "Bar")
        ])
        self.bag.write_baginfo_data(data, overwrite=True)

        self.assertTrue(os.path.exists(infofile))
        with open(infofile) as fd:
            lines = fd.readlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "Goober-Name: Gurn Cranston\n")
        self.assertEqual(lines[1], "Foo: Bar\n")

        data = self.bag.cfg['init_bag_info']
        data['Foo'] = "Bang"
        self.bag.write_baginfo_data(data, overwrite=False)

        with open(infofile) as fd:
            lines = fd.readlines()
        self.assertIn("Goober-Name: Gurn Cranston\n", lines)
        self.assertIn("Foo: Bar\n", lines)
        self.assertEqual(lines[0], "Goober-Name: Gurn Cranston\n")
        self.assertEqual(lines[1], "Foo: Bar\n")
        self.assertIn("Source-Organization: "+
                      "National Institute of Standards and Technology\n",
                      lines)
        self.assertIn("Contact-Email: datasupport@nist.gov\n", lines)
        self.assertIn("Multibag-Version: 0.4\n", lines)
        self.assertEqual(len([l for l in lines
                                if "Organization-Address: " in l]), 2)
        self.assertEqual(len([l for l in lines
                                if "Foo: " in l]), 2)

    def test_update_head_version(self):
        self.bag.ensure_bagdir()
        binfo = {
            'Multibag-Tag-Directory': ["multibag"],
            'Multibag-Version': ["0.4"]
        }

        self.bag.update_head_version(binfo, "1.0.0")
        self.assertEqual(binfo['Multibag-Head-Version'], "1.0.0")
        self.assertEqual(binfo['Multibag-Version'], ["0.4"])
        self.assertEqual(binfo['Multibag-Tag-Directory'], ["multibag"])
        self.assertNotIn('Multibag-Head-Deprecates', binfo)
        
        mbdir = os.path.join(self.bag.bagdir, 'multibag')
        if not os.path.exists(mbdir):
            os.mkdir(mbdir)
        depinfo = {
            'Multibag-Tag-Directory': ["multibag"],
            'Multibag-Version': ["0.3"]
        }
        depinfof = os.path.join(mbdir, "deprecated-info.txt")
        self.bag.write_baginfo_data(depinfo, depinfof, overwrite=True)

        self.bag.update_head_version(binfo, "9.2-78")
        self.assertEqual(binfo['Multibag-Head-Version'], "9.2-78")
        self.assertEqual(binfo['Multibag-Head-Deprecates'], ["1"])
        self.assertEqual(binfo['Multibag-Version'], ["0.4"])
        self.assertEqual(binfo['Multibag-Tag-Directory'], ["multibag"])
        
        depinfo.update({
            'Multibag-Head-Version': ["8.5.1"],
            'Multibag-Head-Deprecates': ["1", "2.1.1"]
        })
        self.bag.write_baginfo_data(depinfo, depinfof, overwrite=True)

        self.bag.update_head_version(binfo, "12.1.9.2-78")
        self.assertEqual(binfo['Multibag-Head-Version'], "12.1.9.2-78")
        self.assertEqual(binfo['Multibag-Head-Deprecates'],
                         ["1", "8.5.1", "2.1.1"])
        self.assertEqual(binfo['Multibag-Version'], ["0.4"])
        self.assertEqual(binfo['Multibag-Tag-Directory'], ["multibag"])
            
    def test_ensure_baginfo(self):
        path = os.path.join("trial1","gold","trial1.json")
        datafile = os.path.join(datadir,"trial1.json")
        datafilesz = os.stat(datafile).st_size
        podfile = os.path.join(datadir, "_pod.json")

        with self.assertRaises(bldr.BagProfileError):
            self.bag.ensure_baginfo()
        self.bag.update_metadata_for("", {})
        with self.assertRaises(bldr.BagProfileError):
            self.bag.ensure_baginfo()

        self.bag.assign_id("mds00kkd13")
        self.bag.add_data_file(path, datafile)
        path = os.path.join("trial1","trial2.json")
        self.bag.add_data_file(path, datafile)
        with open(podfile) as fd:
            pod = json.load(fd)
        self.bag.add_ds_pod(pod, convert=True)

        self.bag.ensure_baginfo()

        infofile = os.path.join(self.bag.bagdir, "bag-info.txt")
        self.assertTrue(os.path.exists(infofile))
        with open(infofile) as fd:
            lines = fd.readlines()

        self.assertIn("Source-Organization: "+
                      "National Institute of Standards and Technology\n",
                      lines)
        self.assertIn("Contact-Email: datasupport@nist.gov\n", lines)
        self.assertIn("Multibag-Version: 0.4\n", lines)
        self.assertEqual(len([l for l in lines
                                if "Organization-Address: " in l]), 2)
        self.assertIn("Internal-Sender-Identifier: "+self.bag.bagname+'\n',
                      lines)
        self.assertEqual(len([l for l in lines
                                if "External-Identifier: " in l]), 2)
        wrapping = [l for l in lines if ':' not in l]
        self.assertEqual(len(wrapping), 1)
        self.assertEqual(len([l for l in wrapping if l.startswith(' ')]), 1)

        oxum = [l for l in lines if "Payload-Oxum: " in l]
        self.assertEqual(len(oxum), 1)
        oxum = [int(n) for n in oxum[0].split(': ')[1].split('.')]
        self.assertEqual(oxum[1], 2)
        self.assertEqual(oxum[0], 2*datafilesz)

        oxum = [l for l in lines if "Bag-Oxum: " in l]
        self.assertEqual(len(oxum), 1)
        oxum = [int(n) for n in oxum[0].split(': ')[1].split('.')]
        self.assertEqual(oxum[1], 14)
        self.assertEqual(oxum[0], 12176)  # this will change if logging changes

        bagsz = [l for l in lines if "Bag-Size: " in l]
        self.assertEqual(len(bagsz), 1)
        bagsz = bagsz[0]
        self.assertIn("kB", bagsz)

    def test_format_bytes(self):
        self.assertEqual(self.bag._format_bytes(108), "108 B")
        self.assertEqual(self.bag._format_bytes(34569), "34.57 kB")
        self.assertEqual(self.bag._format_bytes(9834569), "9.835 MB")
        self.assertEqual(self.bag._format_bytes(19834569), "19.83 MB")
        self.assertEqual(self.bag._format_bytes(14419834569), "14.42 GB")

    def test_write_about(self):
        self.bag.ensure_bagdir()
        with self.assertRaises(bldr.BagProfileError):
            self.bag.write_about_file()
        
        with open(os.path.join(datadir, "_nerdm.json")) as fd:
            mdata = json.load(fd)
        self.bag.add_res_nerd(mdata)
        with self.assertRaises(bldr.BagProfileError):
            self.bag.write_about_file()
        
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)

        # Make sure we can handle unicode data
        poddata['description'] += u" at \u03bb = 20cm."
        self.bag.add_ds_pod(poddata, convert=False)

        aboutfile = os.path.join(self.bag.bagdir,"about.txt")
        self.assertTrue( not os.path.exists(aboutfile) )
        self.bag.write_about_file()
        self.assertTrue( os.path.exists(aboutfile) )

        with open(aboutfile) as fd:
            lines = fd.readlines()

        # pdb.set_trace()
        self.assertIn("NIST Public Data", lines[0])
        self.assertIn("OptSortSph:", lines[2])
        self.assertIn("Zachary Levine [1] and John J. Curry [1]", lines[4])
        self.assertIn("[1] National ", lines[5])
        self.assertIn("Identifier: doi:10.18434/", lines[6])
        self.assertIn("(ark:/88434/", lines[6])
        self.assertIn("Contact: Zachary ", lines[8])
        self.assertIn(" (zachary.levine@nist.gov)", lines[8])
        self.assertIn("         100 Bureau ", lines[9])
        self.assertIn("         Mail Stop", lines[10])
        self.assertIn("         Gaithersburg, ", lines[11])
        self.assertIn("         Phone: 1-301-975-", lines[12])
        self.assertIn("Software to", lines[14])
        self.assertIn("More information:", lines[17])
        self.assertIn("https://doi.org/10.18434/", lines[18])

    def test_write_mbag_files(self):
        podfile = os.path.join(datadir, "_pod.json")
        self.bag.add_ds_pod(podfile, convert=True, savefilemd=False)
        self.assertTrue(os.path.exists(self.bag.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bag.bag.nerd_file_for('')))

        manfile = os.path.join(self.bag.bagdir, "manifest-sha256.txt")
        datafiles = [ "trial1.json", "trial2.json", 
                      os.path.join("trial3", "trial3a.json") ]
        for df in datafiles:
            self.bag.add_data_file(df, os.path.join(datadir, df))

        mbtag = os.path.join(self.bag.bagdir,"multibag", "member-bags.tsv")
        fltag = os.path.join(self.bag.bagdir,"multibag", "file-lookup.tsv")
                             
        self.assertTrue(not os.path.exists(mbtag))
        self.assertTrue(not os.path.exists(fltag))

        # pdb.set_trace()
        self.bag.write_mbag_files()

        self.assertTrue(os.path.exists(mbtag))
        self.assertTrue(os.path.exists(fltag))

        with open(mbtag) as fd:
            lines = fd.readlines()
        self.assertEqual(lines, [self.bag.bagname+'\n'])

        members = [os.path.join("data", d) for d in datafiles] + \
                  ["metadata/pod.json", "metadata/nerdm.json"] + \
                  [os.path.join("metadata", d, "nerdm.json") for d in datafiles]
        
        # FIX: component order is significant!
        # with open(fltag) as fd:
        #    i = 0;
        #    for line in fd:
        #        self.assertEqual(line.strip(), members[i]+' '+self.bag.bagname)
        #        i += 1
        #
        with open(fltag) as fd:
            lines = set([line.strip() for line in fd])
        for member in members:
            self.assertIn(member+'\t'+self.bag.bagname, lines)

            
    def test_finalize_validate(self):
        path = os.path.join("trial1","gold","trial1.json")
        datafile = os.path.join(datadir,"trial1.json")
        datafilesz = os.stat(datafile).st_size
        podfile = os.path.join(datadir, "_pod.json")

        self.bag.assign_id("mds00kkd13")
        self.bag.add_data_file(path, datafile)
        path = os.path.join("trial1","trial2.json")
        self.bag.add_data_file(path, datafile)
        with open(podfile) as fd:
            pod = json.load(fd)
        self.bag.add_ds_pod(pod, convert=True, savefilemd=False)

        self.bag.finalize_bag(stop_logging=True)
        self.bag.validate()

        self.assertTrue(os.path.isfile(os.path.join(self.bag.bagdir, "bagit.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.bag.bagdir, "bag-info.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.bag.bagdir, "about.txt")))
        self.assertTrue(os.path.isdir(os.path.join(self.bag.bagdir, "multibag")))
        
        

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

    def test_ensure_merged_annotations(self):
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        self.bag.add_ds_pod(poddata, convert=True)

        annotsrc = os.path.join(datadir, "..", "metadatabag", "metadata")
        annotfile = os.path.join(annotsrc, "annot.json")
        with open(annotfile) as fd:
            annot = json.load(fd)
        self.bag.replace_annotations_for("", annot)

        nerdfile = os.path.join(self.bag.bagdir, "metadata", "nerdm.json")
        with open(nerdfile) as fd:
            nerd = json.load(fd)
        self.assertNotIn("authors", nerd)
        self.assertNotIn("foo", nerd)
        self.assertIn("ediid", nerd)
        self.assertTrue(nerd["title"].startswith("OptSortSph: Sorting "))
        ediid = nerd['ediid']

        self.bag.ensure_merged_annotations()

        with open(nerdfile) as fd:
            nerd = json.load(fd)
        self.assertIn("authors", nerd)
        self.assertIn("foo", nerd)
        self.assertTrue(nerd['title'].startswith("OptSortSph: Sorting "))
        # self.assertEqual(nerd['title'], "A much better title")
        self.assertEqual(nerd["foo"], "bar")
        self.assertEqual(nerd['authors'][0]['givenName'], "Kevin")
        self.assertEqual(nerd['authors'][1]['givenName'], "Jianming")
        self.assertEqual(len(nerd['authors']), 2)
        self.assertEqual(nerd['ediid'], ediid)

        annotfile = os.path.join(annotsrc, "trial1.json", "annot.json")
        with open(annotfile) as fd:
            annot = json.load(fd)
        self.bag.replace_annotations_for("trial3", annot)

        dnerdfile = os.path.join(self.bag.bagdir, "metadata", "trial3",
                                 "nerdm.json")
        with open(dnerdfile) as fd:
            nerd = json.load(fd)
        self.assertNotIn('previewURL', nerd)
        self.assertNotIn('title', nerd)
            
        self.bag.ensure_merged_annotations()

        # note: this tests that running ensure_merged_annotations() twice 
        # does not change the results
        with open(nerdfile) as fd:
            nerd = json.load(fd)
        self.assertIn("authors", nerd)
        self.assertIn("foo", nerd)
        self.assertTrue(nerd['title'].startswith("OptSortSph: Sorting "))
        self.assertEqual(nerd["foo"], "bar")
        self.assertEqual(nerd['authors'][0]['givenName'], "Kevin")
        self.assertEqual(nerd['authors'][1]['givenName'], "Jianming")
        self.assertEqual(len(nerd['authors']), 2)
        self.assertEqual(nerd['ediid'], ediid)

        with open(dnerdfile) as fd:
            nerd = json.load(fd)
        self.assertIn('previewURL', nerd)
        self.assertTrue(nerd['previewURL'].endswith("trial1.json/preview"))
        self.assertEqual(nerd['title'], "a better title")





if __name__ == '__main__':
    test.main()
