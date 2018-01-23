import os, sys, pdb, json, logging
import unittest as test
from copy import deepcopy
from StringIO import StringIO

from nistoar.testing import *
from nistoar.pdr.notify.base import Notice
import nistoar.pdr.notify.cli as cli
from nistoar.pdr.exceptions import ConfigurationException

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')

notice_data = {
    "type": "FAILURE",
    "title": "data is devoid of science",
    "description": [
        "The data is dull and uninteresting.  Pure noise is less tedious than this data.  It reads like 'Smoke on the Water' but without the changing notes.",
        "This data should not be saved"
    ],
    "origin": "Preservation",
    "issued": "today",
    "metadata": {
        "color": "grey",
        "excitation": False
    }
}

def setUpModule():
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_builder.log"))
    loghdlr.setLevel(logging.INFO)
    rootlog.addHandler(loghdlr)

def tearDownModule():
    rmtmpdir()

class TestCLI(test.TestCase):

    def test_define_options(self):
        parser = cli.define_options("goober")
        self.assertEqual(parser.prog, "goober")
        self.assertTrue(parser.description)

        # This test will write to standard out
        #
        # with self.assertRaises(SystemExit):
        #     opts = parser.parse_args([])

        opts = parser.parse_args(["-s", "Hello world!"])
        self.assertEqual(opts.summary, "Hello world!")
        self.assertEqual(opts.status, "INFO")
        self.assertFalse(opts.stdin)
        self.assertFalse(opts.stdout)
        self.assertIsNone(opts.origin)
        self.assertIsNone(opts.mailserver)
        self.assertIsNone(opts.frm)
        self.assertIsNone(opts.cfgfile)
        self.assertEqual(opts.to, [])

        args = "-T gurn -IO -l WARN -s Hello! -t goob@nist.gov -f me.eye@nist.gov "+\
               " -t help@nist.gov -o pdr -c config.yml -m email.nist.gov"
        opts = parser.parse_args(args.split())
        self.assertEqual(opts.summary, "Hello!")
        self.assertEqual(opts.status, "WARN")
        self.assertEqual(opts.origin, "pdr")
        self.assertEqual(opts.mailserver, "email.nist.gov")
        self.assertTrue(opts.stdin)
        self.assertTrue(opts.stdout)
        self.assertEqual(opts.to, ["goob@nist.gov", "help@nist.gov"])
        self.assertEqual(opts.frm, "me.eye@nist.gov")
        self.assertEqual(opts.cfgfile, "config.yml")
        
    def test_Failure(self):
        ex = cli.Failure("oops!")
        self.assertEquals(str(ex), "oops!")
        self.assertEquals(ex.exitcode, 1)

        ex = cli.Failure("boo!", 3, RuntimeError("oops!"))
        self.assertEquals(str(ex), "boo!")
        self.assertEquals(ex.exitcode, 3)
        self.assertEquals(str(ex.cause), "oops!")

        ex = cli.Failure(cause=RuntimeError("oops!"))
        self.assertEquals(str(ex.cause), "oops!")
        self.assertEquals(str(ex), "oops!")
        self.assertEquals(ex.exitcode, 1)

    def test_read_config(self):
        cfgfile = os.path.join(testdatadir, "config.yml")
        cfg = cli.read_config(cfgfile)
        self.assertEquals(cfg['archive_targets'], ['operators'])
        
    def test_read_bad_config(self):
        with self.assertRaises(cli.Failure):
            cli.read_config(cli.__file__)

    def test_parse_addr(self):
      
        self.assertEqual(cli._parse_addr("me@cyber.nist.gov"),
                         ["me@cyber.nist.gov", ''])

        with self.assertRaises(ValueError):
            cli._parse_addr("me")
        with self.assertRaises(ValueError):
            cli._parse_addr("me@nist")

        self.assertEqual(cli._parse_addr("me@nist.gov, you@nist.gov, him@n.gov"),
                         ["me@nist.gov", 'you@nist.gov, him@n.gov'])
        self.assertEqual(cli._parse_addr("me@nist.gov, you@nist.gov, him@gov"),
                         ["me@nist.gov", 'you@nist.gov, him@gov'])
        with self.assertRaises(ValueError):
            cli._parse_addr("me@nist, you@nist.gov, him@n.gov")

        self.assertEqual(cli._parse_addr('"Myself J. Eye" <me@cyber.nist.gov>'),
                         ["Myself J. Eye", "me@cyber.nist.gov", ''])
        self.assertEqual(cli._parse_addr('"Myself J. Eye" <me@cyber.nist.gov>, goober'),
                         ["Myself J. Eye", "me@cyber.nist.gov", 'goober'])
        
        
        

    def test_build_ops_config(self):
        parser = cli.define_options("goob")
        args = "-t goob@nist.gov -f me@nist.gov -s boo "+\
               "-t help@nist.gov -m email.nist.gov -A /tmp"
        opts = parser.parse_args(args.split())
        cfg = cli.build_ops_config(opts)

        self.assertIn('channels', cfg)
        self.assertIn('targets', cfg)
        self.assertEqual(len(cfg['channels']), 2)
        self.assertEqual(cfg['channels'][0]["smtp_server"], "email.nist.gov")
        self.assertEqual(cfg['channels'][0]["name"], "email")
        self.assertEqual(cfg['channels'][0]["type"], "email")
        self.assertEqual(cfg['channels'][1]["dir"], "/tmp")
        self.assertEqual(cfg['channels'][1]["name"], "archive")
        self.assertEqual(cfg['channels'][1]["type"], "archive")
        self.assertEqual(len(cfg['targets']), 1)
        self.assertEqual(cfg['targets'][0]["name"], "ops")
        self.assertEqual(cfg['targets'][0]["type"], "email")
        self.assertEqual(cfg['targets'][0]["channel"], "email")
        self.assertEqual(cfg['targets'][0]["from"], "me@nist.gov")
        self.assertEqual(cfg['targets'][0]["to"],
                         ["goob@nist.gov", "help@nist.gov"])
        self.assertEqual(cfg['archive_targets'], ['ops'])
        
        args = "-m email.nist.gov:825 -s boo -T admin -A /tmp".split()
        args += [ "-t", '"Goober" <goob@nist.gov>',
                  '-f', '"Myself J. Eye" <me@nist.gov>',
                  '-t',  'help@nist.gov' ]
        opts = parser.parse_args(args)
        cfg = cli.build_ops_config(opts)

        self.assertIn('channels', cfg)
        self.assertIn('targets', cfg)
        self.assertEqual(len(cfg['channels']), 2)
        self.assertEqual(cfg['channels'][0]["smtp_server"], "email.nist.gov")
        self.assertEqual(cfg['channels'][0]["smtp_port"], 825)
        self.assertEqual(cfg['channels'][0]["name"], "email")
        self.assertEqual(cfg['channels'][0]["type"], "email")
        self.assertEqual(cfg['channels'][1]["dir"], "/tmp")
        self.assertEqual(cfg['channels'][1]["name"], "archive")
        self.assertEqual(cfg['channels'][1]["type"], "archive")
        self.assertEqual(len(cfg['targets']), 1)
        self.assertEqual(cfg['targets'][0]["name"], "admin")
        self.assertEqual(cfg['targets'][0]["type"], "email")
        self.assertEqual(cfg['targets'][0]["channel"], "email")
        self.assertEqual(cfg['targets'][0]["from"],
                         ["Myself J. Eye", "me@nist.gov"])
        self.assertEqual(cfg['targets'][0]["to"],
                         [["Goober", "goob@nist.gov"], "help@nist.gov"])
        self.assertEqual(cfg['archive_targets'], ['admin'])

        args = "-s boo".split()
        args += [ "-t", '"Goober" <goob@nist.gov>',
                  '-f', '"Myself J. Eye" <me@nist.gov>',
                  '-t',  'help@nist.gov' ]
        opts = parser.parse_args(args)
        cfg = cli.build_ops_config(opts)

        self.assertNotIn('channels', cfg)
        self.assertIn('targets', cfg)
        self.assertEqual(len(cfg['targets']), 1)
        self.assertEqual(cfg['targets'][0]["name"], "ops")
        self.assertEqual(cfg['targets'][0]["type"], "email")
        self.assertEqual(cfg['targets'][0]["channel"], "email")
        self.assertEqual(cfg['targets'][0]["from"],
                         ["Myself J. Eye", "me@nist.gov"])
        self.assertEqual(cfg['targets'][0]["to"],
                         [["Goober", "goob@nist.gov"], "help@nist.gov"])

        # test failure when -A dir does not exist
        args = "-s boo -A /goober".split()
        args += [ "-t", '"Goober" <goob@nist.gov>',
                  '-f', '"Myself J. Eye" <me@nist.gov>',
                  '-t',  'help@nist.gov' ]
        opts = parser.parse_args(args)
        with self.assertRaises(cli.Failure):
            cfg = cli.build_ops_config(opts)

    def test_create_notice(self):
        parser = cli.define_options("goob")
        args = "-s hello!"
        opts = parser.parse_args(args.split())
        note = cli.create_notice(opts)
        self.assertTrue(isinstance(note, Notice))
        self.assertEqual(note.type, "INFO")
        self.assertEqual(note.title, "hello!")
        self.assertIsNone(note.description)
        self.assertIsNone(note.origin)
        
        args = "-o basement -s hello! -l CRUSTY"
        opts = parser.parse_args(args.split())
        note = cli.create_notice(opts)
        self.assertTrue(isinstance(note, Notice))
        self.assertEqual(note.type, "CRUSTY")
        self.assertEqual(note.title, "hello!")
        self.assertEqual(note.origin, "basement")
        self.assertIsNone(note.description)

        desc = StringIO("this is the end.\nmy only friend, the end.")
        args = "-I -o basement -s hello! -l CRUSTY"
        opts = parser.parse_args(args.split())
        note = cli.create_notice(opts, desc)
        self.assertTrue(isinstance(note, Notice))
        self.assertEqual(note.type, "CRUSTY")
        self.assertEqual(note.title, "hello!")
        self.assertEqual(note.origin, "basement")
        self.assertEqual(note.description,
                         "this is the end.\nmy only friend, the end.")


    def test_StdoutArchiver(self):

        note = Notice("INFO", "hello!")
        out = MyStringIO()
        chan = cli.StdoutArchiver({"name": "archiver", "pretty": False}, out)
        chan.archive("hank", note)

        self.assertGreater(len(out.getvalue()), 10)

    def test_StdoutMailer(self):

        note = Notice("INFO", "hello!")
        out = MyStringIO()
        chan = cli.StdoutMailer({"name": "archiver", "pretty": False}, out)
        chan.send_email("me@nist.gov", ["you@nist.gov", "him@nist.gov"])

        self.assertGreater(len(out.getvalue()), 10)

class MyStringIO(StringIO):
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def __enter__(self):
        return self

if __name__ == '__main__':
    test.main()
