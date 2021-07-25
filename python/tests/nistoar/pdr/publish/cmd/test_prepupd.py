import os, sys, logging, argparse, pdb, imp, time
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish.cmd import prepupd
from nistoar.pdr.exceptions import PDRException, ConfigurationException
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
distarchdir = os.path.join(pdrmoddir, "distrib", "data")
descarchdir = os.path.join(pdrmoddir, "describe", "data")

distarchive = os.path.join(tmpdir(), "distarchive")
mdarchive = os.path.join(tmpdir(), "mdarchive")

def startServices():
    tdir = tmpdir()
    archdir = distarchive
    shutil.copytree(distarchdir, archdir)
    # os.mkdir(archdir)   # keep it empty for now

    srvport = 9091
    pidfile = os.path.join(tdir,"simdistrib"+str(srvport)+".pid")
    wpy = os.path.join(pdrmoddir, "distrib/sim_distrib_srv.py")
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simdistrib.log"), srvport, wpy, archdir, pidfile)
    os.system(cmd)

    archdir = mdarchive
    shutil.copytree(descarchdir, archdir)

    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    wpy = os.path.join(pdrmoddir, "describe/sim_describe_svc.py")
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simrmm.log"), srvport, wpy, archdir, pidfile)
    os.system(cmd)
    time.sleep(0.5)

def stopServices():
    tdir = tmpdir()
    srvport = 9091
    pidfile = os.path.join(tdir,"simdistrib"+str(srvport)+".pid")
    
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                               "simdistrib"+str(srvport)+".pid"))
    os.system(cmd)

    # sometimes stopping with uwsgi doesn't work
    try:
        with open(pidfile) as fd:
            pid = int(fd.read().strip())
        os.kill(pid, signal.SIGTERM)
    except:
        pass

    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    
    cmd = "uwsgi --stop {0}".format(os.path.join(tdir,
                                               "simrmm"+str(srvport)+".pid"))
    os.system(cmd)

    time.sleep(1)

    # sometimes stopping with uwsgi doesn't work
    try:
        with open(pidfile) as fd:
            pid = int(fd.read().strip())
        os.kill(pid, signal.SIGTERM)
    except:
        pass

def setUpModule():
    ensure_tmpdir()
    startServices()

def tearDownModule():
    stopServices()
    rmtmpdir()

class TestPrepupdCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.headcache = self.tf.mkdir("headcache")
        self.config = {
            "repo_access": {
                "headbag_cache": self.headcache,
                "distrib_service": {
                    "service_endpoint": "http://localhost:9091/"
                },
                "metadata_service": {
                    "service_endpoint": "http://localhost:9092/"
                }
            }
        }

        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(prepupd)

    def tearDown(self):
        self.tf.clean()

    def test_parse(self):
        args = self.cmd.parser.parse_args("-q prepupd pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertIsNone(args.cachedir)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "prepupd")
        self.assertEqual(args.aipid, ["pdr2222"])

        argline = "-q -w "+self.workdir+" prepupd pdr2210 -C headbags -u https://data.nist.gov/"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertEqual(args.cachedir, 'headbags')
        self.assertEqual(args.repourl, "https://data.nist.gov/")
        self.assertIsNone(args.replaces)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "prepupd")
        self.assertEqual(args.aipid, ["pdr2210"])

        argline = "-q -w "+self.workdir+" prepupd pdr2210 -C headbags -r pdr2001"
        args = self.cmd.parser.parse_args(argline.split())
        self.assertEqual(args.workdir, self.workdir)
        self.assertEqual(args.cachedir, 'headbags')
        self.assertEqual(args.replaces, "pdr2001")
        self.assertIsNone(args.repourl)
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "prepupd")
        self.assertEqual(args.aipid, ["pdr2210"])

    def test_get_access_config(self):
        args = self.cmd.parser.parse_args("-q prepupd pdr2222".split())
        cfg = prepupd.get_access_config(args, {})
        self.assertNotIn('headbag_cache', cfg)
        self.assertNotIn('distrib_service', cfg)
        self.assertNotIn('metadata_service', cfg)

        argline = "-q -w "+self.workdir+" prepupd pdr2210 -C headbags -u https://data.nist.gov/"
        args = self.cmd.parser.parse_args(argline.split())
        cfg = prepupd.get_access_config(args, {'working_dir': args.workdir})
        self.assertEqual(cfg['headbag_cache'], os.path.join(self.workdir,"headbags"))
        self.assertTrue(os.path.isdir(cfg['headbag_cache']))
        self.assertEqual(cfg['distrib_service']['service_endpoint'], "https://data.nist.gov/od/ds/")
        self.assertEqual(cfg['metadata_service']['service_endpoint'], "https://data.nist.gov/rmm/")
            

    def test_execute(self):
        argline = "-q -w "+self.workdir+" prepupd pdr2210"
        cfg = deepcopy(self.config)
        self.cmd.execute(argline.split(), cfg)

        self.assertTrue(os.path.isfile(os.path.join(self.workdir, "pdr.log")))
        self.assertTrue(os.path.isdir(os.path.join(self.workdir, "pdr2210")))
        self.assertTrue(os.path.isdir(os.path.join(self.workdir, "pdr2210", "metadata")))
        self.assertTrue(os.path.isdir(os.path.join(self.workdir, "pdr2210", "multibag")))
        self.assertTrue(os.path.exists(os.path.join(self.workdir, "pdr2210", "data")))
        self.assertEqual(len([f for f in os.listdir(os.path.join(self.workdir, "pdr2210", "data"))
                                if not f.startswith('.')]), 0)

    def test_execute_notpub(self):
        argline = "-q -w "+self.workdir+" prepupd pdr8888"
        cfg = deepcopy(self.config)
        try: 
            self.cmd.execute(argline.split(), cfg)
            self.fail("failed to raise command failure")
        except cli.PDRCommandFailure as ex:
            self.assertEqual(ex.stat, 13)



if __name__ == '__main__':
    test.main()

