import os, pdb, sys, logging, yaml, stat
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv import PreservationException
from nistoar.pdr.preserv.service import siphandler as sip
from nistoar.pdr.preserv.service import status

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
        loghdlr = None
    rmtmpdir()

class TestMIDASSIPHandler(test.TestCase):

    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.troot = self.tf.mkdir("siphandler")
        self.revdir = os.path.join(self.troot, "review")
        os.mkdir(self.revdir)
        self.workdir = os.path.join(self.troot, "working")
        # os.mkdir(self.workdir)
        self.stagedir = os.path.join(self.troot, "staging")
        # os.mkdir(self.stagedir)
        self.mdserv = os.path.join(self.troot, "mdserv")
        os.mkdir(self.mdserv)
        self.store = os.path.join(self.troot, "store")
        os.mkdir(self.store)
        self.statusdir = os.path.join(self.troot, "status")
        os.mkdir(self.statusdir)

        shutil.copytree(self.sipdata, os.path.join(self.revdir, "1491"))

        with open(os.path.join(datadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
            
        self.config = {
            "working_dir": self.workdir,
            "store_dir": self.store,
            "staging_dir": self.stagedir,
            "review_dir":  self.revdir,
            "metadata_bags_dir":   self.mdserv,
            "status_manager": { "cachedir": self.statusdir },
            "logdir": self.workdir,
            "bagparent_dir": "_preserv",
            "bagger": baggercfg,
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

        self.sip = sip.MIDASSIPHandler(self.midasid, self.config)

    def tearDown(self):
        self.sip = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.sip.bagger)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.stagedir))
        self.assertTrue(os.path.exists(self.mdserv))

        self.assertTrue(isinstance(self.sip.status, dict))
        self.assertEqual(self.sip.state, status.FORGOTTEN)

        self.assertIsNone(self.sip.bagger.asupdate)

    def test_ctor_asupdate(self):
        self.sip = sip.MIDASSIPHandler(self.midasid, self.config,
                                       asupdate=True)
        self.assertTrue(self.sip.bagger)
        self.assertEqual(self.sip.bagger.asupdate, True)

        self.assertTrue(isinstance(self.sip.status, dict))
        self.assertEqual(self.sip.state, status.FORGOTTEN)

        self.sip = sip.MIDASSIPHandler(self.midasid, self.config,
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
        self.assertTrue(os.path.exists(os.path.join(self.store, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))

        csumfile = os.path.join(self.store,
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
        cf = os.path.join(self.revdir, "1491/_preserv", self.midasid+"_0.sha256")
        self.assertTrue(os.path.exists(cf), "Does not exist: "+cf)

        # head bag still in staging area?
        staged = os.listdir(self.sip.stagedir)
        self.assertEqual(len(staged), 1)
        self.assertTrue(os.path.basename(staged[0]).endswith("-0.zip"))

        # we don't have a nerdm staging area, so we shouldn't a cached nerdm file
        # under staging area
        staged = os.path.join(self.stagedir,'_nerd',self.midasid+".json")
        self.assertFalse(os.path.exists(staged))

        # has the metadata bag been cleaned up?
        mdbagdir = os.path.join(self.sip.mdbagdir, self.midasid)
        self.assertFalse( os.path.exists(mdbagdir),
                          "Failed to clean up metadata bag directory: "+mdbagdir)

        # has unserialized bags been cleaned up?
        pd = os.path.join(self.revdir, "1491/_preserv")
        bb = self.midasid+".1_0_0.mbag0_4-"
        bfs = [f for f in os.listdir(pd) if f.startswith(bb)]
        self.assertEqual(len(bfs), 0)

    def test_bagit_withnerdstaging(self):
        mdcache = os.path.join(self.stagedir, "_nerd")
        if not os.path.exists(mdcache):
            os.mkdir(mdcache)

        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.assertEqual(len(os.listdir(self.sip.stagedir)), 1)
        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.store, 
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
        destfile = os.path.join(self.store, self.midasid+".1_0_0.mbag0_4-0.zip")
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
        destfile = os.path.join(self.store, self.midasid+".1_0_0.mbag0_4-0.zip")
        self.assertTrue(not os.path.exists(destfile))
        with open(destfile, 'w') as fd:
            fd.write("\n");
        self.assertEqual(os.stat(destfile).st_size, 1)
        
        self.sip.bagit()
        self.assertGreater(os.stat(destfile).st_size, 1)
            
        
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
