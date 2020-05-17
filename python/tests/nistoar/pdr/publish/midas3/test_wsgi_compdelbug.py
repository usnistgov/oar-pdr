"""
This test was created to test the correction of issue ODD-874 ("Pubserver: 
Files added via MIDAS are not showing up on the landing page").  In this bug, 
adding a new data file would cause any previously added files to be deleted.
This checks to make sure this does not happen.  
"""
import os, sys, pdb, shutil, logging, json, time
from StringIO import StringIO
from collections import OrderedDict
import unittest as test
import requests
from nistoar.testing import *
from nistoar.pdr import def_jq_libdir

import nistoar.pdr.config as config
import nistoar.pdr.utils as utils
import nistoar.pdr.publish.midas3.wsgi as wsgi
import nistoar.pdr.publish.midas3.service as mdsvc
from nistoar.pdr.publish.midas3.webrecord import RequestLogParser
from nistoar.pdr.preserv.bagit import builder as bldr

datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "preserv", "data"
)
testdir = os.path.dirname(os.path.abspath(__file__))
custport = 9091
custbaseurl = "http://localhost:{0}/draft/".format(custport)

loghdlr = None
rootlog = None
def setUpModule():
    ensure_tmpdir()
    global rootlog
    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_publishing.log"))
    loghdlr.setLevel(logging.DEBUG-5)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)
    rootlog.setLevel(logging.DEBUG-1)


def tearDownModule():
    global rootlog
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestLatestHandlerBug(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = "mds2-7213" 
    arkid   = "ark:/88434/mds2-7213" 

    def start(self, status, headers=None, extup=None):
        self.resp.append(status)
        for head in headers:
            self.resp.append("{0}: {1}".format(head[0], head[1]))

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("publish")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.config = {
            'working_dir':     self.workdir,
            'review_dir':      self.revdir,
            'upload_dir':      self.upldir,
            'id_registry_dir': self.workdir,
            'async_file_examine': False,
            'customization_service': {
                'service_endpoint': custbaseurl,
                'merge_convention': 'midas1',
                'updatable_properties': [ "title", "authors", "_editStatus" ],
                'auth_key': "SECRET"
            }
        }
        self.bagparent = os.path.join(self.workdir, "mdbags")
        self.bagdir = os.path.join(self.bagparent, self.midasid)
        self.mddir = os.path.join(self.bagdir, "metadata")

        self.svc = mdsvc.MIDAS3PublishingService(self.config, self.workdir,
                                                 self.revdir, self.upldir)
        self.sipdir = os.path.join(self.upldir, "7213")
        self.hdlr = None
        self.resp = []

    def tearDown(self):
        self.svc.wait_for_all_workers(300)
        self.tf.clean()

    def gethandler(self, path, env):
        return wsgi.LatestHandler(path, self.svc, env, self.start, "secret")

    def test_comp_delete_bug(self):
        req = {
            'REQUEST_METHOD': "POST",
            'CONTENT_TYPE': 'application/json',
            'PATH_INFO': '/pdr/latest',
            'HTTP_AUTHORIZATION': 'Bearer secret'
        }
        self.hdlr = self.gethandler('', req)
        
        podf = os.path.join(self.sipdir, "pod1.json")
        with open(podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])

        self.assertTrue(os.path.isdir(self.bagdir))
        self.assertTrue(os.path.isdir(self.mddir))
        self.svc.wait_for_all_workers(300)
        self.assertTrue(os.path.isfile(os.path.join(self.workdir,"nrdserv",
                                                    self.midasid+".json")))

        self.assertTrue(os.path.isdir(os.path.join(self.mddir,
                                                   "RegistryFederationFigure.pptx.sha256")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir,
                                                   "RegistryFederationFigure.pptx")))
        self.assertTrue(not os.path.exists(os.path.join(self.mddir, "res-md.xsd.sha256")))
        self.assertTrue(not os.path.exists(os.path.join(self.mddir, "res-md.xsd")))
        self.assertTrue(not os.path.exists(os.path.join(self.mddir, "k+_data.txt.sha256")))
        self.assertTrue(not os.path.exists(os.path.join(self.mddir, "k+_data.txt")))

        podf = os.path.join(self.sipdir, "pod2.json")
        with open(podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])
        self.svc.wait_for_all_workers(300)

        # new file added but old file was not deleted
        self.assertTrue(os.path.isdir(os.path.join(self.mddir, "res-md.xsd.sha256")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir, "res-md.xsd")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir,
                                                   "RegistryFederationFigure.pptx.sha256")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir,
                                                   "RegistryFederationFigure.pptx")))
        self.assertTrue(not os.path.exists(os.path.join(self.mddir, "k+_data.txt.sha256")))
        self.assertTrue(not os.path.exists(os.path.join(self.mddir, "k+_data.txt")))

        podf = os.path.join(self.sipdir, "pod3.json")
        with open(podf) as fd:
            req['wsgi.input'] = fd
            body = self.hdlr.handle()

        self.assertIn("201", self.resp[0])
        self.assertEquals(body, [])
        self.svc.wait_for_all_workers(300)

        # new file added but old files were not deleted
        self.assertTrue(os.path.isdir(os.path.join(self.mddir, "k+_data.txt.sha256")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir, "k+_data.txt")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir, "res-md.xsd.sha256")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir, "res-md.xsd")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir,
                                                   "RegistryFederationFigure.pptx.sha256")))
        self.assertTrue(os.path.isdir(os.path.join(self.mddir,
                                                   "RegistryFederationFigure.pptx")))


        
        
        



if __name__ == '__main__':
    test.main()
