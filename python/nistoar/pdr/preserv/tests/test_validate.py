import os, pdb
import warnings as warn
import unittest as test
from collections import OrderedDict

import nistoar.pdr.preserv.validate as val
import nistoar.pdr.preserv.exceptions as exceptions

datadir = os.path.join(os.path.dirname(__file__), "data")

class TestAssessment(test.TestCase):

    def test_noctr(self):
        with self.assertRaises(TypeError):
            validater = val.Assessment("goob")

class TestSimpleAssessment(test.TestCase):

    def test_ctr(self):
        a = val.SimpleAssessment()
        self.assertEqual(a.description, "")
        self.assertTrue(a.valid)
        
        a = val.SimpleAssessment("goob")
        self.assertEqual(a.description, "goob")
        self.assertTrue(a.valid)
        
        a = val.SimpleAssessment("goob", False)
        self.assertEqual(a.description, "goob")
        self.assertFalse(a.valid)

        self.assertEquals(a.recs(), [])
        self.assertEquals(a.warnings(), [])
        self.assertEquals(a.errors(), [])

    def test_invalidate(self):
        a = val.SimpleAssessment()
        self.assertTrue(a.valid)

        a.invalidate()
        self.assertFalse(a.valid)

    def test_messages(self):
        a = val.SimpleAssessment()
        a.add_rec("buy!")
        a.add_rec(["sell!", "stay!"])
        self.assertEqual(a.recs(), ["buy!", "sell!", "stay!"])

        a.add_warning("sell!")
        a.add_warning(["stay!", "buy!"])
        self.assertEqual(a.warnings(), ["sell!", "stay!", "buy!"])

        a.add_error("sell!")
        a.add_error(["buy!", "stay!"])
        self.assertEqual(a.errors(), ["sell!", "buy!", "stay!"])

        self.assertEqual(a.messages(), { "recs": ["buy!", "sell!", "stay!"],
                                         "warnings": ["sell!", "stay!", "buy!"],
                                         "errors": ["sell!", "buy!", "stay!"] })

    def test_config(self):
        a = val.SimpleAssessment()
        self.assertEqual(a.keys(), [])

        a['indir'] = "/data/dataset"
        self.assertIn('indir', a)
        self.assertEqual(a.get('indir'), "/data/dataset")
        self.assertEqual(a['indir'], "/data/dataset")

        
    def test_ops(self):
        a = val.SimpleAssessment()
        self.assertNotIn('ops', a)
        
        self.assertIsInstance(a.ops, OrderedDict)
        self.assertEqual(len(a.ops), 0)
        self.assertIn('ops', a)
        
        a.add_op("bagged", {  })
        self.assertIsInstance(a.ops, OrderedDict)
        self.assertEqual(len(a.ops), 1)
        self.assertIn('bagged', a.ops)

class TestAggregatedAssessment(test.TestCase):

    def test_ctr(self):
        a = val.AggregatedAssessment()
        self.assertEqual(a.description, "")
        self.assertTrue(a.valid)
        
        a = val.AggregatedAssessment("goob")
        self.assertEqual(a.description, "goob")
        self.assertTrue(a.valid)
        
        self.assertEquals(a.recs(), [])
        self.assertEquals(a.warnings(), [])
        self.assertEquals(a.errors(), [])

    def test_config(self):
        a = val.AggregatedAssessment()
        self.assertEqual(a.keys(), [])

        a['indir'] = "/data/dataset"
        self.assertIn('indir', a)
        self.assertEqual(a.get('indir'), "/data/dataset")
        self.assertEqual(a['indir'], "/data/dataset")

    def test_ops(self):
        aa = val.AggregatedAssessment()
        self.assertNotIn('ops', aa)
        
        self.assertIsInstance(aa.ops, OrderedDict)
        self.assertEqual(len(aa.ops), 0)
        self.assertIn('ops', aa)
        
        a = val.SimpleAssessment()
        aa.add_delegated("goob", a)
        self.assertEqual(len(aa.ops), 1)
        self.assertEqual(len(aa.delegated), 1)
        self.assertTrue(aa.ops['goob'].valid)
        self.assertTrue(aa.valid)
    
        a = val.SimpleAssessment()
        aa.add_delegated("gomer", a)
        self.assertEqual(len(aa.ops), 2)
        self.assertEqual(len(aa.delegated), 2)
        self.assertTrue(aa.ops['gomer'].valid)
        self.assertTrue(aa.valid)

        aa.ops["go"] = {"when", "now"}
        self.assertEqual(len(aa.ops), 3)
        self.assertEqual(len(aa.delegated), 2)
        self.assertFalse(hasattr(aa.ops['go'], 'valid'))
        self.assertTrue(aa.valid)
    
        a.invalidate()
        self.assertFalse(a.valid)
        self.assertFalse(aa.valid)
        
    def test_messages(self):
        aa = val.AggregatedAssessment()
        self.assertNotIn('ops', aa)
        
        a = val.SimpleAssessment()
        a.add_rec("buy!")
        a.add_rec(["sell!", "stay!"])
        self.assertEqual(a.recs(), ["buy!", "sell!", "stay!"])
        aa.add_delegated("goob", a)

        a = val.SimpleAssessment()
        a.add_rec("sell!")
        a.add_rec(["stay!", "buy!"])
        self.assertEqual(a.recs(), ["sell!", "stay!", "buy!"])
        aa.add_delegated("gurn", a)

        self.assertEqual(aa.recs(), ["buy!", "sell!", "stay!",
                                     "sell!", "stay!", "buy!"])
    

class TestValidater(test.TestCase):

    def test_noctr(self):
        with self.assertRaises(TypeError):
            validater = val.Validater("goob")

class TestTrivialPrervationValidater(test.TestCase):

    def test_validate(self):
        indir = datadir

        # validater = val.PreservationValidater(datadir)
        with warn.catch_warnings(record=True) as w:
            validater = val.PreservationValidater(datadir)
            self.assertEqual( len(w), 1 )
            self.assertTrue(issubclass(w[0].category,exceptions.ConfigurationWarning))

        out = validater.validate()
        self.assertIsInstance(out, val.Assessment)
        self.assertTrue(out.valid)

    def test_badvalidater(self):
        validater = val.PreservationValidater(datadir, {'goob': 'hank'})
        with self.assertRaises(exceptions.ConfigurationException):
            out = validater.validate()



if __name__ == '__main__':
    test.main()
    
