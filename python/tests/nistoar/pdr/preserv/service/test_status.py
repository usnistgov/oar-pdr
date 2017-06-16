import os, pdb, sys, json
import unittest as test

from nistoar.testing import *
from nistoar.pdr.preserv.service import status

def setUpModule():
    ensure_tmpdir()
def tearDownModule():
    rmtmpdir()

class TestReadWrite(test.TestCase):

    cachefile = os.path.join(tmpdir(), "status.json")
    data = {
        'id':  'aaa',
        'goob': 'gurn',
        'age': 5
    }
    
    def tearDown(self):
        if os.path.exists(self.cachefile):
            os.remove(self.cachefile)

    def testWrite(self):
        status._write_status(self.cachefile, self.data)

        with open(self.cachefile) as fd:
            got = json.load(fd)

        self.assertIn('goob', got)
        self.assertEqual(self.data, got)

    def testRead(self):
        with open(self.cachefile, 'w') as fd:
            json.dump(self.data, fd)

        got = status._read_status(self.cachefile)
        self.assertIn('goob', got)
        self.assertEqual(self.data, got)

class TestSIPStatus(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.cachedir = self.tf.mkdir("status")
        self.cfg = { 'cachedir': self.cachedir }
        self.status = status.SIPStatus("ffff", self.cfg)

    def tearDown(self):
        self.tf.clean()

    def test_ctor(self):
        data = {
            'id': 'ffff',
            'state': "pending",
            'message': status.user_message[status.PENDING]
        }
        self.assertEqual(self.status.id, data['id'])
        self.assertEqual(self.status.data, data)
        self.assertEqual(self.status._cachefile,
                         os.path.join(self.cachedir,"ffff.json"))

        with self.assertRaises(ValueError):
            status.SIPStatus('')

        data['goob'] = 'gurn'
        self.status = status.SIPStatus('ffff', _data=data)
        self.assertEqual(self.status.data['goob'], 'gurn')
        self.assertEqual(self.status.data, data)
        self.assertEquals(self.status._cachefile, "/tmp/sipstatus/ffff.json")

    def test_cache(self):
        self.assertTrue(not os.path.exists(self.status._cachefile))
        self.status.data['gurn'] = 'goob'
        self.status.cache()
        self.assertTrue(os.path.exists(self.status._cachefile))

        self.assertIn('update_stamp', self.status.data)
        self.assertTrue(isinstance(self.status.data['update_stamp'], float))
        self.assertIn('update_date', self.status.data)

        with open(self.status._cachefile) as fd:
            data = json.load(fd)
        self.assertIn('update_stamp', data)
        self.assertTrue(isinstance(data['update_stamp'], float))
        self.assertIn('update_date', data)
        self.assertIn('gurn', data)
        self.assertEqual(data['id'], 'ffff')
        self.assertEqual(data['gurn'], 'goob')
        self.assertEqual(data['state'], 'pending')
        self.assertEqual(data['message'], 
                         status.user_message[status.PENDING])

        self.status = status.SIPStatus("ffff", self.cfg)
        self.assertIn('gurn', self.status.data)
        self.assertEqual(self.status.data['gurn'], 'goob')
        self.assertEqual(self.status.data['id'], 'ffff')

    def test_refresh(self):
        self.status.data['foo'] = 'bar'
        self.status.cache()
        self.status.data['gurn'] = 'goob'
        self.status.refresh()
        self.assertIn('foo', self.status.data)
        self.assertEqual(self.status.data['foo'], 'bar')
        self.assertNotIn('gurn', self.status.data)

    def test_update(self):
        self.assertTrue(not os.path.exists(self.status._cachefile))
        self.status.data['gurn'] = 'goob'

        self.status.update(status.SUCCESSFUL)
        self.assertTrue(os.path.exists(self.status._cachefile))
        self.assertEquals(self.status.data['state'], 'successful')
        self.assertEqual(self.status.data['message'], 
                         status.user_message[status.SUCCESSFUL])
        self.assertNotIn('start_stamp', self.status.data)
        self.assertNotIn('start_date', self.status.data)
        
        with open(self.status._cachefile) as fd:
            data = json.load(fd)
        self.assertEquals(data['state'], 'successful')
        self.assertEqual(data['message'], 
                         status.user_message[status.SUCCESSFUL])
        self.assertEquals(data['gurn'], 'goob')

        self.status.update(status.FAILED, "SIP is too big")
        self.assertEquals(self.status.data['state'], 'failed')
        self.assertEqual(self.status.data['message'], "SIP is too big")

    def test_start(self):
        self.assertTrue(not os.path.exists(self.status._cachefile))
        self.status.data['gurn'] = 'goob'

        self.status.start()
        self.assertEquals(self.status.data['state'], 'in progress')
        self.assertEqual(self.status.data['message'], 
                         status.user_message[status.IN_PROGRESS])
        self.assertEquals(self.status.data['gurn'], 'goob')

        self.status.update(status.FAILED)
        self.assertNotEquals(self.status.data['state'], 'in progress')

        self.status.start("chugging...")
        self.assertEquals(self.status.data['state'], 'in progress')
        self.assertEqual(self.status.data['message'], "chugging...")

    def test_for_update(self):
        self.status.start()
        self.status.update(status.FAILED)

        self.status = status.SIPStatus.for_update('ffff', self.cfg)
        self.assertEqual(self.status.id, 'ffff')
        self.assertEqual(self.status.data['state'], status.PENDING)
        self.assertNotIn('update_stamp', self.status.data)
        self.assertIn('history', self.status.data)
        history = self.status.data['history']
        self.assertEqual(len(history), 1)
        self.assertNotIn('history', history[0])
        self.assertNotIn('id', history[0])
        self.assertEqual(history[0]['state'], status.FAILED)

        self.status.update(status.SUCCESSFUL)
        self.status = status.SIPStatus.for_update('ffff', self.cfg)
        self.assertEqual(self.status.id, 'ffff')
        self.assertEqual(self.status.data['state'], status.PENDING)
        self.assertNotIn('update_stamp', self.status.data)
        self.assertIn('history', self.status.data)
        history = self.status.data['history']
        self.assertEqual(len(history), 2)
        self.assertNotIn('history', history[0])
        self.assertNotIn('id', history[0])
        self.assertEqual(history[0]['state'], status.SUCCESSFUL)
        self.assertNotIn('history', history[1])
        self.assertNotIn('id', history[1])
        self.assertEqual(history[1]['state'], status.FAILED)

        



        

if __name__ == '__main__':
    test.main()
