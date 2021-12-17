# These unit tests test the nistoar.pdr.preserv.bagger.midas3 module.  These tests
# do not include support for updating previously published datasets (via use of 
# the UpdatePrepService class).  Because testing support for updates require 
# simulated RMM and distribution services to be running, they have been 
# seperated out into test_midas3_update.py.
#
from __future__ import print_function
import os, sys, pdb, shutil, logging, json, time, re
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict, Mapping
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit import NISTBag
import nistoar.pdr.preserv.bagger.midas3 as midas
from nistoar.pdr.preserv.bagger import utils as bagutils
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
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_bagger.log"))
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

class TestMIDASSIPMixed(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    wrongid = '333333333333333333333333333333331491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.sip = midas.MIDASSIP(self.midasid, os.path.join(self.revdir, "1491"),
                                  os.path.join(self.upldir, "1491"))

    def test_ctor(self):
        self.assertEqual(self.sip.input_dirs, (self.sip.revdatadir, self.sip.upldatadir))
        self.assertIsNone(self.sip.nerd)
        self.assertIsNone(self.sip.pod)
        self.assertEqual(self.sip._pod_rec(), {'distribution': []})
        self.assertEqual(self.sip._nerdm_rec(), {'components': []})
        self.assertIsNone(self.sip.get_ediid())
        self.assertIsNone(self.sip.get_pdrid())

        self.assertEqual(self.sip._filepaths_in_pod(), [])
        self.assertEqual(self.sip._filepaths_in_nerd(), [])
        self.assertEqual(self.sip.list_registered_filepaths(), [])
        self.assertEqual(self.sip.list_registered_filepaths(True), [])


    def test_pod_rec(self):
        self.sip.pod = os.path.join(self.sip.revdatadir, "_pod.json")
        self.assertTrue(os.path.isfile(self.sip.pod))
        pod = self.sip._pod_rec()
        self.assertEqual(pod['accessLevel'], "public")
        self.assertEqual(pod['identifier'], self.midasid)

        self.assertEqual(self.sip.get_ediid(), self.midasid)

        self.sip.pod = pod
        pod = self.sip._pod_rec()
        self.assertEqual(pod['accessLevel'], "public")
        self.assertEqual(pod['identifier'], self.midasid)
        

    def test_available_files(self):
        datafiles = self.sip.available_files()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 5)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(self.sip.revdatadir, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(self.sip.revdatadir, "trial2.json"))
        # copy of trial3a.json in upload overrides
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(self.sip.upldatadir, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 5)

    def test_registered_files(self):
        pod = utils.read_json(os.path.join(self.revdir, "1491", "_pod.json"))
        del pod['distribution'][1]
        self.sip = midas.MIDASSIP(self.midasid, os.path.join(self.revdir, "1491"),
                                  podrec=pod)
        datafiles = self.sip.registered_files()

        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 4)
        self.assertIn("trial1.json", datafiles)
        self.assertNotIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)
        self.assertEqual(len([k for k in datafiles.keys() if 'sim' in k]), 0) # sim* not in
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(self.sip.revdatadir, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(self.sip.revdatadir, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(self.sip.revdatadir, "trial3/trial3a.json"))
        self.assertEqual(len(datafiles), 4)

    def test_fromPOD(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        self.sip = midas.MIDASSIP.fromPOD(podf, self.revdir, self.upldir)
        
        self.assertIsNone(self.sip.nerd)
        self.assertTrue(isinstance(self.sip.pod, Mapping))
        self.assertEqual(self.sip.midasid, self.midasid)
        self.assertEqual(self.sip._nerdm_rec(), {'components': []})
        pod = self.sip._pod_rec()
        self.assertEqual(pod['accessLevel'], "public")
        self.assertEqual(pod['identifier'], self.midasid)
        
    def test_fromNERD(self):
        nerdf = os.path.join(datadir, self.midasid+".json")
        self.sip = midas.MIDASSIP.fromNERD(nerdf, self.revdir, self.upldir)
        
        self.assertIsNone(self.sip.pod)
        self.assertTrue(isinstance(self.sip.nerd, Mapping))
        self.assertEqual(self.sip.midasid, self.midasid)
        self.assertEqual(self.sip._pod_rec(), {'distribution': []})
        nerd = self.sip._nerdm_rec()
        self.assertEqual(nerd['accessLevel'], "public")
        self.assertEqual(nerd['ediid'], self.midasid)
        

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
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, self.upldir)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr._AsyncFileExaminer.wait_for_all()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.midasid, self.midasid)
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(len(self.bagr.sip.input_dirs), 2)
        self.assertEqual(self.bagr.sip.input_dirs[0],
                         os.path.join(self.revdir, self.midasid[32:]))
        self.assertEqual(self.bagr.sip.input_dirs[1],
                         os.path.join(self.upldir, self.midasid[32:]))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.sip.nerd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.bagbldr.bag)


    def test_ark_ediid(self):
        cfg = { 'bag_builder': { 'validate_id': r'(pdr\d)|(mds[01])' } }
        
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.arkid, self.bagparent,
                                                        self.revdir, self.upldir,
                                                        config=cfg)
        self.assertEqual(self.bagr.midasid, self.arkid)
        self.assertEqual(self.bagr.name, self.arkid[11:])
        self.assertEqual(self.bagr.sip.input_dirs[0],
                         os.path.join(self.revdir, self.arkid[16:]))
        self.assertEqual(self.bagr.sip.input_dirs[1],
                         os.path.join(self.upldir, self.arkid[16:]))

        self.assertEqual(os.path.basename(self.bagr.bagbldr.bagdir),
                         self.arkid[11:])

        self.bagr.ensure_base_bag()
        self.assertEqual(self.bagr.bagbldr.id, self.arkid)
        self.assertEqual(os.path.basename(self.bagr.bagbldr.bag.dir),
                         self.arkid[11:])

        # self.bagr.ensure_res_metadata()
        nerdm = self.bagr.bagbldr.bag.nerd_metadata_for('')
        self.assertEqual(nerdm['ediid'], self.arkid)
        self.assertEqual(nerdm['@id'], self.arkid)

    def test_ensure_base_bag(self):
        self.assertTrue(not os.path.exists(self.bagr.bagdir))
        self.assertEqual(os.path.basename(self.bagr.bagdir), self.bagr.name)
        self.assertIsNone(self.bagr.prepsvc)
        self.assertTrue(not self.bagr.prepared)
        self.assertIsNone(self.bagr.bagbldr.bag)
        
        self.bagr.ensure_base_bag()
        self.assertTrue(os.path.exists(self.bagr.bagdir))
        self.assertTrue(not self.bagr.prepared)
        self.assertIsNotNone(self.bagr.bagbldr.bag)

        with open(os.path.join(self.bagr.bagdir,"metadata","nerdm.json")) as fd:
            nerdm = json.load(fd)

        for key in ['@id', '@type', '@context', 'ediid', 'version', '_extensionSchemas', '_schema']:
            self.assertIn(key, nerdm)
        self.assertEqual(nerdm['ediid'], self.midasid)
        self.assertEqual(nerdm['version'], "1.0.0")
        self.assertTrue(nerdm['@id'].startswith("ark:/88434/mds0"))

        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, self.upldir)
        self.assertIsNotNone(self.bagr.bagbldr.bag)
        self.bagr.ensure_base_bag()
        self.assertTrue(os.path.exists(self.bagr.bagdir))
        self.assertTrue(self.bagr.prepared)
        self.assertIsNotNone(self.bagr.bagbldr.bag)

        self.assertIsNone(self.bagr.sip.nerd)
        self.assertIsNone(self.bagr.datafiles)
        
    def test_res_metadata(self):
        self.assertTrue(not os.path.exists(self.bagr.bagdir))
        self.assertEqual(os.path.basename(self.bagr.bagdir), self.bagr.name)
        self.assertIsNone(self.bagr.prepsvc)
        self.assertIsNone(self.bagr.sip.nerd)
        
        self.bagr.ensure_res_metadata()
        self.assertTrue(os.path.exists(self.bagr.bagdir))
        self.assertIsNotNone(self.bagr.sip.nerd)

        for key in ['@id', '@type', '@context', 'ediid', 'version', '_extensionSchemas', '_schema']:
            self.assertIn(key, self.bagr.sip.nerd)
        self.assertEqual(self.bagr.sip.nerd['ediid'], self.midasid)
        self.assertEqual(self.bagr.sip.nerd['version'], "1.0.0")
        self.assertTrue(self.bagr.sip.nerd['@id'].startswith("ark:/88434/mds0"))

        self.assertEqual(self.bagr.datafiles, {})
        
    def test_apply_pod(self):
        self.assertTrue(not os.path.exists(self.bagr.bagdir))
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")

        self.bagr.apply_pod(inpodfile)

        self.assertTrue(os.path.exists(self.bagr.bagdir))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.nerd_file_for("")))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.nerd_file_for("trial1.json")))
        self.assertIsNotNone(self.bagr.sip.nerd.get('title'))
        self.assertIn("trial1.json", self.bagr.datafiles)

        # ensure indepodence
        self.bagr.apply_pod(inpodfile)

        self.assertTrue(os.path.exists(self.bagr.bagdir))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.nerd_file_for("")))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.nerd_file_for("trial1.json")))
        self.assertIsNotNone(self.bagr.sip.nerd.get('title'))
        self.assertIn("trial1.json", self.bagr.datafiles)

        data = midas.read_pod(os.path.join(self.bagr.bagbldr.bag.pod_file()))
        self.assertIsInstance(data, OrderedDict)
        src = midas.read_pod(inpodfile)
        self.assertEqual(data, src)
        self.assertEqual(data.keys(), src.keys())  # confirms same order
        
        data = self.bagr.bagbldr.bag.nerd_metadata_for("", True)

        # should contain only non-file components:
        self.assertEqual(len(data['components']), 1)
        self.assertIsInstance(data, OrderedDict)
        self.assertNotIn('inventory', data)
        src = deepcopy(self.bagr.sip.nerd)
        del data['components']
        del src['components']
        if 'inventory' in src: del src['inventory']
        if 'dataHierarchy' in src: del src['dataHierarchy']
        self.assertEqual(to_dict(data), to_dict(src))
        self.assertEqual(data.keys(), src.keys())  # same order


        # ensure indepodence, non-redundance
        data = self.bagr.bagbldr.bag.nerd_metadata_for("")
        data['foo'] = "bar"
        data['doi'] = "doi:10.18434/FAKE"
        utils.write_json(data, self.bagr.bagbldr.bag.nerd_file_for(""))
        self.bagr.bagbldr.assign_id("ark:/88434/mds00hw91v")
        
        self.bagr.apply_pod(inpodfile)

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

    def test_apply_minpod(self):
        pod = {"identifier": self.midasid}

        self.bagr.apply_pod(pod, False)

        self.assertTrue(os.path.exists(self.bagr.bagdir))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.pod_file()))
        self.assertTrue(os.path.exists(self.bagr.bagbldr.bag.nerd_file_for("")))
        self.assertEqual(self.bagr.sip.nerd.get('title'), "")
        self.assertEqual(self.bagr.sip.nerd.get('description'), [""])

        # bagger was not configured to set a default DOI
        self.assertNotIn('doi', self.bagr.sip.nerd)

    def test_apply_restricted_pod(self):
        rpgurl = "https://rpg.nist.gov/pdr?"
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")
        pod = utils.read_json(inpodfile)
        pod['distribution'].append({
            "accessURL": rpgurl+"id="+pod.get('identifier'),
            "mediaType": "text/html"
        })
        pod.setdefault('rights', "gotta register")
        pod['accessLevel'] = "restricted public"

        cfg = {
            'gateway_url': rpgurl,
            'disclaimer': "Be careful."
        }
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, self.upldir,
                                                        {"restricted_access": cfg})
        self.bagr.apply_pod(pod)
        rpg = [c for c in self.bagr.sip.nerd.get('components')
                 if 'accessURL' in c and c['accessURL'].startswith(rpgurl)]
        self.assertEquals(len(rpg), 1)
        self.assertEqual(rpg[0]['@type'][0], "nrdp:RestrictedAccessPage")
        self.assertTrue(self.bagr.sip.nerd.get('rights'))
        self.assertTrue(self.bagr.sip.nerd.get('disclaimer'))
        

    def test_apply_defdoi(self):
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, self.upldir,
                                                        {"doi_minter": {"minting_naan": "44.88888"}})

        # old-style identifier
        pod = {"identifier": self.midasid}
        self.bagr.apply_pod(pod, False)
        self.assertNotIn('doi', self.bagr.sip.nerd)

        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.arkid, self.bagparent,
                                                        self.revdir, self.upldir,
                                                        {"doi_minter": {"minting_naan": "44.88888"}})
        
        # new-style identifier will trigger a default DOI to be set
        pod = {"identifier": self.arkid}
        self.bagr.apply_pod(pod, False)
        self.assertEqual(self.bagr.sip.nerd.get('doi'), "doi:44.88888/mds2-1491")


    def test_done(self):
        self.assertTrue(not os.path.exists(self.bagr.bagdir))
        self.assertTrue(not os.path.exists(self.bagr.bagdir+".lock"))
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")

        self.bagr.apply_pod(inpodfile)
        self.assertTrue(os.path.exists(self.bagr.bagdir+".lock"))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,"preserv.log")))
        self.assertTrue(self.bagr.bagbldr.logfile_is_connected())
        self.bagr.done()
        self.assertTrue(not self.bagr.bagbldr.logfile_is_connected())
        self.assertTrue(os.path.exists(self.bagr.bagdir+".lock"))
        
    def test_apply_pod_wremove(self):
        self.assertTrue(not os.path.exists(self.bagr.bagdir))
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")

        self.bagr.apply_pod(inpodfile)

        # make sure file components were registered
        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("trial1.json")))

        # add metadata for a data file that doesn't exist in the source dir
        data = self.bagr.bagbldr.bag.nerd_metadata_for("trial3/trial3a.json")
        data['downloadURL'] = re.sub(r'/'+data['filepath'], "/gold/trial5.json", data['downloadURL'])
        data['filepath'] = "gold/trial5.json"
        self.bagr.bagbldr.update_metadata_for(data['filepath'], data, "DataFile")

        self.assertTrue(os.path.isfile(
            self.bagr.bagbldr.bag.nerd_file_for("gold/trial5.json")))

        # now watch it get erased
        self.bagr.apply_pod(inpodfile, force=True)
        self.assertTrue(not os.path.exists(
            self.bagr.bagbldr.bag.nerd_file_for("gold/trial5.json")))
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
    def test_ensure_enhanced_refs(self):
        self.assertFalse(os.path.exists(self.bagdir))
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")

        cfg = {
            'enrich_refs': True,
            'doi_resolver': {
                'client_info': self.doiclientinfo
            }
        }
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, self.upldir, cfg)
        self.bagr.prepare()
        self.bagr.apply_pod(inpodfile)
        self.assertEqual(len(self.bagr.sip.nerd['references']), 1)
        self.assertIn('doi.org', self.bagr.sip.nerd['references'][0]['location'])
        self.assertNotIn('citation', self.bagr.sip.nerd['references'][0])

        self.bagr.ensure_enhanced_references()
        self.assertEqual(len(self.bagr.sip.nerd['references']), 1)
        self.assertIn('doi.org', self.bagr.sip.nerd['references'][0]['location'])
        self.assertIn('citation', self.bagr.sip.nerd['references'][0])

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

        destpath = "trial3/trial3a.json"
        dlurl = "https://data.nist.gov/od/ds/gurn/"+destpath
        dfile = os.path.join(self.upldir, self.midasid[32:], destpath)
        self.bagr.ensure_file_metadata(dfile, destpath, examine=True)

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
        self.bagr.ensure_file_metadata(dfile, destpath, examine=True)

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
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")
        
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
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine=False)
        valid = []
        invalid = []
        unknn = []
        for comp in self.bagr.sip.nerd.get('components',[]):
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
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_subcoll_metadata()

        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        mdata = self.bagr.bagbldr.bag.nerd_metadata_for("trial3", True)
        self.assertEqual(mdata['filepath'], "trial3")
        self.assertIn("nrdp:Subcollection", mdata['@type'])

    def test_enhance_metadata(self):
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_preparation()
        self.bagr.apply_pod(inpodfile)
        self.bagr.enhance_metadata()

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
        
    def test_registered_files(self):
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        uplsip = os.path.join(self.upldir, self.midasid[32:])
        revsip = os.path.join(self.revdir, self.midasid[32:])

        self.assertEquals(self.bagr.sip.registered_files(), {})

        self.bagr.ensure_preparation()
        self.bagr.apply_pod(inpodfile)

        datafiles = self.bagr.sip.registered_files()
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

    def test_baggermd_file_for(self):
        self.bagr.ensure_base_bag()
        self.assertEqual(self.bagr.baggermd_file_for(''),
                         os.path.join(self.bagr.bagbldr.bag.metadata_dir,"__bagger-midas3.json"))

        self.bagr.ensure_res_metadata()
        self.assertEqual(self.bagr.baggermd_file_for("trial1.json"), 
                         os.path.join(self.bagr.bagbldr.bag.metadata_dir,"trial1.json",
                                      "__bagger-midas3.json"))

    def test_baggermd_for(self):
        self.bagr.ensure_base_bag()
        bgmdf = os.path.join(self.bagr.bagbldr.bag.metadata_dir,"__bagger-midas3.json")
        self.assertTrue(os.path.exists(bgmdf), "Missing bagger md file: "+bgmdf)
        with open(bgmdf) as fd:
            saved = json.load(fd)
        self.assertIn('data_directory', saved)
        self.assertIn('upload_directory', saved)
        self.assertIn('bag_parent', saved)
        self.assertIn('bagger_config', saved)

        os.remove(bgmdf)
        self.assertFalse(os.path.exists(bgmdf), "failed to remove bagger md: "+bgmdf)

        self.assertEqual(self.bagr.baggermd_for(''), {})
        self.assertFalse(os.path.exists(bgmdf))
        with open(bgmdf, 'w') as fd:
            json.dump({"a": 1, "b": 2}, fd)
        self.assertEqual(self.bagr.baggermd_for(''), {"a": 1, "b": 2})

    def test_update_bagger_metadata_for(self):
        self.bagr.ensure_base_bag()
        bgmdf = os.path.join(self.bagr.bagbldr.bag.metadata_dir,"__bagger-midas3.json")
        self.assertTrue(os.path.exists(bgmdf), "Missing bagger md file: "+bgmdf)
        with open(bgmdf) as fd:
            saved = json.load(fd)
        self.assertIn('data_directory', saved)
        self.assertIn('upload_directory', saved)
        self.assertIn('bag_parent', saved)
        self.assertIn('bagger_config', saved)

        os.remove(bgmdf)
        self.assertFalse(os.path.exists(bgmdf), "failed to remove bagger md: "+bgmdf)

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
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.midasid, self.midasid)
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(len(self.bagr.sip.input_dirs), 1)
        self.assertEqual(self.bagr.sip.input_dirs[0],
                         os.path.join(self.revdir, self.midasid[32:]))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.sip.nerd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))
        self.assertFalse(os.path.exists(self.bagdir))

    def test_ensure_data_files(self):
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")
        
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
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine=False)
        valid = []
        invalid = []
        unknn = []
        for comp in self.bagr.sip.nerd.get('components',[]):
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
        self.assertIn("trial1.json.sha256", valid)
        self.assertIn("trial3/trial3a.json.sha256", valid)

    def test_registered_files(self):
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")
        revsip = os.path.join(self.revdir, self.midasid[32:])

        self.assertEquals(self.bagr.sip.registered_files(), {})

        self.bagr.ensure_preparation()
        self.bagr.apply_pod(inpodfile)

        datafiles = self.bagr.sip.registered_files()
        self.assertIsInstance(datafiles, dict)
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

        datafiles = self.bagr.sip.available_files()
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

    def test_fileExaminer_autolaunch(self):
        # show that the async thread does its work with autolaunch
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")
        self.assertIsNotNone(self.bagr.fileExaminer)
        # self.bagr.fileExaminer_autolaunch = True

        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.prepare()
        self.bagr.apply_pod(inpodfile)
        try:
            self.bagr.ensure_data_files(examine="async")
        except Exception as ex:
            if self.bagr.fileExaminer.thread:
                self.bagr.fileExaminer.thread.join()
            raise
        self.assertTrue(os.path.exists(self.bagdir))
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIn('checksum', fmd) # because there's a .sha256 file

#        time.sleep(0.1)
        if self.bagr.fileExaminer.running():
            print("waiting for file examiner thread")
            n = 20
            while n > 0 and self.bagr.fileExaminer.running():
                n -= 1
                time.sleep(0.1)
            if n == 0:
                self.fail("file examiner is taking too long")    
        fmd = self.bagr.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIn('checksum', fmd)

    def test_finalize_version(self):
        stagedir = os.path.join(self.bagparent,"stage")
        if not os.path.isdir(stagedir):
            os.mkdir(stagedir)
        nerddir = os.path.join(stagedir, "_nerd")
        if not os.path.isdir(nerddir):
            os.mkdir(nerddir)
        storedir = os.path.join(self.bagparent,"store")
        if not os.path.isdir(storedir):
            os.mkdir(storedir)
        config = {
            'repo_access': {
                'headbag_cache': stagedir,
                'store_dir': storedir,
            }
        }
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, config=config)

        # because there is data in the review directory, this will be seen
        # as a metadata update.
        inpodfile = os.path.join(self.revdir,"1491","_pod.json")
        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")
        
        self.bagr.bagbldr.update_annotations_for('', {'version': "1.0.0+ (in edit)"})
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.bagr.sip.nerd = nerd
        self.assertEqual(nerd['version'], "1.0.0+ (in edit)")

        nerd = self.bagr.finalize_version()
        # it's never been published before, so version goes to 1.0.0
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertEqual(self.bagr.sip.nerd['version'], "1.0.0")
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEqual(nerd['version'], "1.0.0")

        # now pretend like it has.
        self.bagr.bagbldr.update_annotations_for('', {'version': "1.0.0+ (in edit)"})
        with open(os.path.join(stagedir, self.midasid+".1_0_0.mbag0_4-0.zip"), 'w') as fd:
            fd.write("\n")
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        self.revdir, config=config)
        nerd = self.bagr.finalize_version()
        self.assertEqual(nerd['version'], "1.1.0")
        self.assertIn('releaseHistory', nerd)
        self.assertEqual(nerd['releaseHistory']['@id'], nerd['@id']+".rel")
        self.assertIn('hasRelease', nerd['releaseHistory'])
        self.assertEqual(len(nerd['releaseHistory']['hasRelease']), 1)

        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEqual(nerd['version'], "1.1.0")
        self.assertIn('releaseHistory', nerd)
        self.assertEqual(nerd['releaseHistory']['@id'], nerd['@id']+".rel")
        self.assertIn('hasRelease', nerd['releaseHistory'])
        self.assertEqual(len(nerd['releaseHistory']['hasRelease']), 1)
        self.assertTrue(nerd['releaseHistory']['hasRelease'][0]['location'].endswith(".v1_1_0"),
                        "location does not end with version: "+
                        nerd['releaseHistory']['hasRelease'][0]['location'])
        
        
class TestMIDASMetadataBaggerUpload(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "upload")
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        None, self.upldir)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.midasid, self.midasid)
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(len(self.bagr.sip.input_dirs), 1)
        self.assertEqual(self.bagr.sip.input_dirs[0],
                         os.path.join(self.upldir, self.midasid[32:]))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.sip.nerd)
        self.assertIsNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(self.bagparent))
        self.assertFalse(os.path.exists(self.bagdir))

    def test_ensure_data_files(self):
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        metadir = os.path.join(self.bagr.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagr.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")
        
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
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine=False)
        valid = []
        invalid = []
        unknn = []
        for comp in self.bagr.sip.nerd.get('components',[]):
            if not any([":ChecksumFile" in t for t in comp.get('@type',[])]):
                continue
            if 'valid' not in comp:
                unknn.append(comp['filepath'])
            elif comp['valid'] is True:
                valid.append(comp['filepath'])
            else:
                invalid.append(comp['filepath'])

        self.assertEqual(len(unknn) + len(valid) + len(invalid), 1)
        self.assertEqual(unknn, ["trial3/trial3a.json.sha256"])
        self.assertEqual(invalid, [])
        self.assertEqual(valid, [])

    def test_registered_files(self):
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        uplsip = os.path.join(self.upldir, self.midasid[32:])

        self.assertEquals(self.bagr.sip.registered_files(), {})

        self.bagr.ensure_preparation()
        self.bagr.apply_pod(inpodfile)

        datafiles = self.bagr.sip.registered_files()
        self.assertIsInstance(datafiles, dict)
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

        datafiles = self.bagr.sip.available_files()
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

    def test_finalize_version_deactiv8(self):
        stagedir = os.path.join(self.bagparent,"stage")
        if not os.path.isdir(stagedir):
            os.mkdir(stagedir)
        nerddir = os.path.join(stagedir, "_nerd")
        if not os.path.isdir(nerddir):
            os.mkdir(nerddir)
        storedir = os.path.join(self.bagparent,"store")
        if not os.path.isdir(storedir):
            os.mkdir(storedir)
        config = {
            'repo_access': {
                'headbag_cache': stagedir,
                'store_dir': storedir,
            }
        }
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        None, self.upldir, config=config)

        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")

        self.bagr.datafiles = {}  # trick into thinking there are no files to update

        # trick into thinking its been published before
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        relhist = nerd.get('releaseHistory')
        if not relhist:
            relhist = bagutils.create_release_history_for(nerd['@id'])
        relhist['hasRelease'].append(OrderedDict([
            ('version', "1.0.0"),
            ('issued', '2021-10-09'),
            ('@id', nerd['@id']+".v1_0_0")
        ]))
        self.bagr.bagbldr.update_metadata_for('', {
            'version': "1.0.0",
            'releaseHistory': relhist,
            'status': "removed"
        })
        self.bagr.bagbldr.update_annotations_for('', {'version': "1.0.0+ (in edit)"})
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.bagr.sip.nerd = nerd
        self.assertEqual(nerd['version'], "1.0.0+ (in edit)")
        self.assertEqual(nerd['status'], "removed")

        with open(os.path.join(stagedir, self.midasid+".1_0_0.mbag0_4-0.zip"), 'w') as fd:
            fd.write("\n")
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        None, self.upldir, config=config)
        self.bagr.datafiles = {}
        nerd = self.bagr.finalize_version()
        self.assertEqual(nerd['version'], "1.0.1")
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEqual(nerd['version'], "1.0.1")

        relhist = nerd.get('releaseHistory')
        self.assertEqual(len(relhist['hasRelease']), 2)
        for rel in relhist['hasRelease']:
            self.assertEqual(rel['status'], "removed",
                             "release status for version=%s: '%s' != 'removed'" % (str(rel.get('version')),
                                                                                   str(rel.get('status'))))
        

    def test_finalize_version(self):
        stagedir = os.path.join(self.bagparent,"stage")
        if not os.path.isdir(stagedir):
            os.mkdir(stagedir)
        nerddir = os.path.join(stagedir, "_nerd")
        if not os.path.isdir(nerddir):
            os.mkdir(nerddir)
        storedir = os.path.join(self.bagparent,"store")
        if not os.path.isdir(storedir):
            os.mkdir(storedir)
        config = {
            'repo_access': {
                'headbag_cache': stagedir,
                'store_dir': storedir,
            }
        }
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        None, self.upldir, config=config)

        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")

        self.bagr.datafiles = {}  # trick into thinking there are no files to update
        self.bagr.bagbldr.update_annotations_for('', {'version': "1.0.0+ (in edit)"})
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.bagr.sip.nerd = nerd
        self.assertEqual(nerd['version'], "1.0.0+ (in edit)")

        nerd = self.bagr.finalize_version()
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertEqual(self.bagr.sip.nerd['version'], "1.0.0")
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEqual(nerd['version'], "1.0.0")

        # now pretend like it has.
        self.bagr.bagbldr.update_annotations_for('', {'version': "1.0.0+ (in edit)"})
        with open(os.path.join(stagedir, self.midasid+".1_0_0.mbag0_4-0.zip"), 'w') as fd:
            fd.write("\n")
        self.bagr = midas.MIDASMetadataBagger.fromMIDAS(self.midasid, self.bagparent,
                                                        None, self.upldir, config=config)
        self.bagr.datafiles = {}
        nerd = self.bagr.finalize_version()
        self.assertEqual(nerd['version'], "1.0.1")
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEqual(nerd['version'], "1.0.1")
        
        
    def test_finalize_version_preset(self):
        inpodfile = os.path.join(self.upldir,"1491","_pod.json")
        self.bagr.apply_pod(inpodfile)
        self.bagr.ensure_data_files(examine="sync")

        self.bagr.bagbldr.update_annotations_for('', {'version': "10.3"})
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.bagr.sip.nerd = nerd
        self.assertEqual(nerd['version'], "10.3")

        nerd = self.bagr.finalize_version()
        self.assertEqual(nerd['version'], "10.3")
        self.assertEqual(self.bagr.sip.nerd['version'], "10.3")
        nerd = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEqual(nerd['version'], "10.3")
        
        

class TestPreservationBagger(test.TestCase):
    
    testsip = os.path.join(datadir, "metadatabag")
    testdata = os.path.join(datadir, "samplembag", "data")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("bagger")
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.datadir = os.path.join(self.workdir, "data")
        self.bagparent = os.path.join(self.datadir, "_preserv")
        self.sipdir = os.path.join(self.mdbags, self.midasid)

        # copy the data files first
        shutil.copytree(self.testdata, self.datadir)
        # os.mkdir(self.bagparent)

        # copy input data to writable location
        shutil.copytree(self.testsip, self.sipdir)

        # set the config we'll use
        self.config = {
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

        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, self.datadir)
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.done()

        self.bagr = None

    def createPresBagger(self):
        self.bagr = midas.PreservationBagger(self.sipdir, self.bagparent, self.datadir,
                                             self.config)

    def tearDown(self):
        if self.bagr:
            if self.bagr.bagbldr:
                self.bagr.bagbldr._unset_logfile()
            self.bagr = None
        self.mdbagger = None
        self.tf.clean()

    def test_ctor(self):
        self.createPresBagger()
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.sipdir, self.sipdir)
        self.assertEqual(self.bagr.datadir, self.datadir)
        self.assertEqual(self.bagr.bagparent, self.bagparent)
        self.assertIsNone(self.bagr.bagbldr)
        self.assertTrue(os.path.exists(self.bagparent))

        bagdir = os.path.join(self.bagparent, self.bagr.name)
        self.assertEqual(self.bagr.bagdir, bagdir)

    def test_form_bag_name(self):
        self.createPresBagger()
        self.bagr.cfg['mbag_version'] = "1.2"
        bagname = self.bagr.form_bag_name("goober", 3, "1.0.1")
        self.assertEqual(bagname, "goober.1_0_1.mbag1_2-3")

        

    def test_preparation(self):
        self.createPresBagger()
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
        

    def test_finalize_bag(self):
        self.createPresBagger()
        try:
            self.bagr.finalize_bag()
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

        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "data", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                                   "data", "trial2.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                             "data", "trial3", "trial3a.json")))

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
        self.assertEqual(md.get("title"), "a better title")
        
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

        # test for clean up
        self.assertTrue(not os.path.exists(os.path.join(self.bagr.bagbldr.bag.metadata_dir,
                                                        "__bagger-midas3.json")))

        # test key metadata
        nerdm = self.bagr.bagbldr.bag.nerd_metadata_for('')
        for prop in "annotated revised firstIssued modified issued".split():
            self.assertIn(prop, nerdm)

    def test_check_data_files(self):
        self.createPresBagger()
        self.bagr.prepare()

        # register a file available from an external service
        self.bagr.bagbldr.update_metadata_for("sim++.json", {
            "downloadURL": "https://example.nist.gov/data/sim++.json"
        }, "DataFile")
        
        try:
            self.bagr.finalize_bag()
        except AIPValidationError as ex:
            self.fail(ex.description)

        # make sure we could've found missing files; relies on sim++.json
        self.bagr._check_data_files(self.bagr.cfg.get('data_checker',{}))
        with self.assertRaises(AIPValidationError):
            self.bagr._check_data_files(self.bagr.cfg.get('data_checker',{}),
                                        viadistrib=False)

    def test_clean_bag(self):
        self.createPresBagger()
        self.bagr.prepare()

        # add some things to clean up
        open(os.path.join(self.bagr.bagdir, "_goober.txt"), 'a').close()
        open(os.path.join(self.bagr.bagdir, "metadata", "trial1.json", "_goober.txt"), 'a').close()
        data = utils.read_json(self.bagr.bagbldr.bag.pod_file())
        data["_goober"] = "I am a"
        utils.write_json(data, self.bagr.bagbldr.bag.pod_file())
        self.bagr.bagbldr.update_metadata_for("", {"__goober": "I am a"})
        self.bagr.bagbldr.update_annotations_for("trial1.json", {"__goober": "I am a"})

        # test mods were successful
        data = self.bagr.bagbldr.bag.nerd_metadata_for('trial1.json', True)
        self.assertIn('__goober', data.keys())
        dirtyfiles = []
        dirtymd = []
        for (r, d, files) in os.walk(self.bagr.bagdir):
            dirtyfiles.extend([os.path.join(r,f) for f in files if f.startswith("_")])
            for mdfile in [f for f in files if f in ['pod.json', 'nerdm.json', 'annot.json']]:
                data = utils.read_json(os.path.join(r, mdfile))
                if len([p for p in data.keys() if p.startswith('_')]) > 0:
                    dirtymd.append(os.path.join(r, mdfile))
        self.assertNotEqual(len(dirtyfiles), 0)
        self.assertNotEqual(len(dirtymd), 0)
        
        self.bagr.clean_bag()

        self.assertFalse(os.path.exists(os.path.join(self.bagr.bagdir, "_goober.txt")),
                                        "top-level admin file not removed")
        self.assertFalse(os.path.exists(os.path.join(self.bagr.bagdir, "metadata",
                                                     "trial1.json", "_goober.txt")),
                                        "metadata admin file not removed")
        data = utils.read_json(self.bagr.bagbldr.bag.pod_file())
        self.assertNotIn('__goober', data.keys())
        data = self.bagr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertNotIn('__goober', data.keys())
        data = self.bagr.bagbldr.bag.nerd_metadata_for('trial1.json', True)
        self.assertNotIn('__goober', data.keys())

        # confirm that we are fully clean
        dirtyfiles = []
        dirtymd = []
        for (r, d, files) in os.walk(self.bagr.bagdir):
            dirtyfiles.extend([os.path.join(r,f) for f in files if f.startswith("_")])
            for mdfile in [f for f in files if f in ['pod.json', 'nerdm.json', 'annot.json']]:
                data = utils.read_json(os.path.join(r, mdfile))
                if len([p for p in data.keys() if p.startswith('__')]) > 0:
                    dirtymd.append(os.path.join(r, mdfile))
        self.assertEqual(len(dirtyfiles), 0)
        self.assertEqual(len(dirtymd), 0)

        
                         


if __name__ == '__main__':
    test.main()
