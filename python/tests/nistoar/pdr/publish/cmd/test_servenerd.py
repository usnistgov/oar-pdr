import os, sys, logging, argparse, pdb, imp, time, json
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish.cmd import servenerd
from nistoar.pdr.exceptions import PDRException, ConfigurationException
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
        self.cmd.load_subcommand(servenerd)

    def tearDown(self):
        self.tf.clean()

    def test_parse(self):
        args = self.cmd.parse_args("-q servenerd pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "servenerd")
        self.assertEqual(args.aipid, ["pdr2222"])
        self.assertIsNone(args.bagparent)
        self.assertIsNone(args.nrdserv)

        argline = "-q -w "+self.workdir+" servenerd -b mdserv pdr2210 -n -"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "servenerd")
        self.assertEqual(args.aipid, ["pdr2210"])
        self.assertEqual(args.bagparent, "mdserv")
        self.assertEqual(args.nrdserv, "-")

    def test_execute(self):
        bagdir = os.path.join(datadir, "metadatabag")
        argline = "-q -w "+self.workdir+" servenerd "+bagdir+" -n "+self.workdir
        self.cmd.execute(argline.split(), deepcopy(self.config))

        outrec = os.path.join(self.workdir, "metadatabag.json")
        self.assertTrue(os.path.isfile(outrec))
        with open(outrec) as fd:
            nerd = json.load(fd)
        self.assertIn('@context', nerd)
        self.assertIn('@id', nerd)
        self.assertIn('components', nerd)



if __name__ == '__main__':
    test.main()

