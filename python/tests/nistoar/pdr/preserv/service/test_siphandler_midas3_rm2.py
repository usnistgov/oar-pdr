import os, pdb, sys, logging, yaml, stat
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv import PreservationException
from nistoar.pdr.preserv.service import siphandler as sip
from nistoar.pdr.preserv.service import status
from nistoar.pdr.preserv.bagger import midas3 as midas
from nistoar.pdr.preserv.bagit import BagBuilder

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )
pdrmoddir = os.path.dirname(os.path.dirname(datadir))
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(pdrmoddir))))

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_siphandler.log"))
    loghdlr.setLevel(logging.DEBUG)
    rootlog.addHandler(loghdlr)
    startService()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    stopService()
    rmtmpdir()

distarchive = os.path.join(tmpdir(), "distarchive")

def startService():
    tdir = tmpdir()
    archdir = distarchive
    os.mkdir(archdir)

    srvport = 9091
    pidfile = os.path.join(tdir,"simdistrib"+str(srvport)+".pid")
    wpy = "python/tests/nistoar/pdr/distrib/sim_distrib_srv.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simdistrib.log"), srvport,
                     os.path.join(basedir, wpy), archdir, pidfile)
    os.system(cmd)

def stopService():
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


class TestMIDAS3SIPHandler(test.TestCase):

    testsip = os.path.join(datadir, "metadatabag")
    revdir = os.path.join(datadir, "midassip", "review")
    # testdata = os.path.join(datadir, "samplembag", "data")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        if not os.path.exists(distarchive):
            os.mkdir(distarchive)

        self.workdir = self.tf.mkdir("preserv")
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.dataroot = os.path.join(self.workdir, "data")
        os.mkdir(self.dataroot)
        self.datadir = os.path.join(self.dataroot, "1491")
        self.stagedir = os.path.join(self.workdir, "staging")
        self.storedir = os.path.join(self.workdir, "store")
        os.mkdir(self.storedir)
        self.statusdir = os.path.join(self.workdir, "status")
        os.mkdir(self.statusdir)
        self.bagparent = os.path.join(self.datadir, "_preserv")
        self.sipdir = os.path.join(self.mdbags, self.midasid)

        with open(os.path.join(datadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
            
        # set the config we'll use
        self.config = {
            'working_dir': self.workdir,
            'review_dir': self.dataroot,
            "staging_dir": self.stagedir,
            'store_dir': self.storedir,
            "status_manager": { "cachedir": self.statusdir },
            'bagger': baggercfg,
            "ingester": {
                "data_dir":  os.path.join(self.workdir, "ingest"),
                "submit": "none"
            },
            "repo_access": {
                "distrib_service": {
                    "service_endpoint": "http://localhost:9091"
                }
            },
            "multibag": {
                "max_headbag_size": 2000000,
#                "max_headbag_size": 100,
                "max_bag_size": 200000000
            }
        }

        # copy the data files first
        shutil.copytree(os.path.join(self.revdir, "1491"), self.datadir)
        # os.mkdir(self.bagparent)

        # copy input bag to writable location
        shutil.copytree(self.testsip, self.sipdir)

        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, self.datadir)
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.done()

        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

    def tearDown(self):
        self.sip = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.sip.bagger)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.stagedir))
        self.assertTrue(os.path.exists(self.mdbags))

        self.assertTrue(isinstance(self.sip.status, dict))
        self.assertEqual(self.sip.state, status.FORGOTTEN)

        self.assertIsNone(self.sip.bagger.asupdate)

    def test_bagit_wdeactiv8_2(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 0)

        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.removed")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256.removed")))

        # move bag files to distrib server
        os.rename(os.path.join(self.storedir, self.midasid+".1_0_0.mbag0_4-0.zip"),
                  os.path.join(distarchive, self.midasid+".1_0_0.mbag0_4-0.zip"))
        os.rename(os.path.join(self.storedir, self.midasid+".1_0_0.mbag0_4-0.zip.sha256"),
                  os.path.join(distarchive, self.midasid+".1_0_0.mbag0_4-0.zip.sha256"))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))

        # copy input bag to writable location
        if not os.path.exists(self.sipdir):
            shutil.copytree(self.testsip, self.sipdir)

        bldr = BagBuilder(os.path.dirname(self.sipdir), os.path.basename(self.sipdir))
        bldr.update_metadata_for("", {"version": "1.0.1", "status": "removed"})
        bldr.disconnect_logfile()
        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

        self.sip.bagit()
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                                    self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                                        self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.removed")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256.removed")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_1.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_1.mbag0_4-0.zip.sha256")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_1.mbag0_4-0.zip.removed")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_1.mbag0_4-0.zip.sha256.removed")))

        






if __name__ == '__main__':
    test.main()
