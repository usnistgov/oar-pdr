# These unit tests test the nistoar.pdr.publish.mdserv.serv module, specifically
# the support for accessing metadata that represent an update to a previously
# published dataset (via use of the UpdatePrepService class).  Because these
# tests require simulated RMM and distribution services to be running, they
# have been seperated out from the main unit test module, test_serv.py.
#
import os, sys, pdb, shutil, logging, json, time, signal
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict
from copy import deepcopy
import ejsonschema as ejs

from nistoar.testing import *
from nistoar.pdr import def_jq_libdir
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.publish.mdserv.serv as serv
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.utils import read_nerd, write_json

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')
# datadir = nistoar/preserv/tests/data
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")
jqlibdir = def_jq_libdir
schemadir = os.path.join(os.path.dirname(jqlibdir), "model")
if not os.path.exists(schemadir) and os.environ.get('OAR_HOME'):
    schemadir = os.path.join(os.environ['OAR_HOME'], "etc", "schemas")
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

def to_dict(odict):
    out = dict(odict)
    for prop in out:
        if isinstance(out[prop], OrderedDict):
            out[prop] = to_dict(out[prop])
        if isinstance(out[prop], (list, tuple)):
            for i in range(len(out[prop])):
                if isinstance(out[prop][i], OrderedDict):
                    out[prop][i] = to_dict(out[prop][i])
    return out


class TestPrePubMetadataService(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("mdserv")
        self.bagparent = self.workdir
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.pubcache = self.tf.mkdir("headcache")
        
        self.config = {
            'working_dir':     self.workdir,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'store_dir':       distarchdir,
            'id_registry_dir': self.workdir,
            'repo_access': {
                'headbag_cache':   self.pubcache,
                'distrib_service': {
                    'service_endpoint': "http://localhost:9091/"
                },
                'metadata_service': {
                    'service_endpoint': "http://localhost:9092/"
                },
            },
            'async_file_examine': False
        }
        self.srv = serv.PrePubMetadataService(self.config)
        self.bagdir = os.path.join(self.bagparent, self.midasid)

    def tearDown(self):
        self.srv = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEquals(self.srv.workdir, self.workdir)
        self.assertEquals(self.srv.uploaddir, self.upldir)
        self.assertEquals(self.srv.reviewdir, self.revdir)
        self.assertEquals(os.path.dirname(self.srv._minter.registry.store),
                          self.workdir)

        self.assertIsNotNone(self.srv.prepsvc)
        
    def test_resolve_id(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        mdata = self.srv.resolve_id(self.midasid)
        self.assertIn("ediid", mdata)

        # just for testing purposes, a pdr_status property will appear
        # in the record if this dataset is an update to a previous
        # release.  
        self.assertNotIn("pdr_status", mdata)  

        loader = ejs.SchemaLoader.from_directory(schemadir)
        val = ejs.ExtValidator(loader, ejsprefix='_')
        val.validate(mdata, False, True)

        # resolve_id() is not indepodent with async file examination turned on!
        #
        ## resolve_id() needs to be indepodent
        #data = self.srv.resolve_id(self.midasid)
        #self.assertEqual(to_dict(data), to_dict(mdata))

        with self.assertRaises(serv.IDNotFound):
            self.srv.resolve_id("asldkfjsdalfk")

    def test_resolve_id_published(self):
        # test resolving an identifier that has been published but is not
        # not currently being updated.

        with self.assertRaises(serv.IDNotFound):
            self.srv.resolve_id("STUVWXYZ")     # doesn't exist

        # insert a record into the archive
        src = os.path.join(mdarchive, "pdr02d4t.json")
        data = read_nerd(src)
        data['ediid'] = "STUVWXYZ"
        write_json(data, os.path.join(mdarchive, "stuvwxyz.json"))

        data = self.srv.resolve_id("STUVWXYZ")
        self.assertEqual(data['ediid'], 'STUVWXYZ')

    def test_resolve_id_withupdate(self):
        # test resolving an identifier for a dataset being updated (after
        # an initial publication)
        srczip = os.path.join(distarchive, "1491.1_0.mbag0_4-0.zip")
        destzip = os.path.join(distarchive, self.midasid+".1_0.mbag0_4-0.zip")
        cached = os.path.join(self.pubcache, os.path.basename(destzip))
        rmmrec = os.path.join(mdarchive, self.midasid+".json")

        try:
            shutil.copyfile(srczip, destzip)
            shutil.copy(os.path.join(datadir, self.midasid+".json"),
                        mdarchive)

            data = self.srv.resolve_id(self.midasid)
            self.assertIn("ediid", data)
            self.assertIn("pdr_status", data)  # previous version used!

            self.assertTrue(os.path.exists(cached))

        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)
            if os.path.exists(rmmrec):
                os.remove(rmmrec)
            time.sleep(0.2)  # wait for metadata thread to finish

    def test_resolve_id_usestore(self):
        # test resolving an identifier for a dataset being updated (after
        # an initial publication)
        midasid = "pdr2210"
        self.revdir = self.tf.mkdir("review")
        self.config['review_dir'] = self.revdir
        self.srv = serv.PrePubMetadataService(self.config)
        self.bagdir = os.path.join(self.bagparent, midasid)
        
        os.mkdir(os.path.join(self.revdir, "pdr2210"))
        shutil.copyfile(os.path.join(datadir, "pdr2210_pod.json"),
                        os.path.join(self.revdir,"pdr2210","_pod.json"))
        
        cached = os.path.join(self.pubcache, "pdr2210.3_1_3.mbag0_3-5.zip")

        data = self.srv.resolve_id(midasid)
        self.assertIn("ediid", data)
        self.assertEqual(data['version'], "3.1.3+ (in edit)")

        self.assertTrue(not os.path.exists(cached))
        self.assertTrue(os.path.isdir(self.bagdir))
        self.assertTrue(os.path.isdir(os.path.join(self.bagdir,"multibag")))
        

        



if __name__ == '__main__':
    test.main()
