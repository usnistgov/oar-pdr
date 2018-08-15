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
            'id_registry_dir': self.workdir,
            'headbag_cache':   self.pubcache,
            'distrib_service': {
                'service_endpoint': "http://localhost:9091/"
            },
            'metadata_service': {
                'service_endpoint': "http://localhost:9092/"
            },
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

    def test_prepare_metadata_bag(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)

        self.assertTrue(os.path.exists(os.path.join(metadir, "pod.json")))
        self.assertTrue(os.path.exists(os.path.join(metadir, "nerdm.json")))

        # has file metadata
        self.assertTrue(os.path.exists(metadir))
        datafiles = "trial1.json trial2.json trial3 trial3/trial3a.json".split()
        for filepath in datafiles:
            self.assertTrue(os.path.exists(os.path.join(metadir, filepath,
                                                        "nerdm.json")))

        # has subcollection metadata
        mdfile = os.path.join(metadir, "trial3", "nerdm.json")
        self.assertTrue(os.path.exists(mdfile))

        
    def test_make_nerdm_record(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)
        self.assertTrue(os.path.exists(bagdir))

        data = self.srv.make_nerdm_record(bagdir)
        
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)

        self.assertEqual(len(data['components']), 8)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 6)
        self.assertEqual(data['inventory'][0]['descCount'], 8)

        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == 'sim.json':
                    continue
                self.assertTrue(comp['downloadURL'].startswith('https://data.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/'),
                                "{0} does not start with https://data.nist.gov/od/ds/3A1EE2F169DD3B8CE0531A570681DB5D1491/".format(comp['downloadURL']))
        self.assertEquals(dlcount, 6)
        
    def test_make_nerdm_record_cvt_dlurls(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)
        self.assertTrue(os.path.exists(bagdir))

        data = self.srv.make_nerdm_record(bagdir,
                                          baseurl='https://mdserv.nist.gov/')
        
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)

        self.assertEqual(len(data['components']), 8)
        self.assertEqual(data['inventory'][0]['forCollection'], "")
        self.assertEqual(len(data['inventory']), 2)
        self.assertEqual(data['inventory'][0]['childCount'], 6)
        self.assertEqual(data['inventory'][0]['descCount'], 8)
        
        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == 'sim.json':
                    continue
                self.assertTrue(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
        self.assertEquals(dlcount, 6)

        datafiles = { "trial1.json": "blah/blah/trial1.json" }
        data = self.srv.make_nerdm_record(bagdir, datafiles, 
                                          baseurl='https://mdserv.nist.gov/')

        comps = data['components']
        dlcount = 0
        for comp in comps:
            if 'downloadURL' in comp:
                dlcount += 1
                if comp['filepath'] == "trial1.json":
                    self.assertTrue(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
                else:
                    self.assertFalse(comp['downloadURL'].startswith('https://mdserv.nist.gov/'+self.midasid+'/'),
                                "Bad conversion of URL: "+comp['downloadURL'])
        self.assertEquals(dlcount, 6)

    def test_make_nerdm_record_withannots(self):
        metadir = os.path.join(self.bagdir, 'metadata')
        self.assertFalse(os.path.exists(self.bagdir))

        bagger = self.srv.prepare_metadata_bag(self.midasid)
        bagdir = bagger.bagdir
        self.assertEqual(bagdir, self.bagdir)
        self.assertTrue(os.path.exists(bagdir))

        data = self.srv.make_nerdm_record(bagdir)
        self.assertNotIn("authors", data)
        trial1 = [c for c in data['components']
                    if 'filepath' in c and c['filepath'] == "trial1.json"][0]
        self.assertNotIn('previewURL', trial1)
        ediid = data['ediid']
        
        # copy in some annotation files
        otherbag = os.path.join(datadir, "metadatabag")
        annotpath = os.path.join("metadata", "annot.json")
        self.assertTrue(os.path.exists(os.path.join(otherbag, annotpath)))
        shutil.copyfile(os.path.join(otherbag, annotpath),
                        os.path.join(self.bagdir, annotpath))
        self.assertTrue(os.path.exists(os.path.join(self.bagdir, annotpath)))
        annotpath = os.path.join("metadata", "trial1.json", "annot.json")
        self.assertTrue(os.path.exists(os.path.join(otherbag, annotpath)))
        shutil.copyfile(os.path.join(otherbag, annotpath),
                        os.path.join(self.bagdir, annotpath))
        self.assertTrue(os.path.exists(os.path.join(self.bagdir, annotpath)))

        data = self.srv.make_nerdm_record(bagdir)
        
        self.assertIn("ediid", data)
        self.assertIn("components", data)
        self.assertIn("inventory", data)
        self.assertIn("authors", data)
        self.assertEqual(data['ediid'], ediid)
        self.assertEqual(data['foo'], "bar")

        self.assertEqual(len(data['components']), 8)
        trial1 = [c for c in data['components']
                    if 'filepath' in c and c['filepath'] == "trial1.json"][0]
        self.assertIn('previewURL', trial1)
        self.assertTrue(trial1['previewURL'].endswith("trial1.json/preview"))
        
        
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

        # resolve_id() needs to be indepodent
        data = self.srv.resolve_id(self.midasid)
        self.assertEqual(data, mdata)

        with self.assertRaises(serv.IDNotFound):
            self.srv.resolve_id("asldkfjsdalfk")

    def test_locate_data_file(self):
        loc = self.srv.locate_data_file(self.midasid, 'trial3/trial3a.json')
        self.assertEquals(len(loc), 2)
        self.assertEquals(loc[0], os.path.join(self.upldir,self.midasid[32:],
                                               'trial3/trial3a.json'))
        self.assertEquals(loc[1], "application/json")

        loc = self.srv.locate_data_file(self.midasid, 'trial1.json')
        self.assertEquals(len(loc), 2)
        self.assertEquals(loc[0], os.path.join(self.revdir,self.midasid[32:],
                                               'trial1.json'))
        self.assertEquals(loc[1], "application/json")

    def test_no_locate_data_file(self):
        loc = self.srv.locate_data_file(self.midasid, 'goober/trial3a.json')
        self.assertEquals(len(loc), 2)
        self.assertIsNone(loc[0])
        self.assertIsNone(loc[1])

        
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

        try:
            shutil.copyfile(srczip, destzip)

            data = self.srv.resolve_id(self.midasid)
            self.assertIn("ediid", data)
            self.assertIn("pdr_status", data)  # previous version used!

            self.assertTrue(os.path.exists(cached))

        finally:
            if os.path.exists(destzip):
                os.remove(destzip)
            if os.path.exists(cached):
                os.remove(cached)
        


        

        
        
        

if __name__ == '__main__':
    test.main()
