import os, sys, pdb, shutil, logging, json, time, re
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr import utils, ARK_NAAN
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit.bag import NISTBag
from nistoar.pdr.publish.midas3 import service as mdsvc
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.preserv import AIPValidationError

# datadir = nistoar/pdr/preserv/data
testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, 'preserv', 'data')
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
basedir = os.path.dirname(os.path.dirname(os.path.dirname(
                                                 os.path.dirname(pdrmoddir))))
distarchdir = os.path.join(pdrmoddir, "distrib", "data")
descarchdir = os.path.join(pdrmoddir, "describe", "data")

loghdlr = None
rootlog = None
def setUpModule():
    global loghdlr
    global rootlog
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
            rootlog.removeHandler(loghdlr)
            loghdlr.flush()
            loghdlr.close()
        loghdlr = None
    stopServices()
    rmtmpdir()

distarchive = os.path.join(tmpdir(), "distarchive")
mdarchive = os.path.join(tmpdir(), "mdarchive")

def startServices():
    tdir = tmpdir()
    archdir = distarchive
    shutil.copytree(distarchdir, archdir)
    shutil.copyfile(os.path.join(archdir,"1491.1_0.mbag0_4-0.zip"),
                    os.path.join(archdir,"3A1EE2F169DD3B8CE0531A570681DB5D1491.1_0.mbag0_4-0.zip"))

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
    nerd = utils.read_nerd(os.path.join(archdir, "pdr02d4t.json"))
    nerd['ediid'] = "3A1EE2F169DD3B8CE0531A570681DB5D1491"
    utils.write_json(nerd, os.path.join(archdir, "3A1EE2F169DD3B8CE0531A570681DB5D1491.json"))

    srvport = 9092
    pidfile = os.path.join(tdir,"simrmm"+str(srvport)+".pid")
    wpy = "python/tests/nistoar/pdr/describe/sim_describe_svc.py"
    assert os.path.exists(wpy)
    cmd = "uwsgi --daemonize {0} --plugin python --http-socket :{1} " \
          "--wsgi-file {2} --set-ph archive_dir={3} --pidfile {4}"
    cmd = cmd.format(os.path.join(tdir,"simrmm.log"), srvport,
                     os.path.join(basedir, wpy), archdir, pidfile)
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





class TestMIDAS3PublishingServiceOnUpdate(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    prevmidasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    updmidasid = "ark:/"+ARK_NAAN+"/mds8-8888"

    defcfg = {
        'customization_service': {
            'auth_key': 'SECRET',
            'service_endpoint': "http:notused.net/",
            'merge_convention': 'midas1'
        },
        'update': {
            'updatable_properties': [ "title", "authors", "_editStatus" ]
        },
        'metadata_bags_dir': "mddir"
    }

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("pubserv")
        self.mddir = os.path.join(self.workdir, "mddir")
        os.mkdir(self.mddir)
        self.pubcache = self.tf.mkdir("headcache")

        testsip = os.path.join(self.testsip, "review")
        self.revdir = os.path.join(self.workdir, "review")
        self.upldir = os.path.join(self.workdir, "upload")
        self.sipdir = os.path.join(self.revdir, "8888")
        shutil.copytree(testsip, self.revdir)
        now = time.time()
        for base, dirs, files in os.walk(self.revdir):
            for f in files+dirs:
                os.utime(os.path.join(base,f), (now, now))
        shutil.copytree(os.path.join(self.revdir, "1491"), self.sipdir)
        os.mkdir(self.upldir)
        
        self.nrddir = os.path.join(self.workdir, "nrdserv")
        self.bagconfig = {
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
            'repo_access': {
                'headbag_cache':   self.pubcache,
                'distrib_service': {
                    'service_endpoint': "http://localhost:9091/"
                },
                'metadata_service': {
                    'service_endpoint': "http://localhost:9092/"
                }
            },
            'store_dir': distarchdir
        }
        self.config = { "bagger": self.bagconfig }
        self.config.update(deepcopy(self.defcfg))

        self.svc = mdsvc.MIDAS3PublishingService(self.defcfg, self.workdir,
                                                 self.revdir, self.upldir)
        self.updbagdir = os.path.join(self.mddir, "mds8-8888")
        self.replbagdir = os.path.join(self.mddir, self.prevmidasid)

    def tearDown(self):
        if self.svc:
            self.svc._drop_all_workers(300)
        self.tf.clean()

    def test_copy_oldbag_when_done(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)

        self.assertTrue(not os.path.exists(self.updbagdir))
        self.assertTrue(not os.path.exists(self.replbagdir))

        # submit pod under old EDI-ID
        bagr = self.svc.update_ds_with_pod(pod, False)
        
        self.assertTrue(os.path.exists(self.replbagdir))
        self.assertTrue(not os.path.exists(self.updbagdir))
        data = utils.read_json(os.path.join(self.nrddir, self.prevmidasid+".json"))
        self.assertEqual(data.get('ediid'), self.prevmidasid)
        self.assertEqual(data.get('version'), "1.0.0")

        oldwrkr = self.svc._get_bagging_worker(self.prevmidasid)
        newwrkr = self.svc._get_bagging_worker(self.updmidasid)
        self.svc._copy_oldbag_when_done(oldwrkr, newwrkr)

        self.assertTrue(os.path.exists(self.replbagdir))
        self.assertTrue(os.path.exists(self.updbagdir))
        data = newwrkr.bagger.sip.nerd
        self.assertEqual(data.get('ediid'), self.updmidasid)
        self.assertEqual(data.get('version'), "1.0.0+ (in edit)")

        
    def test_update_ds_with_pod_onupdate(self):
        podf = os.path.join(self.revdir, "1491", "_pod.json")
        pod = utils.read_json(podf)

        self.assertTrue(not os.path.exists(self.updbagdir))
        self.assertTrue(not os.path.exists(self.replbagdir))

        # submit pod under old EDI-ID
        bagr = self.svc.update_ds_with_pod(pod, False)
        
        self.assertTrue(os.path.exists(self.replbagdir))
        self.assertTrue(not os.path.exists(self.updbagdir))
        data = utils.read_json(os.path.join(self.nrddir, self.prevmidasid+".json"))
        self.assertEqual(data.get('ediid'), self.prevmidasid)
        data = utils.read_json(os.path.join(self.mddir, self.prevmidasid, "metadata", "nerdm.json"))
        self.assertEqual(data.get('ediid'), self.prevmidasid)
        self.assertEqual(data.get('version'), "1.0.0")
        # data = {'version': "1.0.1+ (in edit)"}
        # utils.write_json(data, os.path.join(self.mddir, self.prevmidasid, "metadata", "annot.json"))
        
        # submit under new EDI-ID; POD record will have new MIDAS ID, new DOI, and new download URLs
        pod['replaces'] = pod['identifier']
        pod['identifier'] = self.updmidasid
        for dist in pod['distribution']:
            if 'downloadURL' in dist and '/od/ds/' in dist['downloadURL']:
                dist['downloadURL'] = re.sub(self.prevmidasid, self.updmidasid, dist['downloadURL'])
            elif 'accessURL' in dist and 'doi.org' in dist['accessURL']:
                dist['accessURL'] = re.sub(r'/[^/]+$', '/mds8-8888', dist['accessURL'])
                        
        bagr = self.svc.update_ds_with_pod(pod, False)
        self.assertTrue(os.path.exists(self.replbagdir))
        self.assertTrue(os.path.exists(self.updbagdir))
        data = utils.read_json(os.path.join(self.nrddir, "mds8-8888.json"))
        self.assertEqual(data.get('ediid'), self.updmidasid)
        # self.assertEqual(data.get('version'), "1.0.1+ (in edit)")
        self.assertEqual(data.get('version'), "1.0.0+ (in edit)")
        
        self.assertTrue(os.path.exists(os.path.join(self.updbagdir,"metadata","__bagger-midas3.json")))
        bmd = utils.read_json(os.path.join(self.updbagdir,"metadata","__bagger-midas3.json"))
        self.assertEqual(bmd.get("replacedEDI"), self.prevmidasid)
        



if __name__ == '__main__':
    test.main()

