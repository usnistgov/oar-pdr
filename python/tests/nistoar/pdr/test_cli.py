import os, sys, logging, argparse, pdb
import unittest as test

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.exceptions import PDRException, ConfigurationException
import nistoar.pdr.config as cfgmod

tmpd = None

def setUpModule():
    global tmpd
    ensure_tmpdir()
    tmpd = tmpdir()

def tearDownModule():
    rmtmpdir()

class TestModFunctions(test.TestCase):

    def test_define_opts(self):
        p = cli.define_opts()
        self.assertEqual(p.prog, "pdr")
        self.assertIn("PDR", p.description)
        self.assertIn("help specifically on CMD", p.epilog)
        
        args = p.parse_args([])
        self.assertEqual(args.workdir, ".")
        self.assertIsNone(args.conf)
        self.assertIsNone(args.logfile)
        self.assertFalse(args.quiet)
        self.assertFalse(args.verbose)
        self.assertFalse(args.debug)

        p = cli.define_opts("goob")
        self.assertEqual(p.prog, "goob")
        args = p.parse_args([])
        self.assertEqual(args.workdir, ".")
        self.assertIsNone(args.conf)
        self.assertIsNone(args.logfile)
        self.assertFalse(args.quiet)
        self.assertFalse(args.verbose)
        self.assertFalse(args.debug)

        parser = argparse.ArgumentParser("fred", None, "go to work", "good work")
        p = cli.define_opts("goob", parser)
        self.assertTrue(p is parser)
        self.assertEqual(p.prog, "fred")
        args = p.parse_args([])
        self.assertEqual(args.workdir, ".")
        self.assertIsNone(args.conf)
        self.assertIsNone(args.logfile)
        self.assertFalse(args.quiet)
        self.assertFalse(args.verbose)
        self.assertFalse(args.debug)

    def test_PDRComandFailure(self):
        ex = cli.PDRCommandFailure("goob", "hey, don't do that!", 3)
        self.assertEqual(ex.cmd, "goob")
        self.assertEqual(ex.stat, 3)
        self.assertIsNone(ex.cause)
        self.assertEqual(str(ex), "hey, don't do that!")


class TestPDRCLI(test.TestCase):

    def resetLogfile(self):
        rootlog = logging.getLogger()
        if cfgmod._log_handler:
            rootlog.removeHandler(cfgmod._log_handler)
        if self.logfile and os.path.exists(self.logfile):
            os.remove(self.logfile)
        self.logfile = None

    def setUp(self):
        self.logfile = None
        self.resetLogfile()

    def tearDown(self):
        self.resetLogfile()

    def test_ctor(self):
        cmd = cli.PDRCLI()
        self.assertEqual(cmd.suitename, "pdr")
        self.assertIsNotNone(cmd.parser)
        self.assertEqual(cmd.parser.prog, "pdr")
        self.assertIsNotNone(cmd._subparser_src)
        self.assertEqual(cmd._cmds, {})
        self.assertEqual(cmd._next_exit_offset, 10)

        cmd = cli.PDRCLI("goob")
        self.assertEqual(cmd.suitename, "goob")
        self.assertIsNotNone(cmd.parser)
        self.assertEqual(cmd.parser.prog, "goob")
        self.assertIsNotNone(cmd._subparser_src)
        self.assertEqual(cmd._cmds, {})
        self.assertEqual(cmd._next_exit_offset, 10)

    def test_configure_log_defs(self):
        p = cli.define_opts()
        args = p.parse_args("-q".split())
        cfg = {}
        
        cmd = cli.PDRCLI()
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.pdr")
        self.assertEqual(self.logfile, os.path.join(os.getcwd(), "pdr.log"))
        
    def test_configure_log_defs2(self):
        p = cli.define_opts()
        args = p.parse_args("-q".split())
        cfg = {}
        
        cmd = cli.PDRCLI("gurn")
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.gurn")
        self.assertEqual(self.logfile, os.path.join(os.getcwd(), "gurn.log"))
        
    def test_configure_log_viaargs(self):
        p = cli.define_opts()
        args = p.parse_args("-q -l goober.log".split())
        cfg = {}
        
        cmd = cli.PDRCLI()
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.pdr")
        self.assertEqual(self.logfile, os.path.join(os.getcwd(), "goober.log"))
        
    def test_configure_log_viaargs2(self):
        p = cli.define_opts()
        args = p.parse_args("-q -l /tmp/goober.log".split())
        cfg = {}
        
        cmd = cli.PDRCLI()
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.pdr")
        self.assertEqual(self.logfile, "/tmp/goober.log")
        
    def test_configure_log_viaargs3(self):
        p = cli.define_opts()
        args = p.parse_args("-q -l goober.log".split())
        cfg = {
            "logdir": tmpdir()
        }
        
        cmd = cli.PDRCLI()
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.pdr")
        self.assertEqual(self.logfile, os.path.join(os.getcwd(), "goober.log"))
        
    def test_configure_log_viaconfig(self):
        p = cli.define_opts()
        args = p.parse_args("-q".split())
        cfg = {
            "logfile": "gurn.log"
        }
        
        cmd = cli.PDRCLI()
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.pdr")
        self.assertEqual(self.logfile, os.path.join(os.getcwd(), "gurn.log"))
        
    def test_configure_log_viaconfig2(self):
        p = cli.define_opts()
        args = p.parse_args("-q".split())
        cfg = {
            "logfile": "gurn.log",
            "logdir": "/tmp"
        }
        
        cmd = cli.PDRCLI()
        log = cmd.configure_log(args, cfg)
        self.logfile = cfgmod.global_logfile
        self.assertIsNotNone(log)
        self.assertEqual(log.name, "cli.pdr")
        self.assertEqual(self.logfile, "/tmp/gurn.log")

    class TestCmdMod(object):
        def __init__(self):
            self.default_name = "mock"
            self.help = "mighty helpful"
            self.last_exec = None
        def load_into(self, sp):
            sp.help = "helpful"
            sp.add_argument("uid", metavar="ID", type=str, help="the ID to use")
        def execute(self, args, config, log):
            self.last_exec = { 'args': args, 'config': config, 'log': log }


    def test_load(self):
        cmd = cli.PDRCLI()
        tstmod = self.TestCmdMod()

        cmd.load_subcommand(tstmod)
        self.assertIn("mock", cmd._cmds)
        self.assertTrue(cmd._cmds["mock"][0] is tstmod)
        self.assertEqual(cmd._cmds["mock"][1], 10)
        self.assertEqual(cmd._next_exit_offset, 20)

        cmd.load_subcommand(tstmod, "gurn", 20)
        self.assertIn("mock", cmd._cmds)
        self.assertIn("gurn", cmd._cmds)
        self.assertTrue(cmd._cmds["gurn"][0] is tstmod)
        self.assertEqual(cmd._cmds["gurn"][1], 20)
        self.assertEqual(cmd._next_exit_offset, 20)

        cmd.load_subcommand(tstmod, "foo")
        self.assertIn("mock", cmd._cmds)
        self.assertIn("gurn", cmd._cmds)
        self.assertIn("foo", cmd._cmds)
        self.assertTrue(cmd._cmds["foo"][0] is tstmod)
        self.assertEqual(cmd._cmds["foo"][1], 30)
        self.assertEqual(cmd._next_exit_offset, 40)

        cmd.execute("-q gurn cranston".split())
        self.assertEqual(tstmod.last_exec['args'].cmd, "gurn")
        self.assertEqual(tstmod.last_exec['args'].uid, "cranston")
        self.assertTrue(tstmod.last_exec['args'].quiet)
        self.assertTrue(not tstmod.last_exec['args'].verbose)
        self.assertEqual(tstmod.last_exec['config'],
                         {'logdir': '.', 'logfile': "pdr.log", 'working_dir': '.'})
        self.assertIsNotNone(tstmod.last_exec['log'])

    def test_extract_config_for_cmd(self):
        cmd = cli.PDRCLI()
        tstmod = self.TestCmdMod()
        
        config = {
            "foo": "bar",
            "fred": "felon",
            "cmd": {
                "pub" : {
                    "fred": "cranston",
                    "goober": "cleveland"
                },
                "mock": {
                    "goober": "pittsburgh"
                }
            }
        }

        cfg = cmd.extract_config_for_cmd(config, 'pub', tstmod)
        self.assertEqual(cfg.get('goober'), "cleveland")
        self.assertEqual(cfg.get('fred'), "cranston")
        cfg = cmd.extract_config_for_cmd(config, 'preserve', tstmod)
        self.assertEqual(cfg.get('goober'), "pittsburgh")
        self.assertEqual(cfg.get('fred'), "felon")


if __name__ == '__main__':
    test.main()

