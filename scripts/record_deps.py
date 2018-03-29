#! /usr/bin/python
#
# record_deps.py -- encode the dependencies of a distribution as JSON object,
#                   writing it to standard output.
#
# Usage:  record_deps.py DISTNAME VERSION PACKAGE_LOCK_FILE NPMVERSION
#
# where,
#   DISTNAME            the name of the distribution the dependencies apply to
#   VERSION             the version of the distribution 
#
# The default package name (oar-sdp) can be over-ridden by the environment
# variable PACKAGE_NAME
#
from __future__ import print_function
import os, sys, json
from collections import OrderedDict
import subprocess as subproc
import traceback as tb

prog = os.path.basename(sys.argv[0])
execdir = os.path.dirname(sys.argv.pop(0))
pkgdir = os.path.dirname(execdir)
omddir = os.path.join(pkgdir, "oar-metadata")
omdscr = os.path.join(omddir, "scripts")
pkgname = os.environ.get('PACKAGE_NAME', 'oar-pdr')

def usage():
    print("Usage: %s DISTNAME VERSION" % prog, file=sys.stderr)

def fail(msg, excode=1):
    print(prog + ": " + msg, file=sys.stderr)
    sys.exit(excode)

def oarmvers():
    namever = ["oar-metadata", "(unknown)"]
    try:
        with open(os.path.join(omddir, "VERSION")) as fd:
            namever = fd.readline().strip().split(1)
    except Exception:
        pass
    return namever

def oarmddep():
    oarmnv = oarmvers()
    cmd = [ os.path.join(omdscr, "record_deps.py"), oarmnv[0], oarmnv[1] ]
    try:
        depdata = json.loads(subproc.check_output(cmd),
                             object_pairs_hook=OrderedDict)
        deps = depdata['dependencies']
    except Exception as ex:
        tb.print_exc()
        deps = OrderedDict([
            ("oar-metadata", OrderedDict([
                ("version", "(unknown)"), ("comment",
                 "Warning: unable to determine oar-metadata dependencies")
            ]))
        ])

    return deps

def make_depdata(compname, pkgver):
    deps = OrderedDict([
        (pkgname, OrderedDict([ ("version", pkgver) ]))
    ])
    deps.update(oarmddep())
    data = OrderedDict([
        ("name", compname),
        ("version", pkgver),
        ("dependencies", deps)
    ])
    return data

if len(sys.argv) < 2:
    usage()
    fail("Missing arguments -- need 2")
    
distname = sys.argv.pop(0)
distvers = sys.argv.pop(0)
    
data = make_depdata(distname, distvers)
json.dump(data, sys.stdout, indent=2)

