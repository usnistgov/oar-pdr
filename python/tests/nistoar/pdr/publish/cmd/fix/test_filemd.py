import os, sys, logging, argparse, pdb, imp, time, json, shutil
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish.cmd.fix import filemd
from nistoar.pdr.cli import PDRCommandFailure
from nistoar.pdr.utils import checksum_of
from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
from nistoar.pdr.preserv.bagger import midas3 as midas
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(os.path.dirname(testdir)))
datadir = os.path.join(pdrmoddir, "preserv", "data")

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_cmd.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestFilemdCmd(test.TestCase):

    bagdata = os.path.join(datadir, "metadatabag")
    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.troot = self.tf.mkdir("fixfilemd")
        self.revdir = os.path.join(self.troot, "review")
        os.mkdir(self.revdir)
        shutil.copytree(self.sipdata, os.path.join(self.revdir, "1491"))

        self.bagparent = os.path.join(self.troot, "mdbags")
        os.mkdir(self.bagparent)
        self.bagdir = os.path.join(self.bagparent, self.midasid)
        shutil.copytree(self.bagdata, self.bagdir)

        self.cfg = {
            "working_dir":      self.troot,
            "metadata_bag_dir": self.bagparent,
            "review_dir":       self.revdir,
            "bagger": {
            }
        }
        self.bgrcfg = {
            "data_directory":   os.path.join(self.revdir, "1491"),
            "bag_parent":       self.bagparent,
            "bagger": {}
        }

        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(filemd)

    def set_bagger_file(self, when=None):
        if not when:
            when = 1714985652.0
        self.bgrcfg['last_file_examine'] = when
        outf = os.path.join(self.bagdir, "metadata", midas.MIDASMetadataBagger.BGRMD_FILENAME)
        with open(outf, 'w') as fd:
            json.dump(self.bgrcfg, fd, indent=2)

    def tearDown(self):
        self.tf.clean()

    def test_parse(self):
        args = self.cmd.parse_args("-q filemd pdr2210".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "filemd")
        self.assertEqual(args.aipid, ["pdr2210"])
        self.assertIsNone(args.bagparent)
        self.assertFalse(args.correctcsf)
        self.assertFalse(args.dryrun)
        self.assertFalse(args.force)

        argline = "-q -w "+self.troot+" filemd -b mdserv pdr2210 -f --correct-cs-file -n"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.troot)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "filemd")
        self.assertEqual(args.aipid, ["pdr2210"])
        self.assertEqual(args.bagparent, "mdserv")
        self.assertTrue(args.correctcsf)
        self.assertTrue(args.dryrun)
        self.assertTrue(args.force)

    def test_create_bagger(self):
        argline = "-q filemd "+self.midasid+" -f --correct-cs-file -n"
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)
        self.assertEqual(bagger.midasid, self.midasid)
        self.assertEqual(bagger.sip.revdatadir, os.path.join(self.revdir, "1491"))
        self.assertEqual(bagger.bagparent, self.bagparent)

        argline = "-q filemd "+self.midasid+" -d "+self.revdir
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)
        self.assertEqual(bagger.midasid, self.midasid)
        self.assertEqual(bagger.sip.revdatadir, self.revdir)
        self.assertEqual(bagger.bagparent, self.bagparent)

    def test_create_bagger_via_baggermd(self):
        self.set_bagger_file()

        argline = "-q filemd "+self.midasid+" -f --correct-cs-file -n"
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)
        self.assertEqual(bagger.midasid, self.midasid)
        self.assertEqual(bagger.sip.revdatadir, os.path.join(self.revdir, "1491"))
        self.assertEqual(bagger.bagparent, self.bagparent)

    def test_which_files(self):
        datadir = os.path.join(self.revdir, "1491")

        # should select all files since none of the metadata files have checksums
        argline = "-q filemd -n "+self.midasid
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)
        
        files = filemd.which_files(args, bagger, rootlog)
        self.assertEqual(len(files), 3)
        self.assertEqual(files['trial1.json'], os.path.join(datadir, "trial1.json"))
        self.assertEqual(files['trial2.json'], os.path.join(datadir, "trial2.json"))
        self.assertEqual(files['trial3/trial3a.json'], os.path.join(datadir, "trial3/trial3a.json"))

        argline = "-q filemd "+self.midasid+" trail2.json"
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)
        with self.assertRaises(PDRCommandFailure):
            filemd.which_files(args, bagger, rootlog)

        argline = "-q filemd "+self.midasid+" trial2.json"
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)
        
        files = filemd.which_files(args, bagger, rootlog)
        self.assertEqual(len(files), 1)
        self.assertEqual(files['trial2.json'], os.path.join(datadir, "trial2.json"))

    def test_examine_file(self):
        datadir = os.path.join(self.revdir, "1491")

        argline = "-q filemd -n "+self.midasid
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)

        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        sz = fmd.get('size')
        self.assertIsNotNone(sz)
        self.assertIsNone(fmd.get('checksum'))
        bagger.bagbldr.update_metadata_for("trial1.json", {"size": 0})
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertEqual(fmd['size'], 0)

        cs = filemd.examine_file(bagger, "trial1.json", os.path.join(datadir, "trial1.json"), rootlog)
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNotNone(fmd.get('size'))
        self.assertIsNotNone(fmd.get('checksum'))
        self.assertEqual(fmd['checksum'].get('hash'), cs)
        self.assertEqual(fmd['size'], sz)

    def test_execute(self):
        datadir = os.path.join(self.revdir, "1491")
        self.assertFalse(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))

        argline = "-v filemd "+self.midasid+" trial3/trial3a.json"
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)

        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNone(fmd.get('checksum'))
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial3/trial3a.json")
        self.assertIsNone(fmd.get('checksum'))

        args.aipid = [args.aipid]
        filemd.execute(args, self.cfg, rootlog)
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNone(fmd.get('checksum'))
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial3/trial3a.json")
        self.assertIsNotNone(fmd.get('checksum'))
        self.assertFalse(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))

        argline = "-v filemd "+self.midasid
        args = self.cmd.parser.parse_args(argline.split())

        filemd.execute(args, self.cfg, rootlog)
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNotNone(fmd.get('checksum'))
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial3/trial3a.json")
        self.assertIsNotNone(fmd.get('checksum'))
        self.assertFalse(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))

    def test_correctcsf(self):
        datadir = os.path.join(self.revdir, "1491")
        self.assertFalse(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))
        self.assertTrue(os.path.exists(os.path.join(datadir, "trial1.json.sha256")))
        with open(os.path.join(datadir, "trial1.json.sha256"), 'w') as fd:
            fd.write("aaaa bbbb")

        argline = "-v filemd -C "+self.midasid
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)

        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNone(fmd.get('checksum'))
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIsNone(fmd.get('checksum'))

        args.aipid = [args.aipid]
        filemd.execute(args, self.cfg, rootlog)
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNotNone(fmd.get('checksum'))
        cs = fmd['checksum'].get('hash')
        with open(os.path.join(datadir, "trial1.json.sha256")) as fd:
            fcs = fd.read().strip()
        self.assertEqual(fcs, cs)

        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIsNotNone(fmd.get('checksum'))
        cs = fmd['checksum'].get('hash')
        self.assertTrue(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))

        with open(os.path.join(datadir, "trial2.json.sha256")) as fd:
            fcs = fd.read().strip()
        self.assertEqual(fcs, cs)

    def test_dryrun(self):
        datadir = os.path.join(self.revdir, "1491")
        self.assertFalse(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))
        self.assertTrue(os.path.exists(os.path.join(datadir, "trial1.json.sha256")))
        with open(os.path.join(datadir, "trial1.json.sha256"), 'w') as fd:
            fd.write("aaaa bbbb")
        t1cs = checksum_of(os.path.join(datadir, "trial1.json.sha256"))

        argline = "-v filemd -n -C "+self.midasid
        args = self.cmd.parser.parse_args(argline.split())
        args.aipid = args.aipid[0]
        bagger = filemd.create_bagger(args, self.cfg, rootlog)

        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNone(fmd.get('checksum'))
        t1 = checksum_of(bagger.bagbldr.bag.nerd_file_for("trial1.json"))
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIsNone(fmd.get('checksum'))
        t2 = checksum_of(bagger.bagbldr.bag.nerd_file_for("trial2.json"))

        args.aipid = [args.aipid]
        filemd.execute(args, self.cfg, rootlog)

        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial1.json")
        self.assertIsNone(fmd.get('checksum'))
        self.assertEqual(checksum_of(bagger.bagbldr.bag.nerd_file_for("trial1.json")), t1)
        fmd = bagger.bagbldr.bag.nerd_metadata_for("trial2.json")
        self.assertIsNone(fmd.get('checksum'))
        self.assertEqual(checksum_of(bagger.bagbldr.bag.nerd_file_for("trial2.json")), t2)
        self.assertEqual(checksum_of(os.path.join(datadir, "trial1.json.sha256")), t1cs)
        self.assertFalse(os.path.exists(os.path.join(datadir, "trial2.json.sha256")))
        
        


if __name__ == '__main__':
    test.main()

