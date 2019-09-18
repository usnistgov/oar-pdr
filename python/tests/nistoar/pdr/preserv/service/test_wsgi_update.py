# These unit tests specifically test the wsgi module's support for
# updates (via PATCH).  Mock services for the RMM and distribution service
# are spun up to test for a valid update state.
#
import os, pdb, sys, logging, yaml, time
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.service import wsgi
from nistoar.pdr.preserv.service import status
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.service.siphandler import SIPHandler, MIDASSIPHandler
from nistoar.pdr.exceptions import PDRException, StateException

# datadir = nistoar/pdr/preserv/data
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

class TestApp(test.TestCase):

    sipdata = os.path.join(datadir, "midassip", "review", "1491")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def setUp(self):
        self.tf = Tempfiles()
        self.troot = self.tf.mkdir("siphandler")
        self.pubcache = self.tf.mkdir("headcache")
        self.revdir = os.path.join(self.troot, "review")
        os.mkdir(self.revdir)
        self.workdir = os.path.join(self.troot, "working")
        os.mkdir(self.workdir)
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
            "id_registry_dir": self.workdir,
            'repo_access': {
                'headbag_cache':   self.pubcache,
                'distrib_service': {
                    'service_endpoint': "http://localhost:9091/"
                },
                'metadata_service': {
                    'service_endpoint': "http://localhost:9092/"
                }
            },
            "sip_type": {
                "midas": {
                    "common": {
                        "review_dir": self.revdir,
                        "id_minter": { "shoulder_for_edi": "edi0" },
                    },
                    "mdserv": {
                        "working_dir": self.mdserv
                    },
                    "preserv": {
                        "bagparent_dir": "_preserv",
                        "staging_dir": self.stagedir,
                        "bagger": baggercfg,
                        "status_manager": { "cachedir": self.statusdir },
                    }
                }
            }
        }

        try:
            self.svc = wsgi.app(self.config)
        except Exception, e:
            self.tearDown()
            raise

        self.resp = []

    def tearDown(self):
        self.svc = None
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.svc.preserv)
        self.assertTrue(os.path.exists(self.workdir))
        self.assertTrue(os.path.exists(self.store))

        self.assertEqual(self.svc.preserv.siptypes, ['midas'])
        self.assertIsNotNone(self.svc.preserv._prepsvc)

    def test_conflicted_put(self):
        # put a record in the RMM to signal the AIP's existence
        shutil.copy(os.path.join(datadir, self.midasid+".json"),
                    mdarchive)
        
        req = {
            'PATH_INFO': '/midas/'+self.midasid+'/',
            'REQUEST_METHOD': 'PUT'
        }

        try: 
            body = self.svc(req, self.start)
            self.assertGreater(len(self.resp), 0)
            self.assertIn("409", self.resp[0])
        finally:
            rec = os.path.join(mdarchive, self.midasid+".json")
            if os.path.exists(rec):
                os.remove(rec)

    def test_conflicted_patch(self):
        req = {
            'PATH_INFO': '/midas/'+self.midasid+'/',
            'REQUEST_METHOD': 'PATCH'
        }

        body = self.svc(req, self.start)
        self.assertGreater(len(self.resp), 0)
        self.assertIn("409", self.resp[0])

    def test_good_patch(self):
        # put a record in the RMM to signal the AIP's existence
        shutil.copy(os.path.join(datadir, self.midasid+".json"),
                    mdarchive)
        
        req = {
            'PATH_INFO': '/midas/'+self.midasid+'/',
            'REQUEST_METHOD': 'PATCH'
        }

        try: 
            body = self.svc(req, self.start)
            self.assertGreater(len(self.resp), 0)
            self.assertIn("202", self.resp[0])
        finally:
            rec = os.path.join(mdarchive, self.midasid+".json")
            if os.path.exists(rec):
                os.remove(rec)

        

        
        
        
        

if __name__ == '__main__':
    test.main()

        



            
