import pdb, os, json, urlparse, warnings
import unittest as test
from pymongo import MongoClient
from ejsonschema import ExtValidator, SchemaValidator

from nistoar.rmm.mongo import nerdm
from nistoar.rmm.mongo import loader

pydir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
basedir = os.path.dirname(pydir)
schemadir = os.path.join(basedir, "model")
exdir = os.path.join(schemadir, "examples")
janaffile = os.path.join(exdir, "janaf.json")

dburl = None
if os.environ.get('MONGO_TESTDB_URL'):
    dburl = os.environ.get('MONGO_TESTDB_URL')

assert os.path.exists(schemadir), schemadir

@test.skipIf(not os.environ.get('MONGO_TESTDB_URL'),
             "test mongodb not available")
class TestNERDmLoader(test.TestCase):

    def setUp(self):
        self.ldr = nerdm.NERDmLoader(dburl, schemadir)

    def tearDown(self):
        client = MongoClient(dburl)
        db = client.get_default_database()
        if "record" in db.collection_names():
            db.drop_collection("record")
        
    def test_ctor(self):
        self.assertEquals(self.ldr.coll, "record")

    def test_validate(self):
        with open(janaffile) as fd:
            data = json.load(fd)
        res = self.ldr.validate(data, schemauri=nerdm.DEF_SCHEMA)
        self.assertEqual(res, [])

        del data['landingPage']
        res = self.ldr.validate(data, schemauri=nerdm.DEF_SCHEMA)
        self.assertEqual(len(res), 2)

    def test_load_data(self):
        with open(janaffile) as fd:
            data = json.load(fd)
        key = { '@id': "ark:/88434/sdp0fjspek351" }
        self.assertEqual(self.ldr.load_data(data, key, 'fail'), 1)
        c = self.ldr._client.get_default_database().record.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['@id'], 'ark:/88434/sdp0fjspek351')

    def test_load(self):
        with open(janaffile) as fd:
            data = json.load(fd)
        res = self.ldr.load(data)
        self.assertEqual(res.attempt_count, 1)
        self.assertEqual(res.success_count, 1)
        self.assertEqual(res.failure_count, 0)
        c = self.ldr._client.get_default_database().record.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['@id'], 'ark:/88434/sdp0fjspek351')

    def test_load_from_file(self):
        res = self.ldr.load_from_file(janaffile)
        self.assertEqual(res.attempt_count, 1)
        self.assertEqual(res.success_count, 1)
        self.assertEqual(res.failure_count, 0)
        c = self.ldr._client.get_default_database().record.find()
        self.assertEqual(c.count(), 1)
        self.assertEqual(c[0]['@id'], 'ark:/88434/sdp0fjspek351')

        
            
if __name__ == '__main__':
    test.main()
