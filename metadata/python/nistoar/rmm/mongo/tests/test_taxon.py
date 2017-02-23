import pdb, os, json, urlparse, warnings
import unittest as test
from pymongo import MongoClient
from ejsonschema import ExtValidator, SchemaValidator

from nistoar.rmm.mongo import taxon
from nistoar.rmm.mongo import loader

pydir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
basedir = os.path.dirname(pydir)
schemadir = os.path.join(basedir, "model")
taxschemafile = os.path.join(schemadir, "simple-taxonomy-schema.json")
taxdatafile = os.path.join(schemadir, "theme-taxonomy.json")

dburl = None
if os.environ.get('MONGO_TESTDB_URL'):
    dburl = os.environ.get('MONGO_TESTDB_URL')

assert os.path.exists(schemadir), schemadir

class TestTaxonomyDocs(test.TestCase):

    def test_tax_schema(self):
        with open(taxschemafile) as fd:
            data = json.load(fd)
        val = SchemaValidator()
        val.validate(data)
        
    def test_tax_data(self):
        with open(taxdatafile) as fd:
            data = json.load(fd)
        val = ExtValidator.with_schema_dir(schemadir, ejsprefix='_')
        val.validate(data, schemauri=taxon.DEF_BASE_SCHEMA)

@test.skipIf(not os.environ.get('MONGO_TESTDB_URL'),
             "test mongodb not available")
class TestTaxonomyLoader(test.TestCase):

    def setUp(self):
        self.ldr = taxon.TaxonomyLoader(dburl, schemadir)

    def tearDown(self):
        client = MongoClient(dburl)
        db = client.get_default_database()
        if "taxonomy" in db.collection_names():
            db.drop_collection("taxonomy")
        
    def test_ctor(self):
        self.assertEquals(self.ldr.coll, "taxonomy")

    def test_connect(self):
        self.assertIsNone(self.ldr._client)
        self.ldr.connect()
        self.assertIsNotNone(self.ldr._client)
        self.assertEqual(self.ldr._client.get_default_database().collection_names(), [])
        self.ldr.disconnect()
        self.assertIsNone(self.ldr._client)
        
    def test_validate(self):
        data = { "term": "title", "level": 1 }
        res = self.ldr.validate(data, schemauri=taxon.DEF_SCHEMA)
        self.assertEqual(res, [])

        data = { "term": "title", "level": 1, "parent": "" }
        res = self.ldr.validate(data, schemauri=taxon.DEF_SCHEMA)
        self.assertEqual(res, [])

        del data['level']
        res = self.ldr.validate(data, schemauri=taxon.DEF_SCHEMA)
        self.assertEqual(len(res), 1)

    def test_load_keyless_data(self):
        data = { "term": "title", "parent": "goob", "level": 1 }
        self.assertEqual(self.ldr.load_data(data), 1)
        self.assertEqual(self.ldr._client.get_default_database().taxonomy.find().count(), 1)
        data = { "term": "title", "parent": "goob", "level": 2 }
        self.assertEqual(self.ldr.load_data(data), 1)
        self.assertEqual(self.ldr._client.get_default_database().taxonomy.find().count(), 2)
        
    def test_load_data(self):
        key = { "term": "title", "parent": "goob" }
        data = { "term": "title", "parent": "goob", "level": 2 }
        self.assertEqual(self.ldr.load_data(data, key, 'fail'), 1)
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 2)

        data = { "term": "title", "parent": "goob", "level": 3 }
        with self.assertRaises(taxon.RecordIngestError):
            self.ldr.load_data(data, key, 'fail')
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 2)
            
        data = { "term": "title", "parent": "goob", "level": 3 }
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual(self.ldr.load_data(data, key, 'warn'), 1)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, taxon.UpdateWarning))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 3)
            
        data = { "term": "title", "parent": "goob", "level": 1 }
        self.assertEqual(self.ldr.load_data(data, key, 'pass'), 1)
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 1)
            
        key = { "term": "description", "parent": "goob" }
        data = { "term": "description", "parent": "goob", "level": 2 }
        self.assertEqual(self.ldr.load_data(data, key, 'pass'), 1)
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        
    def test_load_simple_obj(self):
        key = { "term": "title", "parent": "goob" }
        data = { "term": "title", "parent": "goob", "level": 2 }
        res = self.ldr.load_obj(data)
        self.assertIsInstance(res, taxon.LoadLog)
        self.assertEqual(res.attempt_count, 1)
        self.assertEqual(res.success_count, 1)
        self.assertEqual(res.failure_count, 0)
        self.assertTrue(res.succeeded(key))
        self.assertFalse(res.failed(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 2)
        self.assertEqual(c[0]['label'], c[0]['term'])

        data = { "term": "title", "parent": "goob", "level": 3 }
        self.ldr.load_obj(data, results=res)
        self.assertEqual(res.attempt_count, 2)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 0)
        self.assertTrue(res.succeeded(key))
        self.assertFalse(res.failed(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 3)
        
        data = { "term": "date", "level": 1 }
        self.ldr.load_obj(data, results=res)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 3)
        self.assertEqual(res.failure_count, 0)
        self.assertTrue(res.succeeded(key))
        self.assertFalse(res.failed(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        c = self.ldr._client.get_default_database().taxonomy.find({'term':'date'})
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 1)
        self.assertEqual(c[0]['parent'], "")
        self.assertEqual(c[0]['label'], "date")
        
    def test_load_array(self):
        data = [{ "term": "title", "parent": "goob", "level": 2 },
                { "term": "description", "level": 2 },
                { "parent": "goob", "level": 2 }]
        key = { "term": "title", "parent": "goob" }

        res = self.ldr.load_array(data)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        self.assertEquals(len(res.failures()), 1)
        
    def test_load_wrapped_array(self):
        data = {
            "vocab": [{ "term": "title", "parent": "goob", "level": 2 },
                      { "term": "description", "level": 2 },
                      { "parent": "goob", "level": 2 }]
        }
        key = { "term": "title", "parent": "goob" }

        res = self.ldr.load_obj(data)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        self.assertEquals(len(res.failures()), 1)
        
    def test_load(self):
        data = {
            "vocab": [{ "term": "title", "parent": "goob", "level": 2 },
                      { "term": "description", "level": 2 },
                      { "parent": "goob", "level": 2 }]
        }
        key = { "term": "title", "parent": "goob" }

        res = self.ldr.load(data)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        self.assertEquals(len(res.failures()), 1)
        self.assertEqual(c[0]['parent'], 'goob')
        self.assertEqual(c[0]['level'], 2)

        data = data['vocab'][:2]
        data[0]['level'] = 3
        data[1]['level'] = 1
        self.ldr.load(data, results=res)
        self.assertEqual(res.attempt_count, 5)
        self.assertEqual(res.success_count, 4)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        self.assertNotEqual(c[0]['level'], 2)
        self.assertNotEqual(c[1]['level'], 2)
        
        data[0]['level'] = 1
        self.ldr.load(data[0], results=res)
        self.assertEqual(res.attempt_count, 6)
        self.assertEqual(res.success_count, 5)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded(key))
        c = self.ldr._client.get_default_database().taxonomy.find()
        self.assertEqual(c.count(), 2)
        self.assertEqual(c[0]['level'], 1)
        self.assertEqual(c[1]['level'], 1)

    def test_load_from_file(self):
        res = self.ldr.load_from_file(taxdatafile)
        self.assertEqual(res.attempt_count, 249)
        self.assertEqual(res.success_count, 249)
        self.assertEqual(res.failure_count, 0)

        key = {'term': "Advanced Communications", "parent": ""}
        self.assertTrue(res.succeeded(key))
        c = self.ldr._client.get_default_database().taxonomy.find(key)
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['level'], 1)
        
            
if __name__ == '__main__':
    test.main()
