import os, sys, pdb, json
import unittest as test

from nistoar.testing import *
from nistoar.pdr.notify.base import Notice
import nistoar.pdr.notify.email as notify

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

class TestEmailFilters(test.TestCase):

    def test_fmtemail(self):
        self.assertEqual(notify._fmtemail(['Name', 'addr']), '"Name" <addr>')

    def test_rawemail(self):
        self.assertEqual(notify._rawemail(['Name', 'addr']), 'addr')

class TestMailer(test.TestCase):

    config = {
        "smtp_server": "email.nist.gov",
        "smtp_port": 55
    }

    def setUp(self):
        self.tf = Tempfiles()
        self.tmpdir = self.tf.mkdir("mailer")
        self.mailer = notify.FakeMailer(self.config, self.tmpdir)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.mailer._server, self.config['smtp_server'])
        self.assertEqual(self.mailer._port, self.config['smtp_port'])
        self.assertTrue(isinstance(self.mailer._port, int))

    def test_send_email(self):
        self.mailer.send_email("oardist@nist.gov",
                               ["raymond.plante@nist.gov",
                                "gretchen.greene@nist.gov"],
                               "Hi there!")
        
        with open(os.path.join(self.mailer.cache, "notice.txt")) as fd:
            msg = fd.read().split("\n")

        self.assertEqual(msg[0],
                         "To raymond.plante@nist.gov gretchen.greene@nist.gov")
        self.assertEqual(msg[1], "From oardist@nist.gov")
        self.assertEqual(msg[2], "Hi there!")

class TestEmailTarget(test.TestCase):

    mailer_config = {
        "smtp_server": "email.nist.gov",
        "smtp_port": 55
    }

    target_config = {
        "name": "operators",
        "fullname": "OAR PDR Operators",
        "from": ['PDR Notification System', 'oardist@nist.gov'],
        "to": [
            ['Raymond Plante', 'raymond.plante@nist.gov'],
            ['Gretchen Greene', 'gretchen.greene@nist.gov']
        ],
        "cc": [['Sys admin', 'oarsysadmin@nist.gov']],
        "bcc": [['Big boss', 'boss@nist.gov']],
    }

    def setUp(self):
        self.tf = Tempfiles()
        self.tmpdir = self.tf.mkdir("mailer")
        self.mailer = notify.FakeMailer(self.mailer_config, self.tmpdir)
        self.target = notify.EmailTarget(self.mailer, self.target_config)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        self.assertEqual(self.target.type, "email")
        self.assertEqual(self.target.name, "operators")
        self.assertEqual(self.target.fullname, "OAR PDR Operators")
        self.assertEqual(self.target.fromaddr, 'oardist@nist.gov')
        self.assertEqual(self.target.recipients[0], 'raymond.plante@nist.gov')
        self.assertEqual(self.target.recipients[1], 'gretchen.greene@nist.gov')
        self.assertEqual(self.target.recipients[2], 'oarsysadmin@nist.gov')
        self.assertEqual(self.target.recipients[3], 'boss@nist.gov')

        self.assertEqual(self.target.mail_header['From'],
                         '"PDR Notification System" <oardist@nist.gov>')
        self.assertIn('"OAR PDR Operators: Raymond Plante" <raymond.plante@nist.gov>',
                      self.target.mail_header['To'])
        self.assertIn('"Sys admin" <oarsysadmin@nist.gov>',
                      self.target.mail_header['Cc'])
        self.assertNotIn("Bcc", self.target.mail_header)

    def test_format_subject(self):
        note = Notice("FAILURE", "Duck!")
        self.assertEqual(self.target.format_subject(note),
                         "PDR Notice: FAILURE: Duck!")
    
    def test_format_body(self):
        note = Notice.from_json(notice_data)
        body = self.target.format_body(note).split("\n")
        self.assertEqual(body[0], "Attention: OAR PDR Operators")
        self.assertEqual(body[1], "Notification Type: FAILURE")
        self.assertEqual(body[2], "Origin: Preservation")
        self.assertEqual(body[4], "data is devoid of science")
        self.assertEqual(body[6], "The data is dull and uninteresting.  Pure noise is less tedious than this data.")
        self.assertEqual(body[7], "It reads like 'Smoke on the Water' but without the changing notes.")
        self.assertEqual(body[9], "This data should not be saved")

        self.assertTrue(body[11].startswith("Issued: "))
        self.assertEqual(body[12], "color: grey")
        self.assertEqual(body[13], "excitation: False")
        
    def test_make_message(self):
        hdr = self.target._make_message("Done!", "Yahoo!").split('\n')
        self.assertIn('From: "PDR Notification System" <oardist@nist.gov>', hdr)
        self.assertIn('To: "OAR PDR Operators: Raymond Plante" <raymond.plante@nist.gov>,', hdr)
        self.assertIn(' "Gretchen Greene" <gretchen.greene@nist.gov>', hdr)
        self.assertIn('Cc: "Sys admin" <oarsysadmin@nist.gov>', hdr)
        self.assertIn('Subject: Done!', hdr)
        self.assertIn('Yahoo!', hdr)

    def test_send_notice(self):
        note = Notice.from_json(notice_data)
        self.target.send_notice(note)

        with open(os.path.join(self.mailer.cache, "notice.txt")) as fd:
            msg = fd.read().split("\n")

        self.assertEqual(msg[0],
                         "To raymond.plante@nist.gov gretchen.greene@nist.gov oarsysadmin@nist.gov boss@nist.gov")
        self.assertEqual(msg[1], "From oardist@nist.gov")
        # self.assertTrue(msg[2].startswith("From oardist@nist.gov "))
        self.assertIn('From: "PDR Notification System" <oardist@nist.gov>', msg)
        self.assertIn('To: "OAR PDR Operators: Raymond Plante" <raymond.plante@nist.gov>,', msg)
        self.assertIn(' "Gretchen Greene" <gretchen.greene@nist.gov>', msg)
        self.assertIn('Cc: "Sys admin" <oarsysadmin@nist.gov>', msg)
        self.assertIn('Subject: PDR Notice: FAILURE: data is devoid of science', msg)
        self.assertIn('The data is dull and uninteresting.  Pure noise is less tedious than this data.', msg)

if __name__ == '__main__':
    test.main()
