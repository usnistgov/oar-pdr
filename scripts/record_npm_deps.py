#! /usr/bin/python
#
# record_npm_deps.py -- encode the dependencies of a distribution as JSON object,
#                       writing it to standard output.
#
# Usage:  record_npm_deps.py DISTNAME VERSION PACKAGE_LOCK_FILE NPMVERSION
#
# where,
#   DISTNAME            the name of the distribution the dependencies apply to
#   VERSION             the version of the distribution 
#   PACKAGE_LOCK_FILE   the package-lock.json produced by npm containing
#                         dependencies it manages
#   NPMVERSION          the version of npm used to build the distribution
#
# The default package name (oar-sdp) can be over-ridden by the environment
# variable PACKAGE_NAME
#
from __future__ import print_function
import os, sys, json
from collections import OrderedDict

prog = os.path.basename(sys.argv.pop(0))
pkgname = os.environ.get('PACKAGE_NAME', 'oar-sdp')

def fail(msg, excode=1):
    print(prog + ": " + msg, file=sys.stderr)
    sys.exit(excode)

def usage():
    print("%s DISTNAME VERSION PACKAGE_LOCK_FILE NPMVERSION" % prog,
          file=sys.stderr)

if len(sys.argv) < 4:
    usage()
    fail("Missing argument(s) -- need four.")

distname = sys.argv.pop(0)
vers = sys.argv.pop(0)
pkgfile = sys.argv.pop(0)
npmvers = sys.argv.pop(0)

if not os.path.exists(pkgfile):
    fail(pkgfile + ": file not found", 2)

npmdep = OrderedDict([("version", npmvers)])
repodep = OrderedDict([("version", vers)])

with open(pkgfile) as fd:
    data = json.load(fd, object_pairs_hook=OrderedDict)

data['name'] = distname
data['version'] = vers

data['dependencies'] = OrderedDict([(pkgname, repodep), ("npm", npmdep)] +
                                   data.get('dependencies', {}).items())

json.dump(data, sys.stdout, indent=2)
