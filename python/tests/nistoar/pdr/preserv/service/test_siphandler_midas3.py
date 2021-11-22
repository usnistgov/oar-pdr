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

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
            loghdlr.close()
        loghdlr = None
    rmtmpdir()

class TestMIDAS3SIPHandler(test.TestCase):

    testsip = os.path.join(datadir, "metadatabag")
    revdir = os.path.join(datadir, "midassip", "review")
    # testdata = os.path.join(datadir, "samplembag", "data")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("preserv")
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        self.dataroot = os.path.join(self.workdir, "data")
        os.mkdir(self.dataroot)
        self.datadir = os.path.join(self.dataroot, "1491")
        self.stagedir = os.path.join(self.workdir, "staging")
        self.storedir = os.path.join(self.workdir, "store")
        os.mkdir(self.storedir)
        self.restrictdir = os.path.join(self.workdir, "restricted")
        os.mkdir(self.restrictdir)
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
            'restricted_store_dir': self.restrictdir,
            "status_manager": { "cachedir": self.statusdir },
            'bagger': baggercfg,
            "ingester": {
                "data_dir":  os.path.join(self.workdir, "ingest"),
                "submit": "none"
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

    def test_ctor_asupdate(self):
        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config,
                                        asupdate=True)
        self.assertTrue(self.sip.bagger)
        self.assertEqual(self.sip.bagger.asupdate, True)

        self.assertTrue(isinstance(self.sip.status, dict))
        self.assertEqual(self.sip.state, status.FORGOTTEN)

        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config,
                                        asupdate=False)
        self.assertTrue(self.sip.bagger)
        self.assertEqual(self.sip.bagger.asupdate, False)

        self.assertTrue(isinstance(self.sip.status, dict))
        self.assertEqual(self.sip.state, status.FORGOTTEN)

    def test_set_state(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.sip.set_state(status.SUCCESSFUL, "Yeah!")
        self.assertEqual(self.sip.state, status.SUCCESSFUL)
        self.assertEqual(self.sip._status.message, "Yeah!")

    def test_isready(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertTrue(self.sip.isready())
        self.assertEqual(self.sip.state, status.READY)

    def test_bagit(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 0)
        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))

        csumfile = os.path.join(self.storedir,
                                self.midasid+".1_0_0.mbag0_4-0.zip.sha256")
        self.assertTrue(os.path.exists(csumfile))
        with open(csumfile) as fd:
            csum = fd.read().strip()
        
        self.assertEqual(self.sip.state, status.SUCCESSFUL)
        self.assertIn('bagfiles', self.sip.status)
        self.assertEqual(len(self.sip.status['bagfiles']), 1)
        self.assertEqual(self.sip.status['bagfiles'][0]['name'], 
                                            self.midasid+".1_0_0.mbag0_4-0.zip")
        self.assertEqual(self.sip.status['bagfiles'][0]['sha256'], csum)

        # check for checksum files in review dir
        cf = os.path.join(self.bagparent, self.midasid+"_0.sha256")
        self.assertTrue(os.path.exists(cf), "Does not exist: "+cf)
        cf = os.path.join(self.bagparent, "_preserved")
        self.assertTrue(os.path.exists(cf), "Does not exist: "+cf)

        # head bag still in staging area?
        staged = os.listdir(self.sip.stagedir)
        self.assertEqual(len(staged), 1)
        self.assertTrue(os.path.basename(staged[0]).endswith("-0.zip"))

        # we don't have a nerdm staging area, so we shouldn't a cached nerdm file
        # under staging area
        staged = os.path.join(self.stagedir,'_nerd',self.midasid+".json")
        self.assertFalse(os.path.exists(staged))

        # has the metadata bag NOT been cleaned up?  (Clean up happens via pubserver
        # service call which this test is not configured for)
        mdbagdir = os.path.join(self.sip.mdbagdir, self.midasid)
        self.assertTrue( os.path.exists(mdbagdir),
                         "Failed to clean up metadata bag directory: "+mdbagdir)

        # has unserialized bags been cleaned up?
        bb = self.midasid+".1_0_0.mbag0_4-"
        bfs = [f for f in os.listdir(self.bagparent) if f.startswith(bb)]
        self.assertEqual(len(bfs), 0)

    def test_bagit_withnerdstaging(self):
        mdcache = os.path.join(self.stagedir, "_nerd")
        if not os.path.exists(mdcache):
            os.mkdir(mdcache)

        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 1)
        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))

        # do we have a cached nerdm file under staging area?
        staged = os.path.join(self.stagedir,'_nerd',self.midasid+".json")
        self.assertTrue(os.path.exists(staged))

    def test_bagit_nerdstagingfail(self):
        mdcache = os.path.join(self.stagedir, "_nerd")
        if not os.path.exists(mdcache):
            os.mkdir(mdcache)
        staged = os.path.join(self.stagedir,'_nerd',self.midasid+".json")
        with open(staged, 'w') as fd:
            pass

        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 1)
        try:
            os.chmod(staged, stat.S_IREAD)
            os.chmod(mdcache, stat.S_IREAD|stat.S_IXUSR)
            with self.assertRaises(OSError):
                self.sip.bagit()
        finally:
            os.chmod(mdcache, stat.S_IREAD|stat.S_IWRITE|stat.S_IXUSR)
            os.chmod(staged, stat.S_IREAD|stat.S_IWRITE|stat.S_IROTH|stat.S_IWOTH)
                     

    def test_bagit_nerdstagingclean(self):
        mdcache = os.path.join(self.stagedir, "_nerd")
        if not os.path.exists(mdcache):
            os.mkdir(mdcache)
        staged = os.path.join(mdcache, self.midasid+".json")
        with open(staged, 'w') as fd:
            pass
        self.assertTrue(os.path.exists(staged))

        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 1)
        try:
            os.chmod(staged, stat.S_IREAD)
            self.sip.bagit()

            # do we have a cached nerdm file under staging area?
            self.assertFalse(os.path.exists(staged))
        finally:
            if os.path.exists(staged):
                os.chmod(staged,stat.S_IREAD|stat.S_IWRITE|stat.S_IROTH|stat.S_IWOTH)

    def test_bagit_nooverwrite(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 0)
        destfile = os.path.join(self.storedir, self.midasid+".1_0_0.mbag0_4-0.zip")
        self.assertTrue(not os.path.exists(destfile))
        with open(destfile, 'w') as fd:
            fd.write("\n");
        
        try:
            self.sip.bagit()
            self.fail("Failed to catch overwrite error")
        except PreservationException as ex:
            self.assertEqual(len(ex.errors), 1)
            self.assertEqual(ex.errors[0],
                             "[Errno 17] File exists: '{}'".format(destfile))
            
    def test_bagit_allowoverwrite(self):
        self.sip.cfg['allow_bag_overwrite'] = True;
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 0)
        destfile = os.path.join(self.storedir, self.midasid+".1_0_0.mbag0_4-0.zip")
        self.assertTrue(not os.path.exists(destfile))
        with open(destfile, 'w') as fd:
            fd.write("\n");
        self.assertEqual(os.stat(destfile).st_size, 1)
        
        self.sip.bagit()
        self.assertGreater(os.stat(destfile).st_size, 1)
            
        

    def test_bagit_wdeactiv8(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 0)

        bldr = BagBuilder(os.path.dirname(self.sipdir), os.path.basename(self.sipdir))
        bldr.update_metadata_for("", {"status": "removed"})
        bldr.disconnect_logfile()

        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.removed")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256.removed")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256.sha256.removed")))
        

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

        # copy input bag to writable location
        if not os.path.exists(self.sipdir):
            shutil.copytree(self.testsip, self.sipdir)

        bldr = BagBuilder(os.path.dirname(self.sipdir), os.path.basename(self.sipdir))
        bldr.update_metadata_for("", {"version": "1.0.1", "status": "removed"})
        bldr.disconnect_logfile()
        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
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

        
    def test_bagit_wdeactiv8_3(self):
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

        # copy input bag to writable location
        if not os.path.exists(self.sipdir):
            shutil.copytree(self.testsip, self.sipdir)

        bldr = BagBuilder(os.path.dirname(self.sipdir), os.path.basename(self.sipdir))
        bldr.update_metadata_for("", {"version": "1.1.0", "status": "removed"})
        bldr.disconnect_logfile()
        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.removed")))
        self.assertTrue(not os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip.sha256.removed")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_1_0.mbag0_4-0.zip")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_1_0.mbag0_4-0.zip.sha256")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_1_0.mbag0_4-0.zip.removed")))
        self.assertTrue(os.path.exists(os.path.join(self.storedir, 
                                          self.midasid+".1_1_0.mbag0_4-0.zip.sha256.removed")))

        

    def test_is_preserved(self):
        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertFalse(self.sip._is_preserved())
        self.sip.bagit()
        self.assertTrue(self.sip._is_preserved())

        # if there is no longer a cached status file, ensure that we notice
        # when there is a bag in the store dir
        os.remove(os.path.join(self.statusdir, self.midasid+'.json'))
        self.sip = sip.MIDASSIPHandler(self.midasid, self.config)
        stat = self.sip.status
        self.sip._is_preserved()
        self.assertEqual(stat['state'], status.SUCCESSFUL)
        self.assertIn('orgotten', stat['message'])






if __name__ == '__main__':
    test.main()
