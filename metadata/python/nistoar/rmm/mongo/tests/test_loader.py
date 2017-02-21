import pdb, os, json
import unittest as test

from nistoar.rmm.mongo import loader 

class TestLoadResult(test.TestCase):

    def test_ctor(self):
        res = loader.LoadResult({"name": "bob"}, ["err1", "err2"])
        self.assertEqual(res.key['name'], 'bob')
        self.assertTrue( isinstance(res.errs, list) )
        self.assertEqual(len(res.errs), 2)
        self.assertTrue("err1" in res.errs)
        self.assertTrue("err2" in res.errs)
        self.assertFalse(res.successful)

    def test_notsuccess(self):
        res = loader.LoadResult({"name": "bob"})
        self.assertEqual(res.key['name'], 'bob')
        self.assertIsNone(res.errs)
        self.assertTrue(res.successful)

class TestLoadLog(test.TestCase):

    def test_ctor(self):
        res = loader.LoadLog("test")
        self.assertEqual(res.description, "test")
        self.assertEqual(res.attempt_count, 0)
        self.assertEqual(res.failure_count, 0)
        self.assertEqual(res.success_count, 0)
        self.assertFalse(res.succeeded({"name": "bob"}))
        self.assertFalse(res.failed({"name": "bob"}))
        self.assertEqual(res.failures({"name": "bob"}), [])

    def test_add(self):
        res = loader.LoadLog("test")
        r = res.add({"name": "bob"})
        self.assertIs(r, res)
        self.assertEqual(res.attempt_count, 1)
        self.assertEqual(res.failure_count, 0)
        self.assertEqual(res.success_count, 1)
        self.assertTrue(res.succeeded({"name": "bob"}))
        self.assertFalse(res.failed({"name": "bob"}))
        self.assertEqual(res.failures({"name": "bob"}), [])
        
        r = res.add({"name": "bob"}, "epic fail")
        self.assertIs(r, res)
        self.assertEqual(res.attempt_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertEqual(res.success_count, 1)
        self.assertTrue(res.succeeded({"name": "bob"}))
        self.assertTrue(res.failed({"name": "bob"}))
        self.assertEqual(res.failures({"name": "bob"})[0].errs, ["epic fail"])
        


            
if __name__ == '__main__':
    test.main()
