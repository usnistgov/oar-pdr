import os, sys, logging, argparse, pdb, imp, time, json, shutil
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish.cmd.fix import topics
from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(os.path.dirname(testdir)))
datadir = os.path.join(pdrmoddir, "preserv", "data")

class TestFixTopicsCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.config = {}
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(topics)

    def tearDown(self):
        self.tf.clean()

    def test_parse(self):
        args = self.cmd.parse_args("-q topics pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "topics")
        self.assertEqual(args.aipid, "pdr2222")
        self.assertIsNone(args.bagparent)
        self.assertFalse(args.frompod)
        self.assertFalse(args.asannots)
        self.assertFalse(args.replacethemes)
        self.assertIsNone(args.addthemes)

        argline = "-q -w "+self.workdir+" topics -b mdserv pdr2210 -a --add-theme goober"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "topics")
        self.assertEqual(args.aipid, "pdr2210")
        self.assertEqual(args.bagparent, "mdserv")
        self.assertFalse(args.frompod)
        self.assertTrue(args.asannots)
        self.assertFalse(args.replacethemes)
        self.assertEquals(args.addthemes, ["goober"])

        argline = "-q -w "+self.workdir+" topics -b mdserv pdr2210 -a -t goober gurn"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "topics")
        self.assertEqual(args.aipid, "pdr2210")
        self.assertEqual(args.bagparent, "mdserv")
        self.assertFalse(args.frompod)
        self.assertTrue(args.asannots)
        self.assertFalse(args.replacethemes)
        self.assertEquals(args.addthemes, ["goober", "gurn"])

    def test_exceute(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        bldr.update_metadata_for('', {'topic': []}, message="test prep topics")

        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 0)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")

    def test_exceute_wvalidation(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        bldr.update_metadata_for('', {'topic': []}, message="test prep topics")

        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir+" -V"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 0)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")

    def test_exceute_addtheme(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        bldr.update_metadata_for('', {'topic': []}, message="test prep topics")

        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir+" -t Bioscience genomics"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 2)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")
        self.assertEquals(nerd.get('topic')[1]['tag'], "Bioscience")
        self.assertEquals(nerd.get('topic')[2]['tag'], "Bioscience: Genomics")

    def test_exceute(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        bldr.update_metadata_for('', {'topic': []}, message="test prep topics")

        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 0)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")

    def test_exceute_replace(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        t = {
            "scheme": "https://data.nist.gov/od/dm/nist-themes/v1.1",
            "tag": "Optical communications"
        }
        bldr.update_metadata_for('', { 'topic': [t] }, message="test prep topics")

        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertNotEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 1)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")
        self.assertEquals(nerd.get('topic')[1]['tag'], "Optical communications")

        argline = "-q -w "+self.workdir+" topics "+bagdir+" -r"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 0)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")

    def test_exceute_correct(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir+" -t genomics -T"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 1)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")
        self.assertEquals(nerd.get('topic')[1]['tag'], "Bioscience: Genomics")
        self.assertEquals(nerd.get('theme')[0], "Physics: Optical physics")
        self.assertEquals(nerd.get('theme')[1], "Bioscience: Genomics")

    def test_exceute_asannots(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        bldr.update_metadata_for('', {'topic': []}, message="test prep topics")

        bag = NISTBag(bagdir)
        nerd = bag.nerdm_record()
        self.assertEqual(nerd.get('topic'), [])
        self.assertGreater(len(nerd.get('theme')), 0)
        self.assertIn("Optical physics", nerd.get('theme'))

        argline = "-q -w "+self.workdir+" topics "+bagdir+" -a"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertEqual(len(nerd.get('topic')), 0)
        nerd = bag.nerdm_record(True)
        self.assertGreater(len(nerd.get('topic')), 0)
        self.assertEqual(nerd.get('topic')[0]['tag'], "Physics: Optical physics")

    def test_exceute_frompod(self):
        bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), bagdir)
        
        bldr = BagBuilder(self.workdir, "pdr2210")
        bldr.update_metadata_for('', {'topic': []}, message="test prep topics")

        bag = NISTBag(bagdir)
        self.assertTrue(os.path.exists(bag.pod_file()))

        argline = "-q -w "+self.workdir+" topics "+bagdir+" -p"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerdm_record(False)
        self.assertGreater(len(nerd.get('topic')), 0)
        self.assertEquals(nerd.get('topic')[0]['tag'], "Physics: Optical physics")

        # test failure when there is no pod file
        os.remove(bag.pod_file())
        self.assertTrue(not os.path.exists(bag.pod_file()))
        with self.assertRaises(cli.PDRCommandFailure):
            self.cmd.execute(argline.split(), deepcopy(self.config))

                  
        


if __name__ == '__main__':
    test.main()

