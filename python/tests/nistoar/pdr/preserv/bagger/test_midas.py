# These unit tests test the nistoar.pdr.preserv.bagger.midas module.  These tests
# do not include support for updating previously published datasets (via use of 
# the UpdatePrepService class).  Because testing support for updates require 
# simulated RMM and distribution services to be running, they have been 
# seperated out into test_midas_update.py.
#
import os, sys, pdb, shutil, logging, json
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.preserv import AIPValidationError

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

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

class TestMIDASMetadataBaggerMixed(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    wrongid = '333333333333333333333333333333331491'

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
        data = midas.read_nerd(os.path.join(metadir, "nerdm.json"))

        # should contain only non-file components:
        self.assertEqual(len(data['components']), 1)
        self.assertIsInstance(data, OrderedDict)
        self.assertNotIn('inventory', data)
        src = deepcopy(self.bagr.resmd)
        del data['components']
        del src['components']
        del src['inventory']
        del src['dataHierarchy']
        self.assertEqual(data, src)
        self.assertEqual(data.keys(), src.keys())  # same order

        # spot check some key NERDm properties
        data = self.bagr.resmd
        self.assertEqual(data['@id'], "ark:/88434/mds00hw91v")
        self.assertEqual(data['doi'], "doi:10.18434/T4SW26")
        self.assertEqual(len(data['components']), 4)
        self.assertEqual(data['components'][3]['@type'][0], 'nrd:Hidden')
        self.assertIsInstance(data['@context'], list)
        self.assertEqual(len(data['@context']), 2)
        self.assertEqual(data['@context'][1]['@base'], data['@id'])

    def test_data_file_inventory(self):
        uplsip = os.path.join(self.upldir, self.midasid[32:])
        revsip = os.path.join(self.revdir, self.midasid[32:])

        datafiles = self.bagr.data_file_inventory()
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

    def test_data_file_distribs(self):
        # pod has not been loaded yet
        self.assertEqual(self.bagr.pod_file_distribs(), [])

        self.bagr.ensure_res_metadata()
        files = self.bagr.pod_file_distribs()
        self.assertIn('trial1.json', files)
        self.assertIn('trial2.json', files)
        self.assertEqual(len(files), 3) # {trial1,trial2,sim}.json + access_comp

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

        data = midas.read_nerd(mdfile)
        self.assertEqual(data['size'], 70)
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
        self.bagr.ensure_file_metadata(dfile, destpath, disttype="ChecksumFile")

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))

        data = midas.read_nerd(mdfile)
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

    def test_ensure_file_metadata_resmd(self):
        # fix the config and recreate
        self.bagr.cfg.setdefault('bag_builder', {})
        self.bagr.cfg['bag_builder']['distrib_service_baseurl'] = \
                        "https://testdata.nist.gov/od/ds"
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, self.upldir,
                                              self.bagr.cfg)
        self.assertFalse(os.path.exists(self.bagdir))

        self.bagr.ensure_res_metadata()

        destpath = os.path.join("trial3", "trial3a.json")
        dfile = os.path.join(self.upldir, self.midasid[32:], destpath)
        self.bagr.ensure_file_metadata(dfile, destpath, self.bagr.resmd)

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))

        data = midas.read_nerd(mdfile)
        self.assertEqual(data['size'], 70)
        self.assertTrue(data['checksum']['hash'])
        self.assertEqual(data['checksum']['algorithm'],
                         { "@type": "Thing", "tag": "sha256" })
        self.assertTrue(data['downloadURL'])
        self.assertTrue(data['downloadURL'].startswith('https://testdata.nist.gov/'),
                        "Unexpected downloadURL: "+ data['downloadURL'])

        # trial3a.json has no matching distribution in _pod.json; thus, no desc
        self.assertNotIn('description', data)

        destpath = os.path.join("trial2.json")
        dfile = os.path.join(self.revdir, self.midasid[32:], destpath)
        self.bagr.ensure_file_metadata(dfile, destpath, self.bagr.resmd)

        mdfile = os.path.join(self.bagdir, 'metadata', destpath, "nerdm.json")
        self.assertTrue(os.path.exists(self.bagdir))
        self.assertTrue(os.path.exists(mdfile))

        data = midas.read_nerd(mdfile)
        self.assertEqual(data['size'], 69)
        self.assertTrue(data['checksum']['hash'])
        self.assertEqual(data['checksum']['algorithm'],
                         { "@type": "Thing", "tag": "sha256" })
        self.assertTrue(data['downloadURL'])
        self.assertTrue(data['description'])

    def test_ensure_data_files(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
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
        
    def test_ensure_data_files_wremove(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        self.assertIsNotNone(self.bagr.datafiles)

        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))

        self.bagr.bagbldr.init_filemd_for( os.path.join("gold","trial5.json"),
                                           write=True,
                                           examine=os.path.join(self.revdir,
                                                               self.midasid[32:],
                                                                "trial1.json") )
        t5path = os.path.join( metadir,"gold","trial5.json","nerdm.json")
        self.assertTrue(os.path.exists(t5path))

        self.bagr.ensure_data_files()
        self.assertTrue(os.path.exists(metadir))
        for filepath in self.bagr.datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))
        self.assertFalse(os.path.exists(t5path))
        
    def test_check_checksum_files(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_data_files()
        valid = []
        invalid = []
        for df in self.bagr.datafiles:
            nerdf = os.path.join(self.bagr.bagdir,"metadata",df,"nerdm.json")
            with open(nerdf) as fd:
                nerd = json.load(fd)
            if not any([":ChecksumFile" in t for t in nerd.get('@type',[])]):
                continue
            if 'valid' in nerd and nerd['valid'] is True:
                valid.append(df)
            else:
                invalid.append(df)

        self.assertEqual(len(valid) + len(invalid), 2)
        self.assertIn("trial1.json.sha256", valid)
        self.assertIn("trial3/trial3a.json.sha256", invalid)
        
        
    def test_ensure_subcoll_metadata(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.ensure_subcoll_metadata()

        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        mdata = midas.read_nerd(mdfile)
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

        mdata = midas.read_nerd(mdfile)
        self.assertEqual(mdata['filepath'], "trial3")
        self.assertIn("nrdp:Subcollection", mdata['@type'])
        
    def test_ensure_preparation(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))
        self.assertIsNone(self.bagr.datafiles)

        self.bagr.prepare()
        self.assertIsNotNone(self.bagr.datafiles)
        self.assertFalse(not os.path.exists(self.bagdir))
        
class TestMIDASMetadataBaggerReview(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.revdir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir)

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

    def test_find_pod_file(self):
        self.assertEquals(self.bagr.find_pod_file(),
                         os.path.join(self.revdir,self.midasid[32:],'_pod.json'))

    def test_data_file_inventory(self):
        revsip = os.path.join(self.revdir, self.midasid[32:])

        datafiles = self.bagr.data_file_inventory()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 5)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)

        # files are only found in the review area
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(revsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(revsip, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(revsip, "trial3/trial3a.json"))


class TestMIDASMetadataBaggerUpload(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "review")
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

    def test_data_file_inventory(self):
        uplsip = os.path.join(self.upldir, self.midasid[32:])

        datafiles = self.bagr.data_file_inventory()
        self.assertIsInstance(datafiles, dict)
        self.assertEqual(len(datafiles), 5)
        self.assertIn("trial1.json", datafiles)
        self.assertIn("trial1.json.sha256", datafiles)
        self.assertIn("trial2.json", datafiles)
        self.assertIn("trial3/trial3a.json", datafiles)
        self.assertIn("trial3/trial3a.json.sha256", datafiles)

        # files are only found in the upload area
        self.assertEqual(datafiles["trial1.json"],
                         os.path.join(uplsip, "trial1.json"))
        self.assertEqual(datafiles["trial2.json"],
                         os.path.join(uplsip, "trial2.json"))
        self.assertEqual(datafiles["trial3/trial3a.json"],
                         os.path.join(uplsip, "trial3/trial3a.json"))

class TestPreservationBagger(test.TestCase):
    
    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

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
            }
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

        self.assertIsNone(self.bagr.prepsvc)  # update support turned off

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
        

if __name__ == '__main__':
    test.main()
