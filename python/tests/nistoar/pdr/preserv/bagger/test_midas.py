# These unit tests test the nistoar.pdr.preserv.bagger.midas module.  These tests
# do not include support for updating previously published datasets (via use of 
# the UpdatePrepService class).  Because testing support for updates require 
# simulated RMM and distribution services to be running, they have been 
# seperated out into test_midas_update.py.
#
from __future__ import print_function
import os, sys, pdb, shutil, logging, json, time
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit import NISTBag
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.preserv import AIPValidationError

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

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
    rootlog.setLevel(logging.DEBUG)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

def to_dict(odict):
    out = dict(odict)
    for prop in out:
        if isinstance(out[prop], OrderedDict):
            out[prop] = to_dict(out[prop])
        if isinstance(out[prop], (list, tuple)):
            for i in range(len(out[prop])):
                if isinstance(out[prop][i], OrderedDict):
                    out[prop][i] = to_dict(out[prop][i])
    return out


class TestMIDASMetadataBaggerMixed(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    wrongid = '333333333333333333333333333333331491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, self.upldir)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "review")
        self.assertEqual(len(self.bagr._indirs), 2)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.revdir, self.midasid[32:]))
        self.assertEqual(self.bagr._indirs[1],
                         os.path.join(self.upldir, self.midasid[32:]))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))
        self.assertFalse(os.path.exists(self.bagdir))

    def test_wrong_ediid(self):
        with self.assertRaises(midas.SIPDirectoryNotFound):
            self.bagr = midas.MIDASMetadataBagger(self.wrongid, self.bagparent,
                                                  self.revdir, self.upldir)

    def test_ark_ediid(self):
        indir = os.path.join(self.bagparent, os.path.basename(self.testsip))
        shutil.copytree(self.testsip, indir)
        self.upldir = os.path.join(indir, "upload")
        self.revdir = os.path.join(indir, "review")

        podf = os.path.join(self.upldir,"1491","_pod.json")
        with open(podf) as fd:
            pod = json.load(fd)
        pod['identifier'] = self.arkid
        with open(podf, 'w') as fd:
            json.dump(pod, fd, indent=2)
        podf = os.path.join(self.revdir,"1491","_pod.json")
        with open(podf, 'w') as fd:
            json.dump(pod, fd, indent=2)

        cfg = { 'bag_builder': { 'validate_id': r'(pdr\d)|(mds[01])' } }
        
        self.bagr = midas.MIDASMetadataBagger(self.arkid, self.bagparent,
                                              self.revdir, self.upldir,
                                              config=cfg)
        self.assertEqual(self.bagr.midasid, self.arkid)
        self.assertEqual(self.bagr.name, self.arkid[11:])
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.revdir, self.arkid[16:]))
        self.assertEqual(self.bagr._indirs[1],
                         os.path.join(self.upldir, self.arkid[16:]))

        self.assertEqual(os.path.basename(self.bagr.bagbldr.bagdir),
                         self.arkid[11:])

        self.bagr.ensure_base_bag()
        self.assertEqual(self.bagr.bagbldr.id, self.arkid)
        self.assertEqual(os.path.basename(self.bagr.bagbldr.bag.dir),
                         self.arkid[11:])

        self.bagr.ensure_res_metadata(True)
        nerdm = self.bagr.bagbldr.bag.nerd_metadata_for('')
        self.assertEqual(nerdm['ediid'], self.arkid)
        self.assertEqual(nerdm['@id'], self.arkid)

    def test_find_pod_file(self):
        self.assertEqual(self.bagr.find_pod_file(),
                         os.path.join(self.upldir,self.midasid[32:],'_pod.json'))
        self.assertIsNone(self.bagr.inpodfile)

    def test_set_pod_file(self):
        self.assertIsNone(self.bagr.inpodfile)
        self.bagr._set_pod_file()
        self.assertEqual(self.bagr.inpodfile,
                         os.path.join(self.upldir,self.midasid[32:],'_pod.json'))

    def test_ensure_res_metadata(self):
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.inpodfile)
        self.bagr.ensure_res_metadata()
        
        self.assertTrue(os.path.exists(self.bagdir))
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertTrue(os.path.exists(metadir))
        self.assertTrue(os.path.exists(os.path.join(metadir, "pod.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir, "nerdm.json")))
        self.assertEqual(self.bagr.inpodfile,
                         os.path.join(self.upldir,self.midasid[32:],"_pod.json"))

        data = midas.read_pod(os.path.join(metadir, "pod.json"))
        self.assertIsInstance(data, OrderedDict)
        src = midas.read_pod(self.bagr.inpodfile)
        self.assertEqual(data, src)
        self.assertEqual(data.keys(), src.keys())  # confirms same order

        self.assertIsNotNone(self.bagr.resmd)
        data = self.bagr.bagbldr.bag.nerd_metadata_for("", True)

        # should contain only non-file components:
        self.assertEqual(len(data['components']), 1)
        self.assertIsInstance(data, OrderedDict)
        self.assertNotIn('inventory', data)
        src = deepcopy(self.bagr.resmd)
        del data['components']
        del src['components']
        if 'inventory' in src: del src['inventory']
        if 'dataHierarchy' in src: del src['dataHierarchy']
        self.assertEqual(to_dict(data), to_dict(src))
        self.assertEqual(data.keys(), src.keys())  # same order

        # spot check some key NERDm properties
        data = self.bagr.resmd
        self.assertNotIn('@id', data)
        self.assertEqual(data['ediid'], self.midasid)
        self.assertEqual(data['doi'], "doi:10.18434/T4SW26")
        self.assertNotIn('foo', data)
        self.assertEqual(len(data['components']), 7)
        self.assertEqual(data['components'][0]['@type'][0], 'nrd:Hidden')
        self.assertIsInstance(data['@context'], list)
        self.assertEqual(len(data['@context']), 2)

        # make sure file components were registered
        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("trial1.json")))

        # ensure indepodence, non-redundance
        data = self.bagr.bagbldr.bag.nerd_metadata_for("")
        data['foo'] = "bar"
        data['doi'] = "doi:10.18434/FAKE"
        utils.write_json(data, self.bagr.bagbldr.bag.nerd_file_for(""))
        self.bagr.bagbldr.assign_id("ark:/88434/mds00hw91v")
        self.bagr.ensure_res_metadata()
        data = self.bagr.bagbldr.bag.nerd_metadata_for("")
        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertEqual(data['ediid'], self.midasid)
        self.assertEqual(data['doi'], "doi:10.18434/FAKE")
        self.assertEqual(data['foo'], "bar")
        self.assertEqual(len(data['components']), 1)
        self.assertEqual(data['components'][0]['@type'][0], 'nrd:Hidden')
        self.assertIsInstance(data['@context'], list)
        self.assertEqual(len(data['@context']), 2)
        self.assertEqual(data['@context'][1]['@base'], data['@id'])

        self.bagr.ensure_res_metadata(force=True)
        data = self.bagr.bagbldr.bag.nerd_metadata_for("")
        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertEqual(data['ediid'], self.midasid)
        self.assertEqual(data['doi'], "doi:10.18434/T4SW26")
        self.assertEqual(data['foo'], 'bar')
        self.assertEqual(len(data['components']), 1)
        self.assertEqual(data['components'][0]['@type'][0], 'nrd:Hidden')
        self.assertIsInstance(data['@context'], list)
        self.assertEqual(len(data['@context']), 2)
        self.assertEqual(data['@context'][1]['@base'], data['@id'])

    def test_ensure_res_metadata_wremove(self):
        # don't use upload version of pod file
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, None)

        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.inpodfile)
        self.bagr.ensure_res_metadata()

        # make sure file components were registered
        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("trial1.json")))
        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("trial1.json.sha256")))

        # add metadata for a data file that doesn't exist in the source dir
        self.bagr.bagbldr.register_data_file(os.path.join("gold","trial5.json"),
                                             os.path.join(self.revdir,
                                                          self.midasid[32:],
                                                          "trial1.json") )
        self.bagr.bagbldr.register_data_file(os.path.join("gold","trial5.json.sha256"),
                                             os.path.join(self.revdir,
                                                          self.midasid[32:],
                                                          "trial1.json.sha256") )
        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("gold/trial5.json")))
        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("gold/trial5.json.sha256")))

        # now watch it get erased
        self.bagr.ensure_res_metadata(force=True)
        self.assertTrue(not os.path.exists(
            self.bagr.bagbldr.bag.nerd_file_for("gold/trial5.json")))
        self.assertTrue(not os.path.exists(
            self.bagr.bagbldr.bag.nerd_file_for("gold/trial5.json.sha256")))
        self.assertTrue(not os.path.exists(
            self.bagr.bagbldr.bag.nerd_file_for("gold")))
        self.assertTrue(not os.path.exists(
            os.path.dirname(self.bagr.bagbldr.bag.nerd_file_for("gold"))))

    doiclientinfo = {
        "app_name": "NIST Open Access for Research: oar-pdr",
        "app_version": "testing",
        "app_url": "http://github.com/usnistgov/oar-pdr/",
        "email": "datasupport@nist.gov"
    }

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_ensure_res_metadata_enhanced_refs(self):
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.inpodfile)

        cfg = {
            'enrich_refs': False,
            'doi_resolver': {
                'client_info': self.doiclientinfo
            }
        }
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, self.upldir, cfg)
        self.bagr.ensure_res_metadata()
        self.assertEqual(len(self.bagr.resmd['references']), 1)
        self.assertIn('doi.org', self.bagr.resmd['references'][0]['location'])
        self.assertNotIn('citation', self.bagr.resmd['references'][0])

        cfg['enrich_refs'] = True
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, self.upldir, cfg)
        self.bagr.ensure_res_metadata(True)
        self.assertEqual(len(self.bagr.resmd['references']), 1)
        self.assertIn('doi.org', self.bagr.resmd['references'][0]['location'])
        self.assertIn('citation', self.bagr.resmd['references'][0])

        rmd = self.bagr.bagbldr.bag.nerd_metadata_for('', False)
        self.assertEqual(len(rmd['references']), 1)
        self.assertIn('doi.org', rmd['references'][0]['location'])
        self.assertNotIn('citation', rmd['references'][0])
        
        rmd = self.bagr.bagbldr.bag.annotations_metadata_for('')
        self.assertEqual(len(rmd['references']), 1)
        self.assertIn('doi.org', rmd['references'][0]['location'])
        self.assertIn('citation', rmd['references'][0])
        
        

    def test_ensure_file_metadata(self):
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.bagbldr.ediid)
        self.bagr.bagbldr.ediid = "gurn"

        destpath = os.path.join("trial3", "trial3a.json")
        dlurl = "https://data.nist.gov/od/ds/gurn/"+destpath
        dfile = os.path.join(self.upldir, self.midasid[32:], destpath)
        self.bagr.ensure_file_metadata(dfile, destpath)

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))
        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "annot.json")
        self.assertTrue(not os.path.exists(mdfile))

        data = self.bagr.bagbldr.bag.nerd_metadata_for(destpath, True)
        self.assertEqual(data['size'], 69)
        self.assertTrue(data['checksum']['hash'])
        self.assertEqual(data['downloadURL'], dlurl)
        self.assertNotIn('description', data)

    def test_ensure_file_metadata_checksumfile(self):
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.bagbldr.ediid)
        self.bagr.bagbldr.ediid = "gurn"

        destpath = os.path.join("trial3", "trial3a.json.sha256")
        dlurl = "https://data.nist.gov/od/ds/gurn/"+destpath
        dfile = os.path.join(self.revdir, self.midasid[32:], destpath)
        self.bagr.ensure_file_metadata(dfile, destpath)

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))

        data = self.bagr.bagbldr.bag.nerd_metadata_for(destpath, True)
        self.assertEqual(data['@type'][0], "nrdp:ChecksumFile")
        self.assertEqual(data['@type'][1], "nrdp:DownloadableFile")
        self.assertEqual(data['@type'][2], "dcat:Distribution")
        self.assertEqual(len(data['@type']), 3)
        self.assertTrue(data['_extensionSchemas'][0]
                        .endswith("#/definitions/ChecksumFile"))
        self.assertEqual(data['size'], 65)
        self.assertTrue(data['checksum']['hash'])
        self.assertEqual(data['downloadURL'], dlurl)
        self.assertEqual(data['describes'],
                         "cmps/"+os.path.splitext(destpath)[0])
        self.assertTrue(data['description'].startswith("SHA-256 checksum"))

    def test_ensure_data_files(self):
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        self.assertIsNotNone(self.bagr.datafiles)
        self.assertEqual(len(self.bagr.datafiles), 4)
        self.assertEqual(len([d for d in self.bagr.datafiles.keys()
                                if d.endswith(".sha256")]), 1)

        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))
            comp = self.bagr.bagbldr.bag.nerd_metadata_for(filepath)
            self.assertIn('size', comp)
            self.assertIn('checksum', comp)
        
    def test_check_checksum_files(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        valid = []
        invalid = []
        unknn = []
        for comp in self.bagr.resmd.get('components',[]):
            if not any([":ChecksumFile" in t for t in comp.get('@type',[])]):
                continue
            if 'valid' not in comp:
                unknn.append(comp['filepath'])
            elif comp['valid'] is True:
                valid.append(comp['filepath'])
            else:
                invalid.append(comp['filepath'])

        self.assertEqual(len(unknn) + len(valid) + len(invalid), 1)
        self.assertEqual(unknn, [])
        self.assertEqual(valid, [])
        self.assertEqual(invalid, ["trial3/trial3a.json.sha256"])
        
        
    def test_ensure_subcoll_metadata(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_subcoll_metadata()

        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        mdata = self.bagr.bagbldr.bag.nerd_metadata_for("trial3", True)
        self.assertEqual(mdata['filepath'], "trial3")
        self.assertIn("nrdp:Subcollection", mdata['@type'])

    def test_ensure_preparation(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_preparation()

        # has resource-level metadata
        self.assertTrue(os.path.exists(os.path.join(metadir, "pod.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir, "nerdm.json")))

        # has file metadata
        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))

        # has subcollection metadata
        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        mdata = self.bagr.bagbldr.bag.nerd_metadata_for("trial3", True)
        self.assertEqual(mdata['filepath'], "trial3")
        self.assertIn("nrdp:Subcollection", mdata['@type'])
        
    def test_ensure_preparation(self):
        self.assertIsNone(self.bagr.fileExaminer)

        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.prepare()
        self.assertIsNotNone(self.bagr.datafiles)
        self.assertFalse(not os.path.exists(self.bagdir))
        
    def test_registered_files(self):
        uplsip = os.path.join(self.upldir, self.midasid[32:])
        revsip = os.path.join(self.revdir, self.midasid[32:])

        self.assertEquals(self.bagr.registered_files(), {})

        self.bagr.ensure_res_metadata()

        datafiles = self.bagr.registered_files()
        self.assertIsInstance(datafiles, dict)
        self.assertIn("trial1.json", datafiles)
        self.assertNotIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        # copy of trial3a.json in upload overrides
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 4)

    def test_available_files(self):
        uplsip = os.path.join(self.upldir, self.midasid[32:])
        revsip = os.path.join(self.revdir, self.midasid[32:])

        datafiles = self.bagr.available_files()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 5)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        # copy of trial3a.json in upload overrides
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 5)

    def test_baggermd_file_for(self):
        self.bagr.ensure_base_bag()
        self.assertEqual(self.bagr.baggermd_file_for(''),
                         os.path.join(self.bagr.bagbldr.bag.metadata_dir,"__bagger.json"))

        self.bagr.ensure_res_metadata()
        self.assertEqual(self.bagr.baggermd_file_for("trial1.json"), 
                         os.path.join(self.bagr.bagbldr.bag.metadata_dir,"trial1.json",
                                      "__bagger.json"))

    def test_baggermd_for(self):
        self.bagr.ensure_base_bag()
        bgmdf = os.path.join(self.bagr.bagbldr.bag.metadata_dir,"__bagger.json")
        self.assertFalse(os.path.exists(bgmdf))

        self.assertEqual(self.bagr.baggermd_for(''), {})
        self.assertFalse(os.path.exists(bgmdf))
        with open(bgmdf, 'w') as fd:
            json.dump({"a": 1, "b": 2}, fd)
        self.assertEqual(self.bagr.baggermd_for(''), {"a": 1, "b": 2})

    def test_update_bagger_metadata_for(self):
        self.bagr.ensure_base_bag()
        bgmdf = os.path.join(self.bagr.bagbldr.bag.metadata_dir,"__bagger.json")
        self.assertFalse(os.path.exists(bgmdf))

        self.bagr.update_bagger_metadata_for('', {})
        self.assertTrue(os.path.exists(bgmdf))
        with open(bgmdf) as fd:
            saved = json.load(fd)
        self.assertEqual(saved, {})

        self.bagr.update_bagger_metadata_for('', {"a": 1, "b": 2})
        with open(bgmdf) as fd:
            saved = json.load(fd)
        self.assertEqual(saved, {"a": 1, "b": 2})

        self.bagr.update_bagger_metadata_for('', {"c": 8, "b": 5})
        with open(bgmdf) as fd:
            saved = json.load(fd)
        self.assertEqual(saved, {"a": 1, "b": 5, "c": 8})

        
        


class TestMIDASMetadataBaggerReview(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.revdir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "review")
        self.assertEqual(len(self.bagr._indirs), 1)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.revdir, self.midasid[32:]))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))
        self.assertIsNone(self.bagr.fileExaminer)

    def test_find_pod_file(self):
        self.assertEquals(self.bagr.find_pod_file(),
                         os.path.join(self.revdir,self.midasid[32:],'_pod.json'))

    def test_ensure_data_files(self):
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        self.assertIsNotNone(self.bagr.datafiles)
        self.assertEqual(len(self.bagr.datafiles), 5)
        self.assertEqual(len([d for d in self.bagr.datafiles.keys()
                                if d.endswith(".sha256")]), 2)

        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))
            comp = self.bagr.bagbldr.bag.nerd_metadata_for(filepath)
            self.assertIn('size', comp)
            self.assertIn('checksum', comp)
        
    def test_check_checksum_files(self):
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        valid = []
        invalid = []
        unknn = []
        for comp in self.bagr.resmd.get('components',[]):
            if not any([":ChecksumFile" in t for t in comp.get('@type',[])]):
                continue
            if 'valid' not in comp:
                unknn.append(comp['filepath'])
            elif comp['valid'] is True:
                valid.append(comp['filepath'])
            else:
                invalid.append(comp['filepath'])

        self.assertEqual(len(unknn) + len(valid) + len(invalid), 2)
        self.assertEqual(unknn, [])
        self.assertEqual(invalid, [])
        self.assertIn("trial3/trial3a.json.sha256", valid)
        self.assertIn("trial1.json.sha256", valid)
        
        
    def test_registered_files(self):
        revsip = os.path.join(self.revdir, self.midasid[32:])

        self.assertEquals(self.bagr.registered_files(), {})

        self.bagr.ensure_res_metadata()

        datafiles = self.bagr.registered_files()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 5)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(revsip, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 5)

    def test_available_files(self):
        revsip = os.path.join(self.revdir, self.midasid[32:])

        datafiles = self.bagr.available_files()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 5)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(revsip, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 5)

    def test_fileExaminer(self):
        # turn on asyncexamine (but turn off autolaunch so that we can test
        # more easily).  Show that the checksum is not calculated for
        # trial2.json.  Start the asynchronous thread; after it is done,
        # show that trial2.json now has a checksum.  
        
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, asyncexamine=True)
        self.assertIsNotNone(self.bagr.fileExaminer)
        self.bagr.fileExaminer_autolaunch = False

        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.prepare()
        self.assertTrue(os.path.exists(self.bagdir))
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIn('checksum', fmd) # because there's a .sha256 file
        self.assertIn('_status', fmd)
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIn('_status', fmd)
        self.assertNotIn('checksum', fmd)

        # self.bagr.fileExaminer.run()
        self.bagr.fileExaminer.launch()
        self.bagr.fileExaminer.thread.join()
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIn('checksum', fmd)
        self.assertNotIn('_status', fmd)

    def test_fileExaminer_autolaunch(self):
        # show that the async thread does its work with autolaunch
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, asyncexamine=True)
        self.assertIsNotNone(self.bagr.fileExaminer)
        # self.bagr.fileExaminer_autolaunch = True

        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        try:
            self.bagr.prepare()
        except Exception as ex:
            self.bagr.fileExaminer.thread.join()
            raise
        self.assertTrue(os.path.exists(self.bagdir))
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIn('checksum', fmd) # because there's a .sha256 file

#        time.sleep(0.1)
        if self.bagr.fileExaminer.thread.is_alive():
            print("waiting for file examiner thread")
            n = 20
            while n > 0 and self.bagr.fileExaminer.thread.is_alive():
                n -= 1
                time.sleep(0.1)
            if n == 0:
                self.fail("file examiner is taking too long")    
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIn('checksum', fmd)



class TestMIDASMetadataBaggerUpload(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "upload")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              None, self.upldir)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "upload")
        self.assertEqual(len(self.bagr._indirs), 1)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.upldir, self.midasid[32:]))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))

    def test_find_pod_file(self):
        self.assertEquals(self.bagr.find_pod_file(),
                          os.path.join(self.upldir,self.midasid[32:],'_pod.json'))

    def test_ensure_data_files(self):
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        self.assertIsNotNone(self.bagr.datafiles)
        self.assertEqual(len(self.bagr.datafiles), 1)
        self.assertEqual(len([d for d in self.bagr.datafiles.keys()
                                if d.endswith(".sha256")]), 0)

        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))
            comp = self.bagr.bagbldr.bag.nerd_metadata_for(filepath)
            self.assertIn('size', comp)
            self.assertIn('checksum', comp)
        
    def test_check_checksum_files(self):
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        valid = []
        invalid = []
        unknn = []
        for comp in self.bagr.resmd.get('components',[]):
            if not any([":ChecksumFile" in t for t in comp.get('@type',[])]):
                continue
            if 'valid' not in comp:
                unknn.append(comp['filepath'])
            elif comp['valid'] is True:
                valid.append(comp['filepath'])
            else:
                invalid.append(comp['filepath'])

        self.assertEqual(len(unknn) + len(valid) + len(invalid), 1)
        self.assertEqual(unknn, ['trial3/trial3a.json.sha256'])
        self.assertEqual(invalid, [])
        self.assertEqual(valid, [])
        
        
    def test_registered_files(self):
        uplsip = os.path.join(self.upldir, self.midasid[32:])

        self.assertEquals(self.bagr.registered_files(), {})

        self.bagr.ensure_res_metadata()

        datafiles = self.bagr.registered_files()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 1)
        self.assertNotIn("trial1.json", datafiles)
        self.assertNotIn("trial1.json.sha256", datafiles)
        self.assertNotIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertNotIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 1)

    def test_available_files(self):
        uplsip = os.path.join(self.upldir, self.midasid[32:])

        datafiles = self.bagr.available_files()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 1)
        self.assertNotIn("trial1.json", datafiles)
        self.assertNotIn("trial1.json.sha256", datafiles)
        self.assertNotIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertNotIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 1)





class TestPreservationBagger(test.TestCase):
    
    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("bagger")
        self.mddir = os.path.join(self.workdir, "mddir")
        os.mkdir(self.mddir)

        # TODO: copy input data to writable location
        testsip = os.path.join(self.testsip, "review")
        self.revdir = os.path.join(self.workdir, "review")
        shutil.copytree(testsip, self.revdir)
        config = {
            'relative_to_indir': True,
            'bag_builder': {
                'validate_id': r'(pdr\d)|(mds[01])',
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
            'store_dir': '/tmp'
        }
        
        self.bagr = midas.PreservationBagger(self.midasid, '_preserv',
                                             self.revdir, self.mddir, config)
        self.sipdir = os.path.join(self.revdir, "1491")
        self.bagparent = os.path.join(self.sipdir, "_preserv")

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.indir, self.sipdir)
        self.assertEqual(self.bagr.mddir, self.mddir)
        self.assertEqual(self.bagr.bagparent, self.bagparent)
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertTrue(os.path.exists(self.bagparent))

        bagdir = os.path.join(self.bagparent, self.midasid+".1_0.mbag0_4-0")
        self.assertEqual(self.bagr.bagdir, bagdir)

    def test_ark_ediid(self):
        podf = os.path.join(self.sipdir,"_pod.json")
        with open(podf) as fd:
            pod = json.load(fd)
        pod['identifier'] = self.arkid
        with open(podf, 'w') as fd:
            json.dump(pod, fd, indent=2)

        bagname = self.arkid[11:]+".1_0.mbag0_4-0"

        self.bagr = midas.PreservationBagger(self.arkid, '_preserv',
                                             self.revdir, self.mddir,
                                             self.bagr.cfg)
        self.assertEqual(self.bagr.midasid, self.arkid)
        self.assertEqual(self.bagr.name, self.arkid[11:])
        self.assertEqual(self.bagr.indir,
                         os.path.join(self.revdir, self.arkid[16:]))
        self.assertEqual(os.path.basename(self.bagr.bagdir), bagname)
        self.assertEqual(os.path.basename(self.bagr.bagbldr.bagdir), bagname)

        self.bagr.ensure_metadata_preparation()
        self.assertEqual(self.bagr.bagbldr.id, self.arkid)
        self.assertEqual(os.path.basename(self.bagr.bagbldr.bag.dir), bagname)

        nerdm = self.bagr.bagbldr.bag.nerd_metadata_for('')
        self.assertEqual(nerdm['ediid'], self.arkid)
        self.assertEqual(nerdm['@id'], self.arkid)


    def test_find_pod_file(self):
        podfile = self.bagr.find_pod_file()
        self.assertEqual(os.path.basename(podfile), "_pod.json")
        self.assertEqual(podfile, os.path.join(self.bagr.indir, "_pod.json"))

    def test_form_bag_name(self):
        self.bagr.cfg['mbag_version'] = "1.2"
        bagname = self.bagr.form_bag_name("goober", 3, "1.0.1")
        self.assertEqual(bagname, "goober.1_0_1.mbag1_2-3")

    def test_ensure_metadata_preparation(self):
        self.bagr.ensure_metadata_preparation()
        self.assertTrue(os.path.exists(self.bagr.bagdir),
                        "Output bag dir not created")
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir, "data")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "preserv.log")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "metadata", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                      "metadata", "trial1.json", "nerdm.json")))

        # data files do not yet appear in output bag
        self.assertTrue(not os.path.isdir(os.path.join(self.bagr.bagdir,
                                                       "data", "trial1.json")),
                        "Datafiles copied prematurely")
        

    def test_preparation(self):
        self.bagr.ensure_preparation()
        self.assertTrue(os.path.exists(self.bagr.bagdir),
                        "Output bag dir not created")
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir, "data")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "preserv.log")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "metadata", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                      "metadata", "trial1.json", "nerdm.json")))

        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "data", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "data", "trial2.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                             "data", "trial3", "trial3a.json")))
        
    def test_make_bag(self):
        try:
            self.bagr.make_bag()
        except AIPValidationError as ex:
            self.fail(ex.description)
            
        self.assertTrue(os.path.exists(self.bagr.bagdir),
                        "Output bag dir not created")
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir, "data")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "preserv.log")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "metadata", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                      "metadata", "trial1.json", "nerdm.json")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "metadata", "trial2.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                      "metadata", "trial2.json", "nerdm.json")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                          "metadata", "trial3", "trial3a.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                            "metadata", "trial3", "trial3a.json", "nerdm.json")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "metadata", "sim++.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                      "metadata", "sim++.json", "nerdm.json")))

        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "data", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "data", "trial2.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                             "data", "trial3", "trial3a.json")))
        self.assertFalse(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                     "data", "sim++.json")))

        # test if we lost the downloadURLs
        mdf = os.path.join(self.bagr.bagdir,
                           "metadata", "trial1.json", "nerdm.json")
        with open(mdf) as fd:
            md = json.load(fd)
        self.assertIn("checksum", md)
        self.assertIn("size", md)
        self.assertIn("mediaType", md)
        self.assertIn("nrdp:DataFile", md.get("@type", []))
        self.assertIn("dcat:Distribution", md.get("@type", []))
        self.assertIn("downloadURL", md)
        self.assertIn("title", md)
        self.assertEqual(md.get("title"),
                         "JSON version of the Mathematica notebook")
        
        # test for BagIt-required files
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                    "bagit.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                    "bag-info.txt")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                    "manifest-sha256.txt")))
        
        # test for NIST-required files
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "multibag")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                            "multibag", "member-bags.tsv")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                            "multibag", "file-lookup.tsv")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "about.txt")))

        # make sure we could've found missing files
        self.bagr._check_data_files(self.bagr.cfg.get('data_checker',{}))
        with self.assertRaises(AIPValidationError):
            self.bagr._check_data_files(self.bagr.cfg.get('data_checker',{}),
                                        viadistrib=False)

    def test_determine_updated_version(self):
        self.bagr.prepare(nodata=False)
        bag = NISTBag(self.bagr.bagdir)
        mdrec = bag.nerdm_record(True)
        self.assertEqual(mdrec['version'], '1.0.0')  # set as the default

        del mdrec['version']
        newver = self.bagr.determine_updated_version(mdrec, bag)
        self.assertEqual(newver, "1.0.0")
        newver = self.bagr.determine_updated_version(mdrec)
        self.assertEqual(newver, "1.0.0")
        newver = self.bagr.determine_updated_version()
        self.assertEqual(newver, "1.0.0")

        newver = self.bagr.determine_updated_version(mdrec, bag)
        self.assertEqual(newver, "1.0.0")
        newver = self.bagr.determine_updated_version(mdrec)
        self.assertEqual(newver, "1.0.0")
        newver = self.bagr.determine_updated_version()
        self.assertEqual(newver, "1.0.0")

        mdrec['version'] = "9.0"
        newver = self.bagr.determine_updated_version(mdrec)
        self.assertEqual(newver, "9.0")

        mdrec['version'] = "1.0.5+ (in edit)"
        newver = self.bagr.determine_updated_version(mdrec)
        self.assertEqual(newver, "1.1.0")

    def test_determine_updated_version_minor(self):
        self.bagr.prepare(nodata=True)
        bag = NISTBag(self.bagr.bagdir)
        mdrec = bag.nerdm_record(True)

        mdrec['version'] = "1.0.5+ (in edit)"
        newver = self.bagr.determine_updated_version(mdrec)
        self.assertEqual(newver, "1.0.6")
        
    def test_finalize_version(self):
        self.bagr.prepare(nodata=True)

        bag = NISTBag(self.bagr.bagdir)
        mdrec = bag.nerdm_record(True)
        self.assertEqual(mdrec['version'], "1.0.0")

        self.bagr.finalize_version()
        mdrec = bag.nerdm_record(True)
        self.assertEqual(mdrec['version'], "1.0.0")

        annotf = os.path.join(bag.metadata_dir, "annot.json")
        data = utils.read_nerd(annotf)
        self.assertEqual(data['version'], "1.0.0")

        self.bagr.bagbldr.update_annotations_for('',
                                                 {'version': "1.0.0+ (in edit)"})
        data = utils.read_nerd(annotf)
        self.assertEqual(data['version'], "1.0.0+ (in edit)")

        self.bagr.finalize_version()
        data = utils.read_nerd(annotf)
        self.assertEqual(data['version'], "1.0.1")
        self.assertIn('versionHistory', data)

        mdrec = bag.nerdm_record(True)
        self.assertEqual(mdrec['version'], "1.0.1")
        self.assertIn('versionHistory', mdrec)
        hist = mdrec['versionHistory']
        self.assertEqual(hist[-1]['version'], "1.0.1")
        self.assertEqual(hist[-1]['description'], "metadata update")
            

        
        
        

if __name__ == '__main__':
    test.main()
