import os, sys, logging, argparse, pdb, imp, time, json, shutil
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import cli, utils
from nistoar.pdr.publish.cmd import validate
from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr.preserv.bagit import NISTBag, validate as vald8
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")

class TestServenerdCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.config = {}
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(validate)

        cfgmod.configure_log(os.path.join(self.workdir, "pdr.log"))

    def tearDown(self):
        self.tf.clean()

    def test_parse(self):
        args = self.cmd.parse_args("-q validate pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "validate")
        self.assertEqual(args.aipid, "pdr2222")
        self.assertIsNone(args.bagparent)
        self.assertIsNone(args.parts)
        self.assertIsNone(args.fpath)

        argline = "-q -w "+self.workdir+" validate -b mdserv pdr2210 -r -f a/b.c -B -M"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "validate")
        self.assertEqual(args.aipid, "pdr2210")
        self.assertEqual(args.bagparent, "mdserv")
        self.assertIn('B', args.parts)
        self.assertIn('M', args.parts)
        self.assertIn('r', args.parts)
        self.assertEqual(args.fpath, "a/b.c")

    def test_validate_aip(self):
        bag = NISTBag(os.path.join(datadir, "samplembag"))
        log = logging.getLogger("test")

        self.assertTrue(validate.validate_aip(bag, log))
        self.assertTrue(validate.validate_aip(bag, log, failon=vald8.REC))

        bag = NISTBag(os.path.join(datadir, "metadatabag"))
        self.assertFalse(validate.validate_aip(bag, log))

    def test_validate_multibag(self):
        bag = NISTBag(os.path.join(datadir, "samplembag"))
        log = logging.getLogger("test")

        self.assertTrue(validate.validate_multibag(bag, log))
        self.assertTrue(validate.validate_multibag(bag, log, failon=vald8.REC))

        bag = NISTBag(os.path.join(datadir, "metadatabag"))
        self.assertFalse(validate.validate_multibag(bag, log))

    def test_validate_bag(self):
        bagdir = os.path.join(self.workdir, "samplembag")
        shutil.copytree(os.path.join(datadir, "samplembag"), bagdir)
        bag = NISTBag(bagdir)
        log = logging.getLogger("test")

        self.assertTrue(validate.validate_bag(bag, log))
        self.assertTrue(validate.validate_bag(bag, log, failon=vald8.REC))

        os.remove(os.path.join(bagdir, "bagit.txt"))
        self.assertFalse(validate.validate_bag(bag, log))

    def test_validate_nerdm(self):
        bagdir = os.path.join(self.workdir, "samplembag")
        shutil.copytree(os.path.join(datadir, "samplembag"), bagdir)
        bag = NISTBag(bagdir)
        log = logging.getLogger("test")

        self.assertTrue(validate.validate_nerdm(bag, log))
        self.assertTrue(validate.validate_nerdm(bag, log, merge=True))

        utils.write_json({"description": "goob"}, os.path.join(bagdir,"metadata","annot.json"))
        self.assertFalse(validate.validate_nerdm(bag, log, merge=True))

    def test_validate_nerdm_for(self):
        bagdir = os.path.join(self.workdir, "samplembag")
        shutil.copytree(os.path.join(datadir, "samplembag"), bagdir)
        bag = NISTBag(bagdir)
        log = logging.getLogger("test")

        self.assertTrue(validate.validate_nerdm_for(bag, '', log))
        self.assertTrue(validate.validate_nerdm_for(bag, 'trial3/trial3a.json', log))

        utils.write_json({"description": "goob"}, os.path.join(bagdir,"metadata","annot.json"))
        self.assertFalse(validate.validate_nerdm_for(bag, '', log, merge=True))

    def test_execute(self):
        argsline = "-q validate -b "+datadir+" samplembag"
        self.cmd.execute(argsline.split())

        argsline = "-q validate -b "+datadir+" metadatabag"
        with self.assertRaises(cli.PDRCommandFailure):
            self.cmd.execute(argsline.split())


    def test_execute_nerdm(self):
        argsline = "-q validate -n -b "+datadir+" samplembag"
        self.cmd.execute(argsline.split())

        argsline = "-q validate -n -b "+datadir+" metadatabag"
        self.cmd.execute(argsline.split())

        bagdir = os.path.join(self.workdir, "samplembag")
        shutil.copytree(os.path.join(datadir, "samplembag"), bagdir)
        argsline = "-q validate -n -b "+self.workdir+" samplembag"
        self.cmd.execute(argsline.split())

        nerd = utils.read_json(os.path.join(bagdir,"metadata","nerdm.json"))
        nerd['description'] = "goob"
        utils.write_json(nerd, os.path.join(bagdir,"metadata","nerdm.json"))
        with self.assertRaises(cli.PDRCommandFailure):
            self.cmd.execute(argsline.split())

if __name__ == '__main__':
    test.main()


