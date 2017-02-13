#!/usr/bin/python
#
import os, json, pdb
import unittest as test
import ejsonschema as ejs

nerdm = "https://www.nist.gov/od/dm/nerdm-schema/v0.1#"
nerdmpub = "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#"

schemadir = os.path.dirname(os.path.dirname(__file__))
exdir = os.path.join(schemadir, "examples")
jqlib = os.path.join(os.path.dirname(schemadir), "jq")
datadir = os.path.join(jqlib, "tests", "data")
pdlfile = os.path.join(datadir, "nist-pdl-oct2016.json")

class TestExamples(test.TestCase):

    def setUp(self):
        loader = ejs.SchemaLoader.from_directory(schemadir)
        self.val = ejs.ExtValidator(loader)

    def validate_file(self, filename):
        fpath = os.path.join(exdir, filename)
        with open(fpath) as fd:
            data = json.load(fd)

        self.val.validate(data, False, True)

    def test_validate_janaf(self):
        self.validate_file("janaf.json")

    def test_validate_hitsc(self):
        self.validate_file("hitsc.json")

    def test_validate_ceramicsportal(self):
        self.validate_file("ceramicsportal.json")

class TestSchemas(test.TestCase):

    def setUp(self):
        self.val = ejs.SchemaValidator()

    def validate_file(self, filename):
        fpath = os.path.join(schemadir, filename)
        with open(fpath) as fd:
            data = json.load(fd)

        self.val.validate(data, False, True)

    def test_nerdm(self):
        self.validate_file("nerdm-schema.json")

    def test_pub_nerdm(self):
        self.validate_file("nerdm-pub-schema.json")

        
        

if __name__ == '__main__':
    test.main()

