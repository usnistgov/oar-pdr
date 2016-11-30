#!/usr/bin/python
#
import os, sys, unittest, pdb

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jqlib = os.path.join(basedir, "jq")
testdir = os.path.join(jqlib, "tests")
jqtest = os.path.join(testdir, "test_pod2nerdm.jqt")
nerdmtest = os.path.join(testdir, "test_podds2resource.py")
pydir = os.path.join(basedir, "python")

print "Executing all tests..."

print "Executing jq translation library tests..."

status = 0
notok = os.system("jq -L {0} --run-tests {1}".format(jqlib, jqtest))
if notok:
    print "**ERROR: some or all jq tests have failed"
    status += 1

print "Executing validation tests..."

notok = os.system("python {0}".format(nerdmtest))
if notok:
    print "**ERROR: some or all validation tests have failed"
    status += 2

print "Executing nistoar python tests..."

ldr = unittest.TestLoader()
suite = ldr.discover(pydir, "test_*.py")
unittest.TextTestRunner().run(suite)

sys.exit(status)

