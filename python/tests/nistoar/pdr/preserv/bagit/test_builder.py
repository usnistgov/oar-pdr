import os, sys, pdb, shutil, logging, json, subprocess
from cStringIO import StringIO
from shutil import copy2 as filecopy, rmtree
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.exceptions as exceptions

# datadir = nistoar/preserv/tests/data
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
    loghdlr.setLevel(logging.INFO)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestBuilder(test.TestCase):

    testsip = os.path.join(datadir, "simplesip")

    def setUp(self):
        self.tf = Tempfiles()
        self.bag = bldr.BagBuilder(self.tf.root, "testbag")
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
        self.assertIsNone(self.bag.ediid)

    def test_download_url(self):
        self.assertEqual(self.bag._download_url('goob',
                                                os.path.join("foo", "bar.json")),
                         "https://data.nist.gov/od/ds/goob/foo/bar.json")

    def test_ensure_bagdir(self):
        self.bag.ensure_bagdir()

        self.assertTrue(os.path.exists(self.bag.bagdir))

    def test_fix_id(self):
        self.assertIsNone(self.bag._fix_id(None))
        fixed = "ark:/88434/pdr06f90"
        self.assertEqual(self.bag._fix_id(fixed), fixed)
        self.assertEqual(self.bag._fix_id("Ark:/88434/pdr06f90"), fixed)
        self.assertEqual(self.bag._fix_id("ARK:/88434/pdr06f90"), fixed)
        self.assertEqual(self.bag._fix_id("/88434/pdr06f90"), fixed)
        self.assertEqual(self.bag._fix_id("88434/pdr06f90"), fixed)

        self.bag = bldr.BagBuilder(self.tf.root, "testbag", id="88434/pdr06f90")
        self.assertEqual(self.bag.id, fixed)

    def test_mint_id(self):
        ediid = 'EBC9DB05EDEA5B0EE043065706812DF81'
        self.assertEqual(self.bag._mint_id(ediid), 'ark:/88434/mds00nbc5c')
        
    def test_logging(self):
        self.test_ensure_bagdir()
        
        # test log setup
        self.assertTrue(self.bag._loghdlr)
        self.bag.record("First message")
        self.bag.log.warn("Warning")
        self.bag.log.debug("oops")
#        self.bag._unset_logfile()
        logfile = os.path.join(self.bag.bagdir,self.bag.logname)
        self.assertTrue(os.path.exists(logfile))
        with open(logfile) as fd:
            lines = fd.readlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("Created ", lines[0])
        self.assertIn(self.bag.bagname, lines[0])
        self.assertIn("First message", lines[1])
        self.assertIn("Warning", lines[2])

    def test_ensure_bag_structure(self):
        self.bag.ensure_bag_structure()

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))

        # test indepodent and extra directories
        self.bag.cfg['extra_tag_dirs'] = ['metameta']
        self.bag.ensure_bag_structure()

        self.assertTrue(os.path.exists(self.bag.bagdir))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"data")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bag.bagdir,"metameta")))
        
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


    def test_pod_file(self):
        self.assertEquals(self.bag.pod_file(),
                      os.path.join(self.bag.bagdir,"metadata","pod.json"))

    def test_nerdm_file_for(self):
        path = os.path.join("trial1","gold","file.dat")
        self.assertEquals(self.bag.nerdm_file_for(path),
                      os.path.join(self.bag.bagdir,"metadata",path,"nerdm.json"))
        self.assertEquals(self.bag.nerdm_file_for(""),
                      os.path.join(self.bag.bagdir,"metadata","nerdm.json"))

    def test_annot_file_for(self):
        path = os.path.join("trial1","gold","file.dat")
        self.assertEquals(self.bag.annot_file_for(path),
                      os.path.join(self.bag.bagdir,"metadata",path,"annot.json"))
        self.assertEquals(self.bag.annot_file_for(""),
                      os.path.join(self.bag.bagdir,"metadata","annot.json"))
        
    def test_add_metadata_for_coll(self):
        path = os.path.join("trial1","gold")
        md = { "foo": "bar", "gurn": "goob", "numbers": [ 1,3,5]}
        need = self.bag.init_collmd_for(path)
        need.update(md)

        self.bag.add_metadata_for_coll(path, md)
        mdf = os.path.join(self.bag.bagdir, "metadata", path, "nerdm.json")
        self.assertTrue(os.path.exists(mdf))
        with open(mdf) as fd:
            data = json.load(fd)
        self.assertEquals(data, need)
        
    def test_add_metadata_for_file(self):
        path = os.path.join("trial1","gold", "file.dat")
        md = { "foo": "bar", "gurn": "goob", "numbers": [ 1,3,5]}
        need = self.bag.init_filemd_for(path)
        need.update(md)

        self.bag.add_metadata_for_file(path, md)
        mdf = os.path.join(self.bag.bagdir, "metadata", path, "nerdm.json")
        self.assertTrue(os.path.exists(mdf))
        with open(mdf) as fd:
            data = json.load(fd)
        self.assertEquals(data, need)
        
    def test_init_filemd_for(self):
        path = os.path.join("trial1","gold","file.dat")
        need = {
            "@id": "cmps/"+path,
            "@type": [ "nrdp:DataFile", "dcat:Distribution" ],
            "filepath": path,
            "_extensionSchemas": [ "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile" ]
        }
        dlurl = "https://www.nist.gov/od/ds/goob/trial1/gold/file.dat"
        mdf = os.path.join(self.bag.bagdir, "metadata", path, "nerdm.json")
        self.assertFalse(os.path.exists(mdf))

        md = self.bag.init_filemd_for(path)
        self.assertEquals(md, need)
        self.assertFalse(os.path.exists(mdf))

        md = self.bag.init_filemd_for(path, True)
        self.assertTrue(os.path.exists(mdf))
        with open(mdf) as fd:
            data = json.load(fd)
        self.assertEquals(data, md)

    def test_examine(self):
        path = os.path.join("trial1","gold","trial1.json")
        need = {
            "@id": "cmps/"+path,
            "@type": [ "nrdp:DataFile", "dcat:Distribution" ],
            "filepath": path,
            "_extensionSchemas": [ "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile" ],
            "size": 69,
            "mediaType": "application/json",
            "checksum": {
                "algorithm": { "@type": "Thing", "tag": "sha256" },
                "hash": \
              "d155d99281ace123351a311084cd8e34edda6a9afcddd76eb039bad479595ec9"
            }
        }
        datafile = os.path.join(datadir, "trial1.json")

        mdata = self.bag.init_filemd_for(path, write=False, examine=datafile)
        self.assertEquals(mdata, need)

    def test_init_collmd_for(self):
        path = os.path.join("trial1","gold")
        md = self.bag.init_collmd_for(path)
        need = {
            "@id": "cmps/"+path,
            "@type": [ "nrdp:Subcollection" ],
            "filepath": path,
            "_extensionSchemas": [ "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/Subcollection" ]
        }
        mdf = os.path.join(self.bag.bagdir, "metadata", path, "nerdm.json")
        self.assertFalse(os.path.exists(mdf))

        md = self.bag.init_collmd_for(path)
        self.assertEquals(md, need)
        self.assertFalse(os.path.exists(mdf))

        md = self.bag.init_collmd_for(path, True)
        self.assertTrue(os.path.exists(mdf))
        with open(mdf) as fd:
            data = json.load(fd)
        self.assertEquals(data, md)

    def test_add_data_file(self):
        path = os.path.join("trial1","gold","trial1.json")
        bagfilepath = os.path.join(self.bag.bagdir, 'data',path)
        bagmdpath = os.path.join(self.bag.bagdir, 'metadata',path,"nerdm.json")
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertFalse( os.path.exists(bagmdpath) )

        self.bag.add_data_file(path, os.path.join(datadir,"trial1.json"))
        self.assertTrue( os.path.exists(bagfilepath) )
        self.assertTrue( os.path.exists(bagmdpath) )

        need = {
            "@id": "cmps/"+path,
            "@type": [ "nrdp:DataFile", "dcat:Distribution" ],
            "filepath": path,
            "_extensionSchemas": [ "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile" ],
            "size": 69,
            "mediaType": "application/json",
            "checksum": {
                "algorithm": { "@type": "Thing", "tag": "sha256" },
                "hash": \
              "d155d99281ace123351a311084cd8e34edda6a9afcddd76eb039bad479595ec9"
            }
        }
        with open(bagmdpath) as fd:
            data = json.load(fd)
        self.assertEqual(data, need)
        
    def test_add_data_no_file(self):
        path = os.path.join("trial1","gold","trial1.json")
        bagfilepath = os.path.join(self.bag.bagdir, 'data',path)
        bagmdpath = os.path.join(self.bag.bagdir, 'metadata',path,"nerdm.json")
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertFalse( os.path.exists(bagmdpath) )

        self.bag.add_data_file(path)
        self.assertFalse( os.path.exists(bagfilepath) )
        self.assertTrue( os.path.exists(bagmdpath) )

        need = {
            "@id": "cmps/"+path,
            "@type": [ "nrdp:DataFile", "dcat:Distribution" ],
            "filepath": path,
            "_extensionSchemas": [ "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile" ]
        }
        with open(bagmdpath) as fd:
            data = json.load(fd)
        self.assertEqual(data, need)

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
            
    def test_add_res_nerd_nofilemd(self):
        with open(os.path.join(datadir, "_nerdm.json")) as fd:
            mdata = json.load(fd)

        self.bag.add_res_nerd(mdata, False)
        ddir = os.path.join(self.bag.bagdir,"data")
        mdir = os.path.join(self.bag.bagdir,"metadata")
        nerdfile = os.path.join(mdir,"nerdm.json")
        self.assertTrue(os.path.isdir(ddir))
        self.assertTrue(os.path.isdir(mdir))
        self.assertTrue(os.path.exists(nerdfile))

        self.assertEqual(len([f for f in os.listdir(mdir)
                                if not f.startswith('.') and
                                   not f.endswith('.json')]), 0)

    def test_update_ediid(self):
        self.assertIsNone(self.bag.ediid)
        with open(os.path.join(datadir, "_nerdm.json")) as fd:
            mdata = json.load(fd)
        self.bag.add_res_nerd(mdata)
        self.assertIsNotNone(self.bag.ediid)

        destpath = "foo/bar.json"
        dlurl = "https://data.nist.gov/od/ds/"+self.bag.ediid+'/'+destpath
        self.bag.init_filemd_for(destpath, write=True)
        with open(self.bag.nerdm_file_for(destpath)) as fd:
            mdata = json.load(fd)
        self.assertTrue(mdata['downloadURL'], dlurl)

        self.bag.ediid = "gurn"

        with open(self.bag.nerdm_file_for("")) as fd:
            mdata = json.load(fd)
        self.assertEqual(mdata['ediid'], 'gurn')
        dlurl = "https://data.nist.gov/od/ds/gurn/"+destpath
        with open(self.bag.nerdm_file_for(destpath)) as fd:
            mdata = json.load(fd)
        self.assertEqual(mdata['downloadURL'], dlurl)

    def test_add_annotation_for(self):
        mdata = { "foo": "bar" }
        self.bag.add_annotation_for("goob", mdata)
        annotfile = os.path.join(self.bag.bagdir,"metadata","goob", "annot.json")
                                 
        self.assertTrue(os.path.isfile(annotfile))

        with open(annotfile) as fd:
            data = json.load(fd)
        self.assertEqual(data, mdata)
                        
        self.bag.add_annotation_for("", mdata)
        annotfile = os.path.join(self.bag.bagdir,"metadata","goob", "annot.json")
        self.assertTrue(os.path.isfile(annotfile))
        
        with open(annotfile) as fd:
            data = json.load(fd)
        self.assertEqual(data, mdata)


    def test_add_ds_pod(self):
        self.assertIsNone(self.bag.ediid)
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        self.bag.add_ds_pod(poddata, convert=False)
        self.assertTrue(os.path.exists(self.bag.pod_file()))
        self.assertIsNone(self.bag.ediid)
        with open(self.bag.pod_file()) as fd:
            data = json.load(fd)
        self.assertEqual(data, poddata)
        self.assertFalse(os.path.exists(self.bag.nerdm_file_for("")))
        self.assertFalse(os.path.exists(self.bag.nerdm_file_for("trial1.json")))
        self.assertFalse(os.path.exists(self.bag.nerdm_file_for("trial3/trial3a.json")))

    def test_add_ds_pod_convert(self):
        self.assertIsNone(self.bag.ediid)
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        self.bag.add_ds_pod(poddata, convert=True, savefilemd=False)
        self.assertTrue(os.path.exists(self.bag.pod_file()))
        self.assertEqual(self.bag.ediid, poddata['identifier'])

        nerdfile = self.bag.nerdm_file_for("")
        self.assertTrue(os.path.exists(nerdfile))
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEqual(data['modified'], poddata['modified'])
        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertFalse(os.path.exists(self.bag.nerdm_file_for("trial1.json")))
        self.assertFalse(os.path.exists(self.bag.nerdm_file_for("trial3/trial3a.json")))

    def test_add_ds_pod_filemd(self):
        podfile = os.path.join(datadir, "_pod.json")
        with open(podfile) as fd:
            poddata = json.load(fd)
        #pdb.set_trace()
        self.bag.add_ds_pod(poddata, convert=True, savefilemd=True)
        self.assertTrue(os.path.exists(self.bag.pod_file()))

        nerdfile = self.bag.nerdm_file_for("")
        self.assertTrue(os.path.exists(nerdfile))
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEqual(data['modified'], poddata['modified'])
        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertTrue(os.path.exists(self.bag.nerdm_file_for("trial1.json")))
        self.assertTrue(os.path.exists(self.bag.nerdm_file_for("trial3/trial3a.json")))
        nerdfile = self.bag.nerdm_file_for("trial3/trial3a.json")
        with open(nerdfile) as fd:
            data = json.load(fd)
        self.assertEquals(data['filepath'], "trial3/trial3a.json")
        self.assertEquals(data['@id'], "cmps/trial3/trial3a.json")

    def test_remove_component(self):
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
        self.bag.init_filemd_for(path, write=True,
                                 examine=os.path.join(datadir,"trial1.json"))
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

    def test_remove_component_trim(self):
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


class TestChecksum(test.TestCase):

    def test_checksum_of(self):
        dfile = os.path.join(datadir,"trial1.json")
        self.assertEqual(bldr.checksum_of(dfile), self.syssum(dfile))
        dfile = os.path.join(datadir,"trial2.json")
        self.assertEqual(bldr.checksum_of(dfile), self.syssum(dfile))
        dfile = os.path.join(datadir,"trial3/trial3a.json")
        self.assertEqual(bldr.checksum_of(dfile), self.syssum(dfile))

    def syssum(self, filepath):
        cmd = ["sha256sum", filepath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(err + "\nFailed sha256sum command: " +
                               " ".join(cmd))
        return out.split()[0]

if __name__ == '__main__':
    test.main()
