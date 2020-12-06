import os, sys, logging, argparse, pdb, imp, time, json, shutil
import unittest as test
from copy import deepcopy
from datetime import date
from StringIO import StringIO

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish import cmd as pub
from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")

class TestPubCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.cwd = os.getcwd()
        os.chdir(self.tf.root)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tf.clean()

    def test_define_pub_options(self):
        p = argparse.ArgumentParser()
        pub.define_pub_opts(p)
        args = p.parse_args("pdr2210".split())
        self.assertEqual(args.aipid, "pdr2210")
        self.assertIsNone(args.bagparent)
        args = p.parse_args("pdr2210 -b goob".split())
        self.assertEqual(args.aipid, "pdr2210")
        self.assertEqual(args.bagparent, "goob")

    def test_load_into(self):
        p = argparse.ArgumentParser()
        cmd = pub.load_into(p, "goob")
        self.assertIsNotNone(cmd)
        self.assertTrue(hasattr(cmd, "execute"))

        usage = StringIO()
        p.print_help(file=usage)
        self.assertIn("{prepupd,servenerd,setver,validate,fix}", usage.getvalue())

    def test_determine_bag_path(self):
        p = argparse.ArgumentParser()
        pub.define_pub_opts(p)
        
        args = p.parse_args("pdr2210".split())
        self.assertEqual(args.aipid, "pdr2210")
        workdir, bagparent, bagdir = pub.determine_bag_path(args, {})
        self.assertEqual(workdir, os.getcwd())
        self.assertEqual(bagparent, workdir)
        self.assertEqual(bagdir, os.path.join(workdir, "pdr2210"))

        cfg = { 'working_dir': "/tmp" }
        args = p.parse_args("pdr2210".split())
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(workdir, "/tmp")
        self.assertEqual(bagparent, "/tmp")
        self.assertEqual(bagdir, "/tmp/pdr2210")

        args = p.parse_args("pdr2210 -b /opt".split())
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(workdir, "/tmp")
        self.assertEqual(bagparent, "/opt")
        self.assertEqual(bagdir, "/opt/pdr2210")

        args = p.parse_args("pdr2210 -b pdr/bags".split())
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(workdir, "/tmp")
        self.assertEqual(bagparent, "/tmp/pdr/bags")
        self.assertEqual(bagdir, "/tmp/pdr/bags/pdr2210")

        args = p.parse_args("pdr2210 -b ./bags".split())
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(workdir, "/tmp")
        self.assertEqual(bagparent, os.path.join(os.getcwd(), "bags"))
        self.assertEqual(bagdir, os.path.join(bagparent, "pdr2210"))

        # by default, aipid given as path are relative to CWD
        args = p.parse_args("curate/pdr2210 -b ./bags".split())      # -b is ignored
        self.assertEqual(args.aipid, "curate/pdr2210")
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(workdir, "/tmp")
        self.assertEqual(bagparent, os.path.join(os.getcwd(), "curate"))
        self.assertEqual(bagdir, os.path.join(bagparent, "pdr2210"))

        # if the working dir is given on the command line, we can allow the aipid path be relative to it
        p.add_argument("-w", type=str, metavar="DIR", dest="workdir")
        args = p.parse_args("curate/pdr2210 -w /pdr/bags".split())      # -b is ignored
        self.assertEqual(args.aipid, "curate/pdr2210")
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(workdir, "/pdr/bags")
        self.assertEqual(bagparent, "/pdr/bags/curate")    # because ./curate/pdr2210 does not exist
        self.assertEqual(bagdir, os.path.join(bagparent, "pdr2210"))

        # create ./curate/pdr2210 and see difference
        self.tf.mkdir("curate")
        os.mkdir("curate/pdr2210")
        args = p.parse_args("curate/pdr2210 -w /pdr/bags".split())
        self.assertEqual(args.aipid, "curate/pdr2210")
        workdir, bagparent, bagdir = pub.determine_bag_path(args, cfg)
        self.assertEqual(args.aipid, "pdr2210")
        self.assertEqual(workdir, "/pdr/bags")
        self.assertEqual(bagparent, os.path.join(os.getcwd(), "curate"))
        self.assertEqual(bagdir, os.path.join(bagparent, "pdr2210"))
        
        
        

        
            


if __name__ == '__main__':
    test.main()

