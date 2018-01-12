import os, sys, pdb, json
import unittest as test

import nistoar.pdr.notify.base as notify

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

class TestNotice(test.TestCase):

    def test_ctor(self):
        d = notice_data.copy()
        notice = notify.Notice(d['type'], d['title'], d['description'], 
                               d['origin'], d['issued'],
                               color=d['metadata']['color'],
                               excitation=d['metadata']['excitation'])

        self.assertEqual(notice.type, d['type'])
        self.assertEqual(notice.title, d['title'])
        self.assertEqual(notice.description, d['description'])
        self.assertEqual(notice.origin, d['origin'])
        self.assertEqual(notice.issued, d['issued'])
        self.assertEqual(notice.metadata, d['metadata'])

        notice = notify.Notice(d['type'], d['title'], d['description'], 
                               color=d['metadata']['color'],
                               excitation=d['metadata']['excitation'])
        
        self.assertEqual(notice.type, d['type'])
        self.assertEqual(notice.title, d['title'])
        self.assertEqual(notice.description, d['description'])
        self.assertIsNone(notice.origin)
        self.assertTrue(isinstance(notice.issued, str))
        self.assertGreater(len(notice.issued), 0)
        self.assertEqual(notice.metadata, d['metadata'])

    def test_now(self):
        d = notice_data.copy()
        notice = notify.Notice(d['type'], d['title'])
        now = notice.now()
        self.assertTrue(isinstance(now, str))
        self.assertGreater(len(now), 0)

    def test_to_json(self):
        d = notice_data.copy()
        notice = notify.Notice(d['type'], d['title'], d['description'], 
                               d['origin'], d['issued'],
                               color=d['metadata']['color'],
                               excitation=d['metadata']['excitation'])

        j = notice.to_json()
        self.assertTrue(isinstance(j, str))
        jd = json.loads(j)

        self.assertEqual(notice.type, jd['type'])
        self.assertEqual(notice.title, jd['title'])
        self.assertEqual(notice.description, jd['description'])
        self.assertEqual(notice.origin, jd['origin'])
        self.assertEqual(notice.issued, jd['issued'])
        self.assertEqual(notice.metadata, jd['metadata'])

    def test_from_json(self):
        j = json.dumps(notice_data)
        notice = notify.Notice.from_json(j)

        d = notice_data.copy()
        self.assertEqual(notice.type, d['type'])
        self.assertEqual(notice.title, d['title'])
        self.assertEqual(notice.description, d['description'])
        self.assertEqual(notice.origin, d['origin'])
        self.assertEqual(notice.issued, d['issued'])
        self.assertEqual(notice.metadata, d['metadata'])




if __name__ == '__main__':
    test.main()
