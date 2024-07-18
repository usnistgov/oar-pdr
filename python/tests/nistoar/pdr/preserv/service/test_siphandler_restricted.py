# These unit tests specifically test the siphandler module's support for
# restricted public data.  This includes creating a special bag for downloading
# via the restricted public gateway.
#
import os, pdb, sys, logging, yaml, time, re
import unittest as test
from zipfile import ZipFile

from nistoar.testing import *
from nistoar.pdr.preserv.service import siphandler as sip
from nistoar.pdr.preserv.service import status
import nistoar.pdr.preserv.bagit.builder as bldr
from nistoar.pdr.preserv.bagit.bag import NISTBag
from nistoar.pdr.preserv import AIPValidationError
from nistoar.pdr.preserv.bagger import midas3 as midas
from nistoar.pdr import utils

# datadir = nistoar/pdr/preserv/data
datadir = os.path.join( os.path.dirname(os.path.dirname(__file__)), "data" )

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
basedir = os.path.dirname(os.path.dirname(os.path.dirname(
                                                 os.path.dirname(pdrmoddir))))
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

def unzip(zipfile):
    zipdir = os.path.dirname(zipfile)
    zip = ZipFile(zipfile)
    zip.extractall(zipdir)
    

class TestSIPHandlerRestricted(test.TestCase):

    testsip = os.path.join(datadir, "metadatabag")
    revdir = os.path.join(datadir, "midassip", "review")
    # testdata = os.path.join(datadir, "samplembag", "data")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'
    arkid = "ark:/88434/mds2-1491"

    def setUp(self):
        self.archtf = Tempfiles()
        self.storedir = distarchive
        if not os.path.exists(distarchive):
            self.archtf.mkdir("distarchive")
        
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("preserv")
        self.sipdata = os.path.join(self.revdir, "1491")
        self.mdbags =  os.path.join(self.workdir, "mdbags")
        os.mkdir(self.mdbags)
        self.dataroot = os.path.join(self.workdir, "data")
        os.mkdir(self.dataroot)
        self.datadir = os.path.join(self.dataroot, "1491")
        self.stagedir = os.path.join(self.workdir, "staging")
        os.mkdir(self.stagedir)
        os.mkdir(os.path.join(self.stagedir,"_nerd"))
        self.pubcache = self.stagedir
        # self.storedir = os.path.join(self.workdir, "store")
        # os.mkdir(self.storedir)
        self.restrictdir = os.path.join(self.workdir, "restrict")
        os.mkdir(self.restrictdir)
        self.statusdir = os.path.join(self.workdir, "status")
        os.mkdir(self.statusdir)
        self.bagparent = os.path.join(self.datadir, "_preserv")
        self.sipdir = os.path.join(self.mdbags, self.midasid)

        with open(os.path.join(datadir, "bagger_conf.yml")) as fd:
            baggercfg = yaml.load(fd)
        baggercfg.update({
            'store_dir': self.storedir,
            'restricted_store_dir': self.restrictdir,
            'restricted_access': {
                "gateway_url": "https://nist.force.com/pdr?",
                "disclaimer": "Be careful."
            }
        })            
            
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
            'repo_access': {
                'headbag_cache':   self.pubcache,
                'distrib_service': {
                    'service_endpoint': "http://localhost:9091/"
                },
                'metadata_service': {
                    'service_endpoint': "http://localhost:9092/"
                }
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
        self.archtf.clean()

    def setup_sip(self, srcdir, destdir):
        # replicate the SIP data to a writable directory; change download
        # urls in metadata to reference simulated service
        shutil.copytree(srcdir, destdir)
        podf = os.path.join(destdir, "_pod.json")
        self.restrict_pod(podf)

        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, destdir, config=self.config['bagger'])
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.apply_pod(podf)
        mdbgr.done()

        
    def restrict_pod(self, podf):
        # change download urls in given POD file to reference simulated service
        datadotnist = re.compile(r'^https://data.nist.gov/')
        pod = utils.read_json(podf)
        dists = pod.setdefault('distribution',[])
        for dist in dists:
            if 'downloadURL' in dist:
                dist['downloadURL'] = \
                    datadotnist.sub('http://localhost:9091/',dist['downloadURL'])
        dists.append({
            "title": "Restricted Access Gateway",
            "accessURL": "https://nist.force.com/pdr?id="+pod.get('identifier'),
            "mediaType": "text/html"
        })
        pod['accessLevel'] = "restricted public"
        pod.setdefault('rights', "gotta register")
        utils.write_json(pod, podf)

    def test_singlebag(self):
        # test creation of a small single bag
        self.setup_sip(self.sipdata, self.datadir)
        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)

        self.assertEqual(self.sip.state, status.FORGOTTEN)

        # prep bag for serialization
        self.sip.bagger.make_bag()

        # check to make sure the midas3 bagger did its work
        bag = NISTBag(self.sip.bagger.bagdir)
        nerdm = bag.nerdm_record()
        self.assertEqual(nerdm.get('accessLevel'), "restricted public")
        self.assertEqual(nerdm.get('disclaimer'), "Be careful.")
        rpg = [c for c in self.sip.bagger.sip.nerd.get('components')
                 if 'accessURL' in c and c['accessURL'].startswith("https://nist.force.com/pdr?")]
        self.assertEquals(len(rpg), 1)
        self.assertEquals(rpg[0]['@type'][0], "nrdp:RestrictedAccessPage")
        self.assertTrue(self.sip.bagger.sip.nerd.get('rights'))
        self.assertEquals(self.sip.bagger.sip.nerd.get('version'), '1.0.0')
        
        # serialize
        aipid = re.sub(r'^ark:/\d+/', '', nerdm['ediid'])
        savefiles = self.sip._serialize_restricted(self.sip.bagger.bagdir, aipid, self.stagedir, "zip")

        self.assertEquals(len(savefiles), 2)
        self.assertIn(os.path.join(self.stagedir, aipid+'.zip'), savefiles)
        self.assertIn(os.path.join(self.stagedir, aipid+'.zip.sha256'), savefiles)

        # files were created
        self.assertTrue(os.path.isfile(savefiles[0]))
        self.assertTrue(os.path.isfile(savefiles[1]))

        os.system("cd %s; unzip -q %s" % (self.stagedir, aipid+'.zip'))
        self.assertTrue(os.path.isdir(os.path.join(self.stagedir, aipid)))
        for f in "trial1.json trial2.json trial3/trial3a.json".split():
            self.assertTrue(os.path.isfile(os.path.join(self.stagedir, aipid, "data", f)))
            self.assertTrue(os.path.isfile(os.path.join(self.stagedir, aipid, "metadata", f, "nerdm.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.stagedir, aipid, "bag-info.txt")))
        self.assertTrue(not os.path.exists(os.path.join(self.stagedir, aipid, "multibag")))

    def test_update(self):
        # test creation of a small single bag
        self.setup_sip(self.sipdata, self.datadir)
        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)
        pod = utils.read_json(os.path.join(self.datadir, "_pod.json"))

        self.assertEqual(self.sip.state, status.FORGOTTEN)

        # create the initial version
        self.sip.bagit()

        # check that the output files got sent to the restricted dir
        stored = [f for f in os.listdir(self.storedir) if f.startswith(self.midasid)]
        self.assertEquals(len(stored), 0)
        stored = [f for f in os.listdir(self.restrictdir) if f.startswith(self.midasid)]
        self.assertIn(self.midasid+".zip", stored)
        self.assertIn(self.midasid+".zip.sha256", stored)
        stored = [f for f in stored if f.startswith(self.midasid+".1_0_0.mbag")]
        self.assertEquals(len(stored), 2)
        shutil.rmtree(os.path.join(self.mdbags, self.midasid))
        shutil.rmtree(self.datadir)
        os.mkdir(self.datadir)

        # create an update
        pod['title'] += '!'
        mdbgr = midas.MIDASMetadataBagger(self.midasid, self.mdbags, self.datadir,
                                          config=self.config['bagger'])
        mdbgr.ensure_data_files(examine="sync")
        mdbgr.apply_pod(pod)
        mdbgr.finalize_version()
        mdbgr.done()

        nerdm = mdbgr.bagbldr.bag.nerd_metadata_for('', True)
        self.assertEquals(nerdm['version'], "1.0.1")
        self.assertEqual(nerdm.get('accessLevel'), "restricted public")
        self.assertEqual(nerdm.get('disclaimer'), "Be careful.")

        self.sip = sip.MIDAS3SIPHandler(self.midasid, self.config)
        self.sip.bagger.make_bag()
        
        bag = NISTBag(self.sip.bagger.bagdir)
        nerdm = bag.nerdm_record()
        self.assertEqual(nerdm.get('accessLevel'), "restricted public")
        self.assertEqual(nerdm.get('disclaimer'), "Be careful.")
        self.assertEqual(len(nerdm['components']), 10)
        self.assertEquals(nerdm['version'], "1.0.1")
        
        # serialize
        aipid = re.sub(r'^ark:/\d+/', '', nerdm['ediid'])
        savefiles = self.sip._serialize_restricted(self.sip.bagger.bagdir, aipid, self.stagedir, "zip")

        self.assertEquals(len(savefiles), 2)
        self.assertIn(os.path.join(self.stagedir, aipid+'.zip'), savefiles)
        self.assertIn(os.path.join(self.stagedir, aipid+'.zip.sha256'), savefiles)

        # files were created
        self.assertTrue(os.path.isfile(savefiles[0]))
        self.assertTrue(os.path.isfile(savefiles[1]))

        os.system("cd %s; unzip -q %s" % (self.stagedir, aipid+'.zip'))
        self.assertTrue(os.path.isdir(os.path.join(self.stagedir, aipid)))
        for f in "trial1.json trial2.json trial3/trial3a.json".split():
            self.assertTrue(os.path.isfile(os.path.join(self.stagedir, aipid, "metadata", f, "nerdm.json")),
                            "restored bag is missing metadata file for "+f)
            self.assertTrue(os.path.isfile(os.path.join(self.stagedir, aipid, "data", f)),
                            "restored bag is missing data file, "+f)
        self.assertTrue(os.path.isfile(os.path.join(self.stagedir, aipid, "bag-info.txt")))
        self.assertTrue(not os.path.exists(os.path.join(self.stagedir, aipid, "multibag")))

        bag = NISTBag(os.path.join(self.stagedir, aipid))
        nerdm = bag.nerdm_record()
        self.assertEqual(nerdm.get('accessLevel'), "restricted public")
        self.assertEqual(nerdm.get('disclaimer'), "Be careful.")
        self.assertEqual(len(nerdm['components']), 10)
        self.assertEquals(nerdm['version'], "1.0.1")
        
        
        
                         


if __name__ == '__main__':
    test.main()
