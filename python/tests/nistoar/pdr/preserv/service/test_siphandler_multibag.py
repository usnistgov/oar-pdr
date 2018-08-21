# These unit tests specifically test the siphandler module's support for
# multibags.  This includes both the splitting of large AIPs and updating
# previously published datasets.  The tests engage simulated distribution 
# and RMM services to detect a previously published dataset. 
#
import os, pdb, sys, logging, yaml, time
import unittest as test
from zipfile import ZipFile

from nistoar.testing import *
from nistoar.pdr.preserv.service import siphandler as sip
from nistoar.pdr.preserv.service import status
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit.bag import NISTBag
from nistoar.pdr.preserv import AIPValidationError

# datadir = nistoar/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
basedir = os.path.dirname(os.path.dirname(os.path.dirname(
                                                 os.path.dirname(pdrmoddir))))
distarchdir = os.path.join(pdrmoddir, "distrib", "data")
descarchdir = os.path.join(pdrmoddir, "describe", "data")


loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
#    logging.basicConfig(filename=os.path.join(tmpdir(),"test_builder.log"),
#                        level=logging.INFO)
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_builder.log"))
    loghdlr.setLevel(logging.INFO)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)
    startServices()

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    stopServices()
    rmtmpdir()

distarchive = os.path.join(tmpdir(), "distarchive")
mdarchive = os.path.join(tmpdir(), "mdarchive")

def startServices():
    tdir = tmpdir()
    archdir = distarchive
    os.mkdir(archdir)   # keep it empty for now

    srvport = 9091
    pidfile = os.path.join(tdir,"simdistrib"+str(srvport)+".pid")
    wpy = "python/tests/nistoar/pdr/distrib/sim_distrib_srv.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simdistrib.log"), srvport,
                     os.path.join(basedir, wpy), archdir, pidfile)
    os.system(cmd)

    archdir = mdarchive
    shutil.copytree(descarchdir, archdir)

    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    wpy = "python/tests/nistoar/pdr/describe/sim_describe_svc.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simrmm.log"), srvport,
                     os.path.join(basedir, wpy), archdir, pidfile)
    os.system(cmd)

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

def unzip(zipfile):
    zipdir = os.path.dirname(zipfile)
    zip = ZipFile(zipfile)
    zip.extractall(zipdir)
    

class TestMultibagSIPHandler(test.TestCase):

    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.troot = self.tf.mkdir("siphandler")
        self.pubcache = self.tf.mkdir("headcache")
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

        with open(os.path.join(datadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
        baggercfg.update({
            'headbag_cache':   self.pubcache,
            'distrib_service': {
                'service_endpoint': "http://localhost:9091/"
            },
            'metadata_service': {
                'service_endpoint': "http://localhost:9092/"
            }
        })            
            
        self.config = {
            "working_dir": self.workdir,
            "store_dir": self.store,
            "staging_dir": self.stagedir,
            "review_dir":  self.revdir,
            "mdbag_dir":   self.mdserv,
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
        
    def tearDown(self):
        self.sip = None
        self.tf.clean()

    def test_singlebag(self):
        # test creation of a small single bag

        shutil.copytree(self.sipdata, os.path.join(self.revdir, "1491"))
        self.sip = sip.MIDASSIPHandler(self.midasid, self.config)

        self.assertEqual(self.sip.state, status.FORGOTTEN)
        self.sip.bagit()
        self.assertTrue(os.path.exists(os.path.join(self.store, 
                                          self.midasid+".1_0_0.mbag0_4-0.zip")))
        self.assertTrue(not os.path.exists(os.path.join(self.store, 
                                          self.midasid+".1_0_0.mbag0_4-1.zip")))

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
        


    def test_small_revision(self):
        # test creating small update to an existing dataset
        shutil.copytree(self.sipdata, os.path.join(self.revdir, "1491"))
        shutil.rmtree(os.path.join(self.revdir, "1491", "trial3"))
        self.sip = sip.MIDASSIPHandler(self.midasid, self.config)

        srczip = os.path.join(distarchdir, "1491.1_0.mbag0_4-0.zip")
        destzip = os.path.join(distarchive, self.midasid+".1_0.mbag0_4-0.zip")
        cached = os.path.join(self.pubcache, os.path.basename(destzip))

        try:
            shutil.copyfile(srczip, destzip)

            try:
                self.sip.bagit()
            except AIPValidationError as ex:
                self.fail(ex.description)

            self.assertTrue(os.path.exists(os.path.join(self.store, 
                                           self.midasid+".1_1_0.mbag0_4-1.zip")))
            self.assertTrue(not os.path.exists(os.path.join(self.store, 
                                          self.midasid+".1_1_0.mbag0_4-2.zip")))

            csumfile = os.path.join(self.store,
                                    self.midasid+".1_1_0.mbag0_4-1.zip.sha256")
            self.assertTrue(os.path.exists(csumfile))
            with open(csumfile) as fd:
                csum = fd.read().strip()
            
            self.assertEqual(self.sip.state, status.SUCCESSFUL)
            self.assertIn('bagfiles', self.sip.status)
            self.assertEqual(len(self.sip.status['bagfiles']), 1)
            self.assertEqual(self.sip.status['bagfiles'][0]['name'], 
                                             self.midasid+".1_1_0.mbag0_4-1.zip")
            self.assertEqual(self.sip.status['bagfiles'][0]['sha256'], csum)

            # check for checksum files in review dir
            cf = os.path.join(self.revdir, "1491/_preserv",
                              self.midasid+"_1.sha256")
            self.assertTrue(os.path.exists(cf), "Does not exist: "+cf)

            # check contents of revision
            bagdir = os.path.join(self.store, self.midasid+".1_1_0.mbag0_4-1")
            unzip(bagdir+".zip")
            datadir = os.path.join(bagdir, "data")
            self.assertTrue(os.path.isdir(datadir))
            self.assertGreater(len(os.listdir(datadir)), 1)
            datadir = os.path.join(bagdir, "metadata")
            self.assertTrue(os.path.isdir(datadir))
            self.assertTrue(os.path.isfile(os.path.join(datadir,"pod.json")))
            self.assertTrue(os.path.isfile(os.path.join(datadir,"nerdm.json")))
            self.assertGreater(len(os.listdir(datadir)), 2)

            with open(os.path.join(bagdir,"multibag","member-bags.tsv")) as fd:
                members = [l.strip().split('\t')[0] for l in fd.readlines()]
            self.assertEqual(members, [self.midasid+".1_0.mbag0_4-0",
                                       self.midasid+".1_1_0.mbag0_4-1" ])
            
        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)
        


    def test_metadata_revision(self):
        # test creating small update involving only metadata
        indir = os.path.join(self.revdir, "1491")
        os.mkdir(indir)
        shutil.copy(os.path.join(self.sipdata, "_pod.json"), indir)

        self.sip = sip.MIDASSIPHandler(self.midasid, self.config)

        srczip = os.path.join(distarchdir, "1491.1_0.mbag0_4-0.zip")
        destzip = os.path.join(distarchive, self.midasid+".1_0.mbag0_4-0.zip")
        cached = os.path.join(self.pubcache, os.path.basename(destzip))

        try:
            shutil.copyfile(srczip, destzip)

            try:
                self.sip.bagit()
            except AIPValidationError as ex:
                self.fail(ex.description)

            self.assertTrue(os.path.exists(os.path.join(self.store, 
                                           self.midasid+".1_0_1.mbag0_4-1.zip")))
            self.assertTrue(not os.path.exists(os.path.join(self.store, 
                                          self.midasid+".1_0_1.mbag0_4-2.zip")))

            csumfile = os.path.join(self.store,
                                    self.midasid+".1_0_1.mbag0_4-1.zip.sha256")
            self.assertTrue(os.path.exists(csumfile))
            with open(csumfile) as fd:
                csum = fd.read().strip()
            
            self.assertEqual(self.sip.state, status.SUCCESSFUL)
            self.assertIn('bagfiles', self.sip.status)
            self.assertEqual(len(self.sip.status['bagfiles']), 1)
            self.assertEqual(self.sip.status['bagfiles'][0]['name'], 
                                             self.midasid+".1_0_1.mbag0_4-1.zip")
            self.assertEqual(self.sip.status['bagfiles'][0]['sha256'], csum)

            # check for checksum files in review dir
            cf = os.path.join(self.revdir, "1491/_preserv",
                              self.midasid+"_1.sha256")
            self.assertTrue(os.path.exists(cf), "Does not exist: "+cf)

            # check contents of revision
            bagdir = os.path.join(self.store, self.midasid+".1_0_1.mbag0_4-1")
            unzip(bagdir+".zip")
            datadir = os.path.join(bagdir, "data")
            self.assertTrue(os.path.isdir(datadir))
            self.assertEqual(len(os.listdir(datadir)), 0)
            datadir = os.path.join(bagdir, "metadata")
            self.assertTrue(os.path.isdir(datadir))
            self.assertTrue(os.path.isfile(os.path.join(datadir,"pod.json")))
            self.assertTrue(os.path.isfile(os.path.join(datadir,"nerdm.json")))
            self.assertGreater(len(os.listdir(datadir)), 2)
            
            
        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)
        


    def no_test_large_multibag(self):
        # test creating an initial large submission
        pass

    def no_test_large_revision(self):
        # test creating a large revision which itself requires splitting
        pass



        

if __name__ == '__main__':
    test.main()
