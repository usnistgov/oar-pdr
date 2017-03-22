#!/usr/bin/python
#
import os, sys, unittest, pdb

scriptdir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.dirname(scriptdir)
pydir = os.path.join(basedir, "python")
status = 0

print "Executing all tests..."

print "Executing pdr python tests..."

testpy = os.path.join(scriptdir, "testpy.py")
notok = os.system("python {0}".format(testpy))
if notok:
    print "**ERROR: some or all python unit tests failed"
    status += 2

if status:
    print("NOT OK!")
sys.exit(status)
