# These unit tests test the nistoar.pdr.publish.mdserv.serv module, specifically
# the support for accessing metadata that represent an update to a previously
# published dataset (via use of the UpdatePrepService class).  Because these
# tests require simulated RMM and distribution services to be running, they
# have been seperated out from the main unit test module, test_serv.py.
# 
import os, sys, pdb, shutil, logging, json, time
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit.bag import NISTBag
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.preserv import AIPValidationError

# datadir = nistoar/preserv/data
testdir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(testdir), 'data')
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
    shutil.copytree(distarchdir, archdir)

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


class TestPreservationUpdateBagger(test.TestCase):
    
    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("bagger")
        self.mddir = os.path.join(self.workdir, "mddir")
        os.mkdir(self.mddir)
        self.pubcache = self.tf.mkdir("headcache")

        # TODO: copy input data to writable location
        testsip = os.path.join(self.testsip, "review")
        self.revdir = os.path.join(self.workdir, "review")
        shutil.copytree(testsip, self.revdir)
        config = {
            'relative_to_indir': True,
            'bag_builder': {
                'copy_on_link_failure': False,
                'init_bag_info': {
                    'Source-Organization':
                        "National Institute of Standards and Technology",
                    'Contact-Email': ["datasupport@nist.gov"],
                    'Organization-Address': [
                        "100 Bureau Dr., Gaithersburg, MD 20899"],
                    'NIST-BagIt-Version': "0.4",
                    'Multibag-Version': "0.4"
                }
            },
            'headbag_cache':   self.pubcache,
            'distrib_service': {
                'service_endpoint': "http://localhost:9091/"
            },
            'metadata_service': {
                'service_endpoint': "http://localhost:9092/"
            }
        }
        
        self.bagr = midas.PreservationBagger(self.midasid, '_preserv',
                                             self.revdir, self.mddir, config)
        self.sipdir = os.path.join(self.revdir, "1491")
        self.bagparent = os.path.join(self.sipdir, "_preserv")

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.indir, self.sipdir)
        self.assertEqual(self.bagr.mddir, self.mddir)
        self.assertEqual(self.bagr.bagparent, self.bagparent)
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertTrue(os.path.exists(self.bagparent))

        bagdir = os.path.join(self.bagparent, self.midasid+".1_0.mbag0_4-0")
        self.assertEqual(self.bagr.bagdir, bagdir)

        self.assertIsNotNone(self.bagr.prepsvc)

    def test_ensure_metadata_preparation(self):
        self.bagr.ensure_metadata_preparation()
        self.assertTrue(os.path.exists(self.bagr.bagdir),
                        "Output bag dir not created")
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir, "data")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "metadata")))
        self.assertTrue(os.path.exists(os.path.join(self.bagr.bagdir,
                                                    "preserv.log")))
        self.assertTrue(os.path.isdir(os.path.join(self.bagr.bagdir,
                                                   "metadata", "trial1.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.bagr.bagdir,
                                      "metadata", "trial1.json", "nerdm.json")))

        # data files do not yet appear in output bag
        self.assertTrue(not os.path.isdir(os.path.join(self.bagr.bagdir,
                                                       "data", "trial1.json")),
                        "Datafiles copied prematurely")
        

    def test_ensure_metadata_preparation_withupdate(self):
        # test resolving an identifier for a dataset being updated (after
        # an initial publication)
        srczip = os.path.join(distarchive, "1491.1_0.mbag0_4-0.zip")
        destzip = os.path.join(distarchive, self.midasid+".1_0.mbag0_4-0.zip")
        cached = os.path.join(self.pubcache, os.path.basename(destzip))

        try:
            shutil.copyfile(srczip, destzip)

            self.bagr.ensure_metadata_preparation()

            bag = NISTBag(self.bagr.bagdir)
            data = bag.nerd_metadata_for('', True)
            self.assertIn("ediid", data)
            self.assertIn("pdr_status", data)  # previous version used!
            self.assertEqual(data["version"], "1.0.0+ (in edit)")

            self.assertTrue(os.path.exists(cached))

            depinfof = os.path.join(bag.dir, "multibag", "deprecated-info.txt")
            self.assertTrue(os.path.exists(depinfof))

        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)
        

    def test_finalize_version(self):
        srczip = os.path.join(distarchive, "1491.1_0.mbag0_4-0.zip")
        destzip = os.path.join(distarchive, self.midasid+".1_0.mbag0_4-0.zip")
        cached = os.path.join(self.pubcache, os.path.basename(destzip))

        try:
            shutil.copyfile(srczip, destzip)

            self.bagr.prepare(nodata=True)

            bag = NISTBag(self.bagr.bagdir)
            mdrec = bag.nerdm_record(True)
            self.assertEqual(mdrec['version'], "1.0.0+ (in edit)")

            self.bagr.finalize_version()
            mdrec = bag.nerdm_record(True)
            self.assertEqual(mdrec['version'], "1.0.1")

            annotf = os.path.join(bag.metadata_dir, "annot.json")
            data = utils.read_nerd(annotf)
            self.assertEqual(data['version'], "1.0.1")

        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)

    def test_make_updated_bag(self):
        srczip = os.path.join(distarchive, "1491.1_0.mbag0_4-0.zip")
        destzip = os.path.join(distarchive, self.midasid+".1_0.mbag0_4-0.zip")
        cached = os.path.join(self.pubcache, os.path.basename(destzip))

        try:
            shutil.copyfile(srczip, destzip)

            try:
                self.bagr.make_bag()
            except AIPValidationError as ex:
                self.fail(ex.description)

            self.assertEqual(self.bagr.bagbldr.bagname,
                             self.midasid+".1_1_0.mbag0_4-1")
            self.assertEqual(os.path.basename(self.bagr.bagdir),
                             self.bagr.bagbldr.bagname)
            self.assertTrue(os.path.isdir(self.bagr.bagdir))
                
            bag = NISTBag(self.bagr.bagdir)
            info = bag.get_baginfo()

            self.assertEqual(info['Multibag-Head-Version'], ["1.1.0"])
            self.assertEqual(info['Multibag-Head-Deprecates'], ["1"])

            self.assertEqual(bag.nerdm_record().get('version'), "1.1.0")

            depinfof = os.path.join(bag.dir, "multibag", "deprecated-info.txt")
            self.assertTrue(not os.path.exists(depinfof))
            
        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)
        

if __name__ == '__main__':
    test.main()
