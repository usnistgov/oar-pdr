import pdb, os, json, urlparse, warnings
import unittest as test
from pymongo import MongoClient
from ejsonschema import ExtValidator, SchemaValidator

from nistoar.rmm.mongo import fields
from nistoar.rmm.mongo import loader

pydir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
basedir = os.path.dirname(pydir)
schemadir = os.path.join(basedir, "model")
fldschemafile = os.path.join(schemadir, "field-help-schema.json")
flddatafile = os.path.join(schemadir, "nerdm-fields-help.json")

dburl = None
if os.environ.get('MONGO_TESTDB_URL'):
    dburl = os.environ.get('MONGO_TESTDB_URL')

assert os.path.exists(schemadir), schemadir

class TestFieldsDocs(test.TestCase):

    def test_field_schema(self):
        with open(fldschemafile) as fd:
            data = json.load(fd)
        val = SchemaValidator()
        val.validate(data)
        
    def test_field_data(self):
        with open(flddatafile) as fd:
            data = json.load(fd)
        val = ExtValidator.with_schema_dir(schemadir, ejsprefix='_')
        val.validate(data, schemauri=fields.DEF_BASE_SCHEMA)

@test.skipIf(not os.environ.get('MONGO_TESTDB_URL'),
             "test mongodb not available")
class TestFieldLoader(test.TestCase):

    def setUp(self):
        self.ldr = fields.FieldLoader(dburl, schemadir)

    def tearDown(self):
        client = MongoClient(dburl)
        db = client.get_default_database()
        if "fields" in db.collection_names():
            db.drop_collection("fields")
        
    def test_ctor(self):
        self.assertEquals(self.ldr.coll, "fields")

    def test_connect(self):
        self.assertIsNone(self.ldr._client)
        self.ldr.connect()
        self.assertIsNotNone(self.ldr._client)
        self.assertEqual(self.ldr._client.get_default_database().collection_names(), [])
        self.ldr.disconnect()
        self.assertIsNone(self.ldr._client)
        
    def test_validate(self):
        data = { "name": "title", "type": "string" }
        res = self.ldr.validate(data, schemauri=fields.DEF_SCHEMA)
        self.assertEqual(res, [])

        del data['name']
        res = self.ldr.validate(data, schemauri=fields.DEF_SCHEMA)
        self.assertEqual(len(res), 1)

    def test_load_keyless_data(self):
        data = { "name": "title", "type": "string" }
        self.assertEqual(self.ldr.load_data(data), 1)
        self.assertEqual(self.ldr._client.get_default_database().fields.find().count(), 1)
        data = { "name": "title", "type": "string" }
        self.assertEqual(self.ldr.load_data(data), 1)
        self.assertEqual(self.ldr._client.get_default_database().fields.find().count(), 2)
        
    def test_load_data(self):
        key = { "name": "title" }
        data = { "name": "title", "type": "string" }
        self.assertEqual(self.ldr.load_data(data, key, 'fail'), 1)
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'string')

        data = { "name": "title", "type": "array" }
        with self.assertRaises(fields.RecordIngestError):
            self.ldr.load_data(data, key, 'fail')
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'string')
            
        data = { "name": "title", "type": "array" }
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual(self.ldr.load_data(data, key, 'warn'), 1)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, fields.UpdateWarning))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'array')
            
        data = { "name": "title", "type": "bool" }
        self.assertEqual(self.ldr.load_data(data, key, 'pass'), 1)
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'bool')
            
        key = { "name": "description" }
        data = { "name": "description", "type": "bool" }
        self.assertEqual(self.ldr.load_data(data, key, 'pass'), 1)
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 2)
        
    def test_load_simple_obj(self):
        data = { "name": "title", "type": "string" }
        res = self.ldr.load_obj(data)
        self.assertIsInstance(res, fields.LoadLog)
        self.assertEqual(res.attempt_count, 1)
        self.assertEqual(res.success_count, 1)
        self.assertEqual(res.failure_count, 0)
        self.assertTrue(res.succeeded({'name': "title"}))
        self.assertFalse(res.failed({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'string')

        data = { "name": "title", "type": "array" }
        self.ldr.load_obj(data, results=res)
        self.assertEqual(res.attempt_count, 2)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 0)
        self.assertTrue(res.succeeded({'name': "title"}))
        self.assertFalse(res.failed({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'array')
        
    def test_load_array(self):
        data = [{ "name": "title", "type": "string" },
                { "name": "description", "type": "string" },
                { "type": "bool"}]
        res = self.ldr.load_array(data)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 2)
        self.assertEquals(len(res.failures()), 1)
        
    def test_load_wrapped_array(self):
        data = {
            "fields": [{ "name": "title", "type": "string" },
                       { "name": "description", "type": "string" },
                       { "type": "bool"}]
        }
        res = self.ldr.load_obj(data)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 2)
        self.assertEquals(len(res.failures()), 1)
        
    def test_load(self):
        data = {
            "fields": [{ "name": "title", "type": "string" },
                       { "name": "description", "type": "string" },
                       { "type": "bool"}]
        }
        res = self.ldr.load(data)
        self.assertEqual(res.attempt_count, 3)
        self.assertEqual(res.success_count, 2)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 2)
        self.assertEquals(len(res.failures()), 1)
        self.assertEqual(c[0]['type'], 'string')

        data = data['fields'][:2]
        data[0]['type'] = 'array'
        data[1]['type'] = 'bool'
        self.ldr.load(data, results=res)
        self.assertEqual(res.attempt_count, 5)
        self.assertEqual(res.success_count, 4)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 2)
        self.assertNotEqual(c[0]['type'], 'string')
        self.assertNotEqual(c[1]['type'], 'string')
        
        data[0]['type'] = 'bool'
        self.ldr.load(data[0], results=res)
        self.assertEqual(res.attempt_count, 6)
        self.assertEqual(res.success_count, 5)
        self.assertEqual(res.failure_count, 1)
        self.assertTrue(res.succeeded({'name': "description"}))
        c = self.ldr._client.get_default_database().fields.find()
        self.assertEqual(c.count(), 2)
        self.assertEqual(c[0]['type'], 'bool')
        self.assertEqual(c[1]['type'], 'bool')

    def test_load_from_file(self):
        res = self.ldr.load_from_file(flddatafile)
        self.assertEqual(res.attempt_count, 32)
        self.assertEqual(res.success_count, 32)
        self.assertEqual(res.failure_count, 0)
        
        self.assertTrue(res.succeeded({'name': "title"}))
        c = self.ldr._client.get_default_database().fields.find({'name':'title'})
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['type'], 'string')
        self.assertIn('searchable', c[0]['tags'])
        
            
if __name__ == '__main__':
    test.main()
