import os, pdb, shutil
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.tests import Tempfiles, rmtmpdir
import nistoar.preserv.bagit.prep as prep
import nistoar.preserv.exceptions as exceptions

# datadir = nistoar/preserv/tests/data
datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "data"
)

def tearDownModule():
    rmtmpdir()

class TestDetectFormat(test.TestCase):

    testsip = os.path.join(datadir, "simplesip")

    def test_find_file(self):
        files = [ "goob.xml", "_pod.json", "trial1.json" ]
        self.assertEqual(prep.find_file(self.testsip, files),
                         os.path.join(self.testsip, files[1]))

    def test_detect_SIP_format(self):
        self.assertEqual(prep.detect_SIP_format(self.testsip), "MIDAS")
        self.assertIsNone(prep.detect_SIP_format(datadir))

    
class TestMIDASPrepper(test.TestCase):

    testsip = os.path.join(datadir, "simplesip")

    def setUp(self):
        self.tf = Tempfiles()

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        outdir = self.tf.mkdir("wbag")
        prpr = prep.MIDASFormatPrepper(self.testsip, outdir, {})
        self.assertEqual(prpr.sipdir, self.testsip)
        self.assertEqual(prpr.bagparent, outdir)
        self.assertEqual(prpr.cfg, {})
        self.assertIsNone(prpr.poddata)
        self.assertIsNone(prpr.dsid)
        self.assertIsNone(prpr.bagdir)

        with self.assertRaises(exceptions.SIPDirectoryNotFound):
            prpr = prep.MIDASFormatPrepper("/goob", outdir, {})
        with self.assertRaises(exceptions.SIPDirectoryError):
            try:
                prpr = prep.MIDASFormatPrepper("/etc/passwd", outdir, {})
            except exceptions.SIPDirectoryNotFound, ex:
                self.fail("wrong exception: "+str(ex))

    def setup_insitu(self):
        sipdir = self.tf.track("sip")
        shutil.copytree(self.testsip, sipdir)
        return sipdir

    def test_insitu(self):
        sipdir = self.setup_insitu()
        outdir = os.path.join(sipdir, "_wbag")
        
        prpr = prep.MIDASFormatPrepper(sipdir, outdir, {})
        self.assertTrue(prpr.cfg['relative_to_indir'])

        with self.assertRaises(exceptions.ConfigurationException):
            prpr = prep.MIDASFormatPrepper(sipdir, outdir,
                                           {'relative_to_indir': False})

    def test_ensure_bag_parent_dir(self):
        outdir = self.tf("wbag")
        prpr = prep.MIDASFormatPrepper(self.testsip, outdir, {})
        self.assertFalse(os.path.exists(outdir))
        with self.assertRaises(exceptions.StateException):
            prpr.ensure_bag_parent_dir()
            
        sipdir = self.setup_insitu()
        outdir = os.path.join(sipdir, "_wbag")
        prpr = prep.MIDASFormatPrepper(sipdir, outdir, {})
        self.assertFalse(os.path.exists(outdir))
        prpr.ensure_bag_parent_dir()
        self.assertTrue(os.path.exists(outdir))

    def test_find_pod_file(self):
        outdir = os.path.join(self.testsip, "_wbag")

        prpr = prep.MIDASFormatPrepper(self.testsip, outdir,
                                       {'pod_locations': ['goober.json']})
        with self.assertRaises(exceptions.PODError):
            prpr.find_pod_file()

        prpr = prep.MIDASFormatPrepper(self.testsip, outdir,
                                       {'pod_locations': ['goober.json',
                                                          prep.MIDAS_POD_FILE ]})
        podf = prpr.find_pod_file()
        self.assertEqual(podf, os.path.join(self.testsip, prep.MIDAS_POD_FILE))

        prpr = prep.MIDASFormatPrepper(self.testsip, outdir, {})
        podf = prpr.find_pod_file()
        self.assertEqual(podf, os.path.join(self.testsip, prep.MIDAS_POD_FILE))

    def test_form_bagdir_name(self):
        prpr = prep.MIDASFormatPrepper("/tmp", "/tmp/gomer", {})
        name = prpr.form_bagdir_name("POKEMON")
        self.assertEqual(name, "POKEMON.mbag0_2-1")

        prpr = prep.MIDASFormatPrepper("/tmp", "/tmp/gomer",
                                       {'mbag_seqno': 14,
                                        'mbag_version': '1.0'})
        name = prpr.form_bagdir_name("POKEMON")
        self.assertEqual(name, "POKEMON.mbag1_0-14")

    def test_read_pod(self):
        sipdir = self.setup_insitu()
        outdir = os.path.join(sipdir, "_wbag")
        prpr = prep.MIDASFormatPrepper(sipdir, outdir, {})

        podf = os.path.join(sipdir, prep.MIDAS_POD_FILE)
        self.assertTrue(os.path.exists(podf))
        data = prpr.read_pod(podf)
        self.assertIsInstance(data, dict)
        self.assertIn('identifier', data)
        self.assertIn('distribution', data)
        self.assertEqual(data['identifier'],
                         '3A1EE2F169DD3B8CE0531A570681DB5D1491')

        with self.assertRaises(exceptions.PODError):
            data = prpr.read_pod("goob.json")

    def test_set_bagdir(self):
        sipdir = self.setup_insitu()
        outdir = os.path.join(sipdir, "_wbag")
        prpr = prep.MIDASFormatPrepper(sipdir, outdir, {})

        self.assertIsNone(prpr.dsid)
        self.assertIsNone(prpr.bagdir)
        prpr.set_bagdir()
        self.assertEqual(prpr.dsid, '3A1EE2F169DD3B8CE0531A570681DB5D1491')
        self.assertEqual(os.path.dirname(prpr.bagdir), outdir)
        self.assertEqual(os.path.basename(prpr.bagdir),
                         '3A1EE2F169DD3B8CE0531A570681DB5D1491.mbag0_2-1')

    def test_ensure_bagdir(self):
        sipdir = self.setup_insitu()
        outdir = os.path.join(sipdir, "_wbag")
        prpr = prep.MIDASFormatPrepper(sipdir, outdir, {})

        self.assertIsNone(prpr.dsid)
        self.assertIsNone(prpr.bagdir)
        prpr.set_bagdir()
        bagdir = prpr.bagdir
        self.assertTrue(not os.path.exists(bagdir))
        prpr.ensure_bagdir()
        self.assertEqual(prpr.bagdir, bagdir)
        self.assertTrue(os.path.exists(bagdir))
        self.assertTrue(os.path.isdir(bagdir))

        # ensure indepodent
        prpr.ensure_bagdir()
        self.assertEqual(prpr.bagdir, bagdir)
        self.assertTrue(os.path.exists(bagdir))
        self.assertTrue(os.path.isdir(bagdir))
        
        shutil.rmtree(bagdir)
        self.assertTrue(not os.path.exists(bagdir))
        prpr.bagdir = None
        prpr.dsid = None
        prpr.ensure_bagdir()
        self.assertEqual(prpr.bagdir, bagdir)
        self.assertTrue(os.path.exists(bagdir))
        self.assertTrue(os.path.isdir(bagdir))
        
    def test_ensure_bag_structure(self):
        sipdir = self.setup_insitu()
        outdir = os.path.join(sipdir, "_wbag")
        prpr = prep.MIDASFormatPrepper(sipdir, outdir, {})

        self.assertIsNone(prpr.dsid)
        self.assertIsNone(prpr.bagdir)

        prpr.ensure_bag_structure()
        self.assertIsNotNone(prpr.dsid)
        self.assertIsNotNone(prpr.bagdir)
        self.assertTrue(os.path.exists(prpr.bagdir))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'data')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'data')))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'metadata')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'metadata')))

        # ensure indepodent
        prpr.ensure_bag_structure()
        self.assertIsNotNone(prpr.dsid)
        self.assertIsNotNone(prpr.bagdir)
        self.assertTrue(os.path.exists(prpr.bagdir))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'data')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'data')))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'metadata')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'metadata')))
        
        # indepodent and extra dirs
        prpr = prep.MIDASFormatPrepper(sipdir, outdir,
                                       {'extra_tag_dirs': ['metameta']})
        self.assertIsNone(prpr.dsid)
        self.assertIsNone(prpr.bagdir)

        prpr.ensure_bag_structure()
        self.assertIsNotNone(prpr.dsid)
        self.assertIsNotNone(prpr.bagdir)
        self.assertTrue(os.path.exists(prpr.bagdir))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'data')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'data')))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'metadata')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'metadata')))
        self.assertTrue(os.path.exists(os.path.join(prpr.bagdir,'metameta')))
        self.assertTrue(os.path.isdir(os.path.join(prpr.bagdir,'metameta')))
        


if __name__ == '__main__':
    test.main()
    
