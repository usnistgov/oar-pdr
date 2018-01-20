import os, sys, pdb, json
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.notify.base import Notice
from nistoar.pdr.notify.email import Mailer, EmailTarget
from nistoar.pdr.notify.archive import Archiver, ArchiveTarget
import nistoar.pdr.notify.service as notify
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

class TestTargetManager(test.TestCase):

    def test_aa_register_channel_class(self):
        mgr = notify.TargetManager()
        self.assertFalse(mgr.has_channel_class("fakeemail"))
        fm = mgr.register_channel_class("fakeemail",
                                        "nistoar.pdr.notify.email.FakeMailer")
        self.assertTrue(issubclass(fm, Mailer))
        self.assertTrue(mgr.has_channel_class("fakeemail"))
        self.assertTrue(mgr._channelcls["fakeemail"] is fm)

        fmer = mgr.register_channel_class("fakeremail", fm)
        self.assertTrue(fmer is fm)
        self.assertTrue(mgr.has_channel_class("fakeremail"))
        self.assertTrue(mgr._channelcls["fakeremail"] is fmer)

        with self.assertRaises(ImportError):
            mgr.register_channel_class("fakeremail", "goober.Mailer")
        with self.assertRaises(ValueError):
            mgr.register_channel_class("fakeremail", "Mailer")

    def test_aa_register_target_class(self):
        mgr = notify.TargetManager(targetcls={})
        self.assertFalse(mgr.has_target_class("email"))
        mt = mgr.register_target_class("email",
                                       "nistoar.pdr.notify.email.EmailTarget")
        self.assertTrue(issubclass(mt, EmailTarget))
        self.assertTrue(mgr.has_target_class("email"))
        self.assertTrue(mgr._targetcls["email"] is mt)

        mt = mgr.register_target_class("megamail", mt)
        self.assertTrue(mgr.has_target_class("megamail"))
        self.assertTrue(mgr._targetcls["megamail"] is mt)

    def test_default_cls(self):
        mgr = notify.TargetManager()
        self.assertTrue(mgr.has_channel_class('email'))
        self.assertTrue(mgr.has_channel_class('archive'))
        self.assertTrue(not mgr.has_channel_class('fakeemail'))
        
        self.assertTrue(mgr.has_target_class('email'))
        self.assertTrue(mgr.has_target_class('archive'))
        self.assertTrue(not mgr.has_target_class('fakeemail'))
        
        mgr = notify.TargetManager(channelcls={}, targetcls={})
        self.assertTrue(not mgr.has_channel_class('email'))
        self.assertTrue(not mgr.has_channel_class('archive'))
        self.assertTrue(not mgr.has_channel_class('fakeemail'))
        
        self.assertTrue(not mgr.has_target_class('email'))
        self.assertTrue(not mgr.has_target_class('archive'))
        self.assertTrue(not mgr.has_target_class('fakeemail'))

        with self.assertRaises(ImportError):
            mgr.register_target_class("fakeremail", "goober.MailTarget")
        with self.assertRaises(ValueError):
            mgr.register_target_class("fakeremail", "Target")
        

    def test_define_channel(self):
        mgr = notify.TargetManager()
        self.assertTrue(not mgr.has_channel("arch"))
        self.assertTrue(not mgr.has_channel("archive"))

        cfg = {
            'name': 'archive',
            'dir': "/tmp",
            'type': 'archive',
            'timeout': 500,
            'pretty': False
        }
        ch = mgr.define_channel(cfg)
        self.assertTrue(isinstance(ch, Archiver))
        self.assertTrue(not mgr.has_channel("arch"))
        self.assertTrue(mgr.has_channel("archive"))
        self.assertTrue(mgr.get_channel("archive") is ch)
        self.assertEqual(mgr.channel_names, ['archive'])
        
        ch = mgr.define_channel(cfg, "arch")
        self.assertTrue(isinstance(ch, Archiver))
        self.assertTrue(mgr.has_channel("arch"))
        self.assertTrue(mgr.get_channel("arch") is ch)
        self.assertTrue(mgr.get_channel("archive") is not ch)
        self.assertEqual(mgr.channel_names, ['arch', 'archive'])

        del cfg['name']
        with self.assertRaises(ConfigurationException):
            mgr.define_channel(cfg)
        mgr.define_channel(cfg, 'arch2')

        del cfg['type']
        with self.assertRaises(ConfigurationException):
            mgr.define_channel(cfg, 'arch3')

    def test_define_target(self):
        mgr = notify.TargetManager()
        chcfg = {
            'name': 'herb',
            'dir': "/tmp",
            'type': 'archive',
            'timeout': 500,
            'pretty': False
        }
        tcfg = {
            'name': 'gary',
            'fullname': 'Fred',
            'type': 'archive',
            'channel': 'herb'
        }

        self.assertTrue(not mgr.has_channel('herb'))
        mgr.define_channel(chcfg)
        self.assertTrue(mgr.has_channel('herb'))

        self.assertTrue(not mgr.has_target('gary'))
        self.assertNotIn('gary', mgr)
        self.assertIsNone(mgr.get('gary'))
        with self.assertRaises(KeyError):
            mgr['gary']

        tgt = mgr.define_target(tcfg)
        self.assertEqual(tgt.name, 'gary')
        self.assertEqual(tgt.fullname, 'Fred')
        self.assertTrue(isinstance(tgt, ArchiveTarget))
        self.assertTrue(isinstance(tgt.service, Archiver))
        self.assertTrue(mgr.has_target('gary'))
        self.assertIn('gary', mgr)
        self.assertTrue(mgr.get('gary') is tgt)
        self.assertTrue(mgr['gary'] is tgt)
        self.assertEqual(mgr.targets, ['gary'])

        del tcfg['name']
        with self.assertRaises(ConfigurationException):
            mgr.define_target(tcfg)
        mgr.define_target(tcfg, "cooper")
        self.assertIn('cooper', mgr)
        self.assertEqual(mgr.targets, ['cooper', 'gary'])

        del tcfg['channel']
        with self.assertRaises(ConfigurationException):
            mgr.define_target(tcfg, "busey")
        tcfg['channel'] = 'herb'
        del tcfg['type']
        with self.assertRaises(ConfigurationException):
            mgr.define_target(tcfg, "busey")
        tcfg['type'] = 'archive'
        tcfg['channel'] = 'goober'
        with self.assertRaises(ConfigurationException):
            mgr.define_target(tcfg, "busey")

service_cfg = {
    "archive_targets": [ "operators" ],
    "channels": [{
        "type": "email",
        "smtp_server": "email.nist.gov",
        "name": "fakeemail",
        "type": "fakeemail",
    }, {
        "name": "archive",
        "type": "archive"
    }],
    "targets": [{
        "name": "operators",
        "fullname": "OAR PDR Operators",
        "channel": 'fakeemail',
        "type": 'email',
        "from": ['PDR Notification System', 'oardist@nist.gov'],
        "to": [
            ['Raymond Plante', 'raymond.plante@nist.gov'],
            ['Gretchen Greene', 'gretchen.greene@nist.gov']
        ],
        "cc": [['Sys admin', 'oarsysadmin@nist.gov']],
        "bcc": [['Big boss', 'boss@nist.gov']],
    }, {
        "name": "me",
        "fullname": "Raymond Plante",
        "channel": 'fakeemail',
        "type": 'email',
        "from": ['Developer', 'raymond.plante@nist.gov'],
        "to": 'raymond.plante@nist.gov'
    }]        
}

class TestNotificationService(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.arcdir = self.tf.mkdir("archive")
        self.mbox = self.tf.mkdir("mbox")
        tm = notify.TargetManager()
        tm.register_channel_class("fakeemail",
                                  "nistoar.pdr.notify.email.FakeMailer")

        config = deepcopy(service_cfg)
        config['channels'][0]['cachedir'] = self.mbox
        config['channels'][1]['dir'] = self.arcdir
        self.svc = notify.NotificationService(config, targetmgr=tm)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.svc._targets2archive, ['operators'])
        self.assertTrue(self.svc._archiver)

        self.assertEqual(self.svc.channels, ['fakeemail', 'archive' ])
        self.assertEqual(self.svc.targets, ['me', 'operators' ])

        tm = notify.TargetManager()
        tm.register_channel_class("fakeemail",
                                  "nistoar.pdr.notify.email.FakeMailer")
        config = deepcopy(service_cfg)
        config['channels'][0]['cachedir'] = self.mbox
        del config['channels'][1]
        with self.assertRaises(ConfigurationException):
            self.svc = notify.NotificationService(config, targetmgr=tm)

        tm = notify.TargetManager()
        tm.register_channel_class("fakeemail",
                                  "nistoar.pdr.notify.email.FakeMailer")
        del config['archive_targets']
        self.svc = notify.NotificationService(config, targetmgr=tm)
        self.assertTrue(not self.svc._archiver)

        
    def test_archive(self):
        note = Notice("info", "Whoa!")

        archfile = os.path.join(self.arcdir, "goob.txt")
        self.assertTrue(not os.path.exists(archfile))
        self.svc.archive(note, "goob")
        self.assertTrue(os.path.exists(archfile))

    def test_notify(self):
        archfile1 = os.path.join(self.arcdir, "operators.txt")
        archfile2 = os.path.join(self.arcdir, "me.txt")
        cache = os.path.join(self.mbox, "notice.txt")

        self.assertTrue(not os.path.exists(archfile1))
        self.assertTrue(not os.path.exists(archfile2))
        self.assertTrue(not os.path.exists(cache))

        self.svc.notify("me", "info", "Hey, wake up!")
        self.assertTrue(not os.path.exists(archfile1))
        self.assertTrue(not os.path.exists(archfile2))
        self.assertTrue(os.path.exists(cache))
        
        self.svc.notify("operators", "info", "Un-oh")
        self.assertTrue(os.path.exists(archfile1))
        self.assertTrue(not os.path.exists(archfile2))
        self.assertTrue(os.path.exists(cache))
        


if __name__ == '__main__':
    test.main()
