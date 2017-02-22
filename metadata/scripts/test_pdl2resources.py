#!/usr/bin/python
#
from __future__ import print_function

import os, pdb, sys, shutil
import unittest as test
import ejsonschema as ejs

datadir = os.path.join(os.path.dirname(os.path.dirname(
                                                    os.path.abspath(__file__))),
                       "jq", "tests", "data")
pdlfile = os.path.join(datadir, "nist-pdl-oct2016.json")

tmpname = "_test"
basedir = os.getcwd()
tmpdir = os.path.join(basedir, tmpname)
outdir = os.path.join(tmpdir, "nerdmrecs")
errdir = os.path.join(tmpdir, "errors")
scriptdir = os.path.dirname(__file__)
cvtscript = os.path.join(scriptdir, "pdl2resources.py")
schemadir = os.path.join(os.path.dirname(scriptdir), "model")

class TestConvert(test.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.isdir(outdir):
            if not os.path.isdir(tmpdir):
                os.mkdir(tmpdir)
            os.mkdir(outdir)
        os.makedirs(errdir)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

    def setUp(self):
        self.val = ejs.ExtValidator.with_schema_dir(schemadir, ejsprefix='_')

    
    def test_convert(self):
        script = "python {0} -d {1} {2}".format(cvtscript, outdir, pdlfile)
        self.assertEquals(os.system(script), 0)

        files = [f for f in os.listdir(outdir) if f.endswith(".json")]
        failed = []
        passed = 0
        for f in files:
            nf = os.path.join(outdir, f)
            errs = self.val.validate_file(nf, raiseex=False)
            if len(errs) > 0:
                failed.append(f)
                with open(os.path.join(errdir, f), 'w') as fd:
                    for err in errs:
                        print(str(err), file=fd)
            else:
                sys.stderr.write(".")
                passed += 1

        sys.stderr.write("\nValidated {0} files".format(str(passed)))
        self.assertEquals(len(failed), 0,
                          "{0} converted file(s) failed validation")

        

if __name__ == '__main__':
    test.main()

