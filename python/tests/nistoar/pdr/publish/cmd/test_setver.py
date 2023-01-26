import os, sys, logging, argparse, pdb, imp, time, json, shutil
import unittest as test
from copy import deepcopy
from datetime import date

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish.cmd import setver
from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")

class TestSetverCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.config = {}
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(setver)

        self.bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), self.bagdir)
        
    def tearDown(self):
        self.tf.clean()

    def test_parse(self):
        args = self.cmd.parse_args("-q setver pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "setver")
        self.assertEqual(args.aipid, ["pdr2222"])
        self.assertIsNone(args.bagparent)
        self.assertIsNone(args.level)
        self.assertIsNone(args.setver)
        self.assertFalse(args.incr4md)
        self.assertFalse(args.incr4d)
        self.assertFalse(args.validate)
        self.assertFalse(args.asannots)
        self.assertIsNone(args.why)
        self.assertIsNone(args.repourl)

        argline = "-q -w "+self.workdir+" setver -b mdserv pdr2210 -a -H goober -s 1.1"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "setver")
        self.assertEqual(args.aipid, ["pdr2210"])
        self.assertEqual(args.bagparent, "mdserv")
        self.assertIsNone(args.level)
        self.assertEqual(args.setver, "1.1")
        self.assertFalse(args.incr4md)
        self.assertFalse(args.incr4d)
        self.assertFalse(args.validate)
        self.assertTrue(args.asannots)
        self.assertEqual(args.why, "goober")
        self.assertIsNone(args.repourl)

    def test_increment_version(self):
        self.assertEqual(setver.increment_version("1.0.0", 1), "1.0.1")
        self.assertEqual(setver.increment_version("1.0.1", 2), "1.1.0")
        self.assertEqual(setver.increment_version("1.0.0+ (editing)", 2), "1.1.0")
        self.assertEqual(setver.increment_version("1.0.1", 3), "2.0.0")
        with self.assertRaises(ValueError):
            setver.increment_version("1.0.1", 5)
        with self.assertRaises(ValueError):
            setver.increment_version("1.0.1", -5)

    def test_execute_noop(self):
        argline = "-q -w "+self.workdir+" setver pdr2210 -a"
        with self.assertRaises(cli.PDRCommandFailure):
            self.cmd.execute(argline.split(), deepcopy(self.config))
            
    def test_execute_md(self):
        bag = NISTBag(self.bagdir)
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('releaseHistory', annot)
        self.assertNotIn('releaseHistory', nerd)

        argline = "-q -w "+self.workdir+" setver pdr2210 -m"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.1")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        self.assertNotIn('releaseHistory', annot)
        self.assertNotIn('releaseHistory', nerd)

        argline = "-q -w "+self.workdir+" setver pdr2210 -m -a"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(annot['version'], "1.0.2")
        self.assertEqual(nerd['version'], "1.0.1")
        self.assertNotIn('versionHistory', nerd)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('releaseHistory', annot)
        self.assertNotIn('releaseHistory', nerd)
            
    def test_execute_data(self):
        bag = NISTBag(self.bagdir)
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        
        argline = "-q -w "+self.workdir+" setver pdr2210 -d"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.1.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)

        argline = "-q -w "+self.workdir+" setver pdr2210 -d -a"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.1.0")
        self.assertEqual(annot['version'], "1.2.0")
        self.assertNotIn('versionHistory', nerd)
        self.assertNotIn('versionHistory', annot)
            
    def test_execute_level(self):
        bag = NISTBag(self.bagdir)
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        
        argline = "-q -w "+self.workdir+" setver pdr2210 -i 2"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.1.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        
        argline = "-q -w "+self.workdir+" setver pdr2210 -i 3"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "2.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        
        argline = "-q -w "+self.workdir+" setver pdr2210 -i 1"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "2.0.1")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)

    def test_execute_set(self):
        bag = NISTBag(self.bagdir)
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        
        argline = "-q -w "+self.workdir+" setver pdr2210 -s 3.1.0rc4"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "3.1.0rc4")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        
    def test_execute_hist(self):
        bag = NISTBag(self.bagdir)
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('versionHistory', nerd)

        argline = "-q -w "+self.workdir+" setver pdr2210 -H update"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.0")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('releaseHistory', annot)
        self.assertNotIn('versionHistory', nerd)
        history = nerd['releaseHistory']
        self.assertEqual(history['@id'], "ark:/88434/mds00hw91v/pdr:v")
        history = history['hasRelease']
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['description'], "update")
        self.assertEqual(history[0]['@id'], "ark:/88434/mds00hw91v/pdr:v/1.0.0")
        self.assertEqual(history[0]['location'],
                         "https://data.nist.gov/od/id/ark:/88434/mds00hw91v/pdr:v/1.0.0")
        self.assertEqual(history[0]['issued'], date.today().isoformat())

        argline = "-q -w "+self.workdir+" setver pdr2210 -m -H again"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.1")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        self.assertNotIn('releaseHistory', annot)
        history = nerd['releaseHistory']['hasRelease']
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['description'], "update")
        self.assertEqual(history[1]['description'], "again")

        argline = "-q -w "+self.workdir+" setver pdr2210 -H foobar"
        self.cmd.execute(argline.split(), deepcopy(self.config))
        nerd = bag.nerd_metadata_for('', False)
        annot = bag.annotations_metadata_for('')
        self.assertEqual(nerd['version'], "1.0.1")
        self.assertNotIn('version', annot)
        self.assertNotIn('versionHistory', annot)
        history = nerd['releaseHistory']['hasRelease']
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['description'], "update")
        self.assertEqual(history[1]['description'], "foobar")
        

        
            


if __name__ == '__main__':
    test.main()

