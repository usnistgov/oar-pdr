import os, sys, pdb, shutil, logging, json
from cStringIO import StringIO
from io import BytesIO
import warnings as warn
import unittest as test
from collections import OrderedDict

from nistoar.tests import *
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.preserv.bagger.midas as midas
import nistoar.pdr.preserv.exceptions as exceptions

# datadir = nistoar/preserv/tests/data
datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "tests", "data"
)

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

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeLog(loghdlr)
        loghdlr = None
    rmtmpdir()

class TestMIDASMetadataBagger(test.TestCase):

    testsip = os.path.join(datadir, "midassip")
    midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

    def setUp(self):
        self.tf = Tempfiles()
        self.bagparent = self.tf.mkdir("bagger")
        self.upldir = os.path.join(self.testsip, "upload")
        self.revdir = os.path.join(self.testsip, "review")
        self.bagr = midas.MIDASMetadataBagger(self.midasid, self.bagparent,
                                              self.revdir, self.upldir)

    def tearDown(self):
        self.bagr.bagbldr._unset_logfile()
        self.bagr = None
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.bagr.name, self.midasid)
        self.assertEqual(self.bagr.state, "review")
        self.assertEqual(len(self.bagr._indirs), 2)
        self.assertEqual(self.bagr._indirs[0],
                         os.path.join(self.revdir, self.midasid))
        self.assertEqual(self.bagr._indirs[1],
                         os.path.join(self.upldir, self.midasid))
        self.assertIsNotNone(self.bagr.bagbldr)
        self.assertIsNone(self.bagr.inpodfile)
        self.assertIsNone(self.bagr.resmd)
        self.assertIsNone(self.bagr.datafiles)

if __name__ == '__main__':
    test.main()
