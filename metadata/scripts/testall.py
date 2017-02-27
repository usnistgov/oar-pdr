#!/usr/bin/python
#
import os, sys, unittest, pdb

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jqlib = os.path.join(basedir, "jq")
testdir = os.path.join(jqlib, "tests")
jqtest = os.path.join(testdir, "test_pod2nerdm.jqt")
nerdmtest = os.path.join(testdir, "test_podds2resource.py")
pdltest = os.path.join(basedir, "scripts", "test_pdl2resources.py")
extest = os.path.join(basedir, "model", "tests", "test_examples.py")
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
    print "**ERROR: some or all basic validation tests have failed"
    status += 2
notok = os.system("python {0}".format(extest))
if notok:
    print "**ERROR: some or all example files have failed validation"
    status += 4
notok = os.system("python {0}".format(pdltest))
if notok:
    print "**ERROR: some or all pdl2resources output files have failed validation"
    status += 8

print "Executing nistoar python tests..."

ldr = unittest.TestLoader()
suite = ldr.discover(pydir, "test_*.py")
unittest.TextTestRunner().run(suite)

if status:
    print("NOT OK!")
sys.exit(status)

