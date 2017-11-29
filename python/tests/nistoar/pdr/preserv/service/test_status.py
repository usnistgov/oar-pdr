import os, pdb, sys, json
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.preserv.service import status

def setUpModule():
    ensure_tmpdir()
def tearDownModule():
    rmtmpdir()

class TestSIPStatusFile(test.TestCase):

    cachefile = os.path.join(tmpdir(), "statusfile.json")
    data = {
        'id':  'aaa',
        'goob': 'gurn',
        'age': 5
    }

    def setUp(self):
        with open(self.cachefile, 'w') as fd:
            json.dump(self.data, fd)

    def tearDown(self):
        if os.path.exists(self.cachefile):
            os.remove(self.cachefile)

    def test_ctor(self):
        sf = status.SIPStatusFile(self.cachefile)
        self.assertEqual(sf._file, self.cachefile)
        self.assertIsNone(sf._fd)
        self.assertIsNone(sf._type)
        del sf

        sf = status.SIPStatusFile(self.cachefile, status.LOCK_READ)
        self.assertEqual(sf._file, self.cachefile)
        self.assertIsNotNone(sf._fd)
        self.assertEqual(sf._type, status.LOCK_READ)
        self.assertEqual(sf.lock_type, status.LOCK_READ)
        del sf

        sf = status.SIPStatusFile(self.cachefile, status.LOCK_WRITE)
        self.assertEqual(sf._file, self.cachefile)
        self.assertIsNotNone(sf._fd)
        self.assertEqual(sf._type, status.LOCK_WRITE)
        self.assertEqual(sf.lock_type, status.LOCK_WRITE)

    def test_aquirerelease(self):
        sf = status.SIPStatusFile(self.cachefile)
        sf.acquire(status.LOCK_READ)
        self.assertEqual(sf.lock_type, status.LOCK_READ)
        sf.acquire(status.LOCK_READ)
        self.assertEqual(sf.lock_type, status.LOCK_READ)
        with self.assertRaises(RuntimeError):
            sf.acquire(status.LOCK_WRITE)
        sf.release()
        self.assertIsNone(sf.lock_type)

        sf.acquire(status.LOCK_WRITE)
        self.assertEqual(sf.lock_type, status.LOCK_WRITE)
        sf.acquire(status.LOCK_WRITE)
        self.assertEqual(sf.lock_type, status.LOCK_WRITE)
        sf.release()
        self.assertIsNone(sf.lock_type)

        with status.SIPStatusFile(self.cachefile, status.LOCK_READ) as sf:
            self.assertEqual(sf.lock_type, status.LOCK_READ)
        self.assertIsNone(sf.lock_type)

    def test_read(self):
        sf = status.SIPStatusFile(self.cachefile)
        self.assertIsNone(sf.lock_type)
        data = sf.read_data()
        self.assertIsNone(sf.lock_type)
        self.assertEqual(data, self.data)
            
        sf = status.SIPStatusFile(self.cachefile, status.LOCK_READ)
        self.assertEqual(sf.lock_type, status.LOCK_READ)
        data = sf.read_data()
        self.assertEqual(sf.lock_type, status.LOCK_READ)
        self.assertEqual(data, self.data)
            
    def test_write(self):
        data = deepcopy(self.data)
        data['goob'] = 'gurn'
        
        sf = status.SIPStatusFile(self.cachefile)
        self.assertIsNone(sf.lock_type)
        sf.write_data(data)
        self.assertIsNone(sf.lock_type)

        with open(self.cachefile) as fd:
            d = json.load(fd)
        self.assertEqual(d, data)
        self.assertIn('goob', d)
            
        sf = status.SIPStatusFile(self.cachefile, status.LOCK_WRITE)
        self.assertEqual(sf.lock_type, status.LOCK_WRITE)
        sf.write_data(data)
        self.assertEqual(sf.lock_type, status.LOCK_WRITE)
        sf.release()

        with open(self.cachefile) as fd:
            d = json.load(fd)
        self.assertEqual(d, data)
        self.assertIn('goob', d)
            
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
        status.SIPStatusFile.write(self.cachefile, self.data)

        with open(self.cachefile) as fd:
            got = json.load(fd)

        self.assertIn('goob', got)
        self.assertEqual(self.data, got)

    def testRead(self):
        with open(self.cachefile, 'w') as fd:
            json.dump(self.data, fd)

        got = status.SIPStatusFile.read(self.cachefile)
        self.assertIn('goob', got)
        self.assertEqual(self.data, got)


class TestReadWriteOld(test.TestCase):

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

    def read_data(self, filepath):
        with open(filepath) as fd:
            return json.load(fd)
    
    def test_ctor(self):
        data = {
            'user': {
                'id': 'ffff',
                'state': "forgotten",
                'message': status.user_message[status.FORGOTTEN]
            },
            'sys': {},
            'history': []
        }
        self.assertEqual(self.status.id, data['user']['id'])
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

    def test_str(self):
        self.status.update(status.PENDING, "starting soon")
        self.assertEqual(str(self.status), "ffff status: pending: starting soon")

    def test_cache(self):
        self.assertTrue(not os.path.exists(self.status._cachefile))
        self.status.data['gurn'] = 'goob'
        self.status.cache()
        self.assertTrue(os.path.exists(self.status._cachefile))

        self.assertIn('update_time', self.status.data['user'])
        self.assertTrue(isinstance(self.status.data['user']['update_time'], float))
        self.assertIn('updated', self.status.data['user'])

        data = self.read_data(self.status._cachefile)
        self.assertIn('update_time', data['user'])
        self.assertTrue(isinstance(data['user']['update_time'], float))
        self.assertIn('updated', data['user'])
        self.assertIn('gurn', data)
        self.assertEqual(data['user']['id'], 'ffff')
        self.assertEqual(data['gurn'], 'goob')
        self.assertEqual(data['user']['state'], 'forgotten')
        self.assertEqual(data['user']['message'], 
                         status.user_message[status.FORGOTTEN])

        self.status = status.SIPStatus("ffff", self.cfg)
        self.assertIn('gurn', self.status.data)
        self.assertEqual(self.status.data['gurn'], 'goob')
        self.assertEqual(self.status.data['user']['id'], 'ffff')

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

        with self.assertRaises(ValueError):
            self.status.update("hanky")

        self.status.update(status.SUCCESSFUL)
        self.assertTrue(os.path.exists(self.status._cachefile))
        self.assertEquals(self.status.data['user']['state'], 'successful')
        self.assertEqual(self.status.data['user']['message'], 
                         status.user_message[status.SUCCESSFUL])
        self.assertNotIn('start_time', self.status.data['user'])
        self.assertNotIn('started', self.status.data['user'])
        
        data = self.read_data(self.status._cachefile)
        self.assertEquals(data['user']['state'], 'successful')
        self.assertEqual(data['user']['message'], 
                         status.user_message[status.SUCCESSFUL])
        self.assertEquals(data['gurn'], 'goob')

        self.status.update(status.FAILED, "SIP is too big")
        self.assertEquals(self.status.data['user']['state'], 'failed')
        self.assertEqual(self.status.data['user']['message'], "SIP is too big")

    def test_start(self):
        self.assertTrue(not os.path.exists(self.status._cachefile))
        self.status.data['gurn'] = 'goob'

        self.status.start()
        self.assertEquals(self.status.data['user']['state'], 'in progress')
        self.assertEqual(self.status.data['user']['message'], 
                         status.user_message[status.IN_PROGRESS])
        self.assertEquals(self.status.data['gurn'], 'goob')

        self.status.update(status.FAILED)
        self.assertNotEquals(self.status.data['user']['state'], 'in progress')

        self.status.start("chugging...")
        self.assertEquals(self.status.data['user']['state'], 'in progress')
        self.assertEqual(self.status.data['user']['message'], "chugging...")

    def test_user_export(self):
        self.status.update(status.FAILED)
        self.status = status.SIPStatus.for_update('ffff', self.cfg)
        self.status.start()
        data = self.status.user_export()
        self.assertIn('id',  data)
        self.assertIn('state',  data)
        self.assertIn('history', data)
        self.assertEqual(data['id'],  'ffff')
        self.assertEqual(data['state'],  status.IN_PROGRESS)
        self.assertEqual(data['history'][0]['state'],  status.FAILED)
        
    def test_reset(self):
        self.assertEqual(self.status.state, status.FORGOTTEN)

        self.status.reset()
        self.assertEqual(self.status.state, status.PENDING)
        self.assertEqual(self.status.data['history'], [])
        
        self.status.start()
        self.status.update(status.FAILED)
        self.status.reset()
        self.assertEqual(self.status.state, status.PENDING)
        self.assertEqual(self.status.data['history'][0]['state'], status.FAILED)

        

    def test_for_update(self):
        self.status.start()
        self.status.update(status.FAILED)

        self.status = status.SIPStatus.for_update('ffff', self.cfg)
        self.assertEqual(self.status.id, 'ffff')
        self.assertEqual(self.status.data['user']['state'], status.PENDING)
        self.assertIn('update_time', self.status.data['user'])
        self.assertIn('history', self.status.data)
        history = self.status.data['history']
        self.assertEqual(len(history), 1)
        self.assertNotIn('history', history[0])
        self.assertNotIn('id', history[0])
        self.assertEqual(history[0]['state'], status.FAILED)

        self.status.update(status.SUCCESSFUL)
        self.status = status.SIPStatus.for_update('ffff', self.cfg)
        self.assertEqual(self.status.id, 'ffff')
        self.assertEqual(self.status.data['user']['state'], status.PENDING)
        self.assertIn('update_time', self.status.data['user'])
        self.assertIn('history', self.status.data)
        history = self.status.data['history']
        self.assertEqual(len(history), 2)
        self.assertNotIn('history', history[0])
        self.assertNotIn('id', history[0])
        self.assertEqual(history[0]['state'], status.SUCCESSFUL)
        self.assertNotIn('history', history[1])
        self.assertNotIn('id', history[1])
        self.assertEqual(history[1]['state'], status.FAILED)

    def test_record_progress(self):
        self.assertEquals(self.status.data['user']['state'], status.FORGOTTEN)

        self.status.record_progress("almost there")
        data = self.read_data(self.status._cachefile)
        self.assertEquals(data['user']['state'], status.FORGOTTEN)
        self.assertEquals(data['user']['message'], "almost there")

        self.status.start()
        self.status.record_progress("started")
        data = self.read_data(self.status._cachefile)
        self.assertEquals(data['user']['state'], status.IN_PROGRESS)
        self.assertEquals(data['user']['message'], "started")



        

if __name__ == '__main__':
    test.main()
