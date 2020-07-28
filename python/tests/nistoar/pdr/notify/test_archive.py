import os, sys, pdb, json
import unittest as test

from nistoar.testing import *
from nistoar.pdr.notify.base import Notice, NotificationError
import nistoar.pdr.notify.archive as notify
from nistoar.pdr.exceptions import ConfigurationException

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')

notice_data = {
    "type": "FAILURE",
    "title": "data is devoid of science",
    "description": [
        "The data is dull and uninteresting.  Pure noise is less tedious than this data.  It reads like 'Smoke on the Water' but without the changing notes.",
        "This data should not be saved"
    ],
    "origin": "Preservation",
    "issued": "today",
    "metadata": {
        "color": "grey",
        "excitation": False
    }
}

def setUpModule():
    ensure_tmpdir()

def tearDownModule():
    rmtmpdir()

class TestArchiver(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.tmpdir = self.tf.mkdir("notify-archive")
        self.config = { "dir": self.tmpdir }
        self.archiver = notify.Archiver(self.config)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.archiver._timeout, 60)
        self.assertEqual(self.archiver._pretty, True)
        self.assertEqual(self.archiver._cdir, self.tmpdir)

        cfg = {
            'dir': self.tmpdir,
            'timeout': 500,
            'pretty': False
        }
        self.archiver = notify.Archiver(cfg)
        self.assertEqual(self.archiver._timeout, 500)
        self.assertEqual(self.archiver._pretty, False)
        self.assertEqual(self.archiver._cdir, self.tmpdir)

        del cfg['dir']
        with self.assertRaises(ConfigurationException):
            self.archiver = notify.Archiver(cfg)

    def test_archive(self):
        note = Notice("FAILURE", "Duck!")
        archfile = os.path.join(self.tmpdir, "operators.txt")
        self.assertTrue(not os.path.exists(archfile))

        self.archiver.archive("operators", note)
        self.assertTrue(os.path.exists(archfile))
        with open(archfile) as fd:
            lines = fd.readlines()

        self.assertEqual(lines[0], '{\n')
        self.assertEqual(lines[-2], '}\n')
        self.assertEqual(lines[-1], ',\n')
        self.assertGreater(len(lines), 5)
        js = ''.join(lines[0:-1])
        data = json.loads(js)
        self.assertIn('issued', data)
        self.assertEqual(data['type'], "FAILURE")
        self.assertEqual(data['title'], "Duck!")

        self.archiver.archive("operators", note)
        self.assertTrue(os.path.exists(archfile))
        with open(archfile) as fd:
            lines = fd.readlines()
        self.assertEqual(lines[0], '{\n')
        self.assertEqual(lines[-2], '}\n')
        self.assertEqual(lines[-1], ',\n')
        self.assertGreater(len(lines), 10)

    def test_notification_error(self):
        with self.assertRaises(NotificationError):
            raise NotificationError("Testing")

class TestArchiveTarget(test.TestCase):
    
    def setUp(self):
        self.tf = Tempfiles()
        self.tmpdir = self.tf.mkdir("notify-archive")
        self.config = { "dir": self.tmpdir }
        self.archiver = notify.Archiver(self.config)
        tcfg = { "name": "goober" }
        self.target = notify.ArchiveTarget(self.archiver, tcfg)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertTrue(self.target.service is self.archiver)

    def test_send_notice(self):
        note = Notice("FAILURE", "Duck!")
        archfile = os.path.join(self.tmpdir, "operators.txt")
        self.assertTrue(not os.path.exists(archfile))
        archfile = os.path.join(self.tmpdir, "goober.txt")
        self.assertTrue(not os.path.exists(archfile))

        self.target.send_notice(note)
        self.assertTrue(os.path.exists(archfile))
        with open(archfile) as fd:
            lines = fd.readlines()

        self.assertEqual(lines[0], '{\n')
        self.assertEqual(lines[-2], '}\n')
        self.assertEqual(lines[-1], ',\n')
        self.assertGreater(len(lines), 5)
        
        archfile = os.path.join(self.tmpdir, "operators.txt")
        self.target.send_notice(note, "operators")
        self.assertTrue(os.path.exists(archfile))
        with open(archfile) as fd:
            lines = fd.readlines()

        self.assertEqual(lines[0], '{\n')
        self.assertEqual(lines[-2], '}\n')
        self.assertEqual(lines[-1], ',\n')
        self.assertGreater(len(lines), 5)

        

        

if __name__ == '__main__':
    test.main()
