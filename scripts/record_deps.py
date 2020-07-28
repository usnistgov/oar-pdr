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
import os, sys, json, re
from collections import OrderedDict
import subprocess as subproc
import traceback as tb

prog = os.path.basename(sys.argv[0])
execdir = os.path.dirname(sys.argv.pop(0))
pkgdir = os.path.dirname(execdir)
pkgname = os.environ.get('PACKAGE_NAME', 'oar-pdr')
# targetdir = os.path.join(pkgdir, "target")
targetdir = sys.argv[2]

def usage():
    print("Usage: %s DISTNAME VERSION" % prog, file=sys.stderr)

def fail(msg, excode=1):
    print(prog + ": " + msg, file=sys.stderr)
    sys.exit(excode)


class parse_artifact(object):
    def __init__(self, artstr):
        if ':' not in artstr:
            raise ValueError("Not an artifact string: "+artstr)
        parts = artstr.split(':')
        self.groupid = parts[0]
        self.artifactid = parts[1]
        self.type = parts[2]
        self.version = parts[3]
        self.neededfor = (len(parts) > 4 and parts[4]) or None

def parse_deptree(depfile, compname=None):
    flre = re.compile(r'digraph "([^"]*)" {')
    depre = re.compile(r'\s*"([^"]*)" -> "([^"]*)"')
    endre = re.compile(r'\s*}')

    deps = OrderedDict()
    with open(depfile) as fd:
        m = flre.match(fd.readline())
        if not m:
            raise ValueError("file contents not in DOT (directed graph) format")
        compstr = m.group(1)
        comp = parse_artifact(compstr)
        if compname and comp.artifactid != compname:
            raise ValueError("Unexpected component described: "+comp.artifactid)

        for line in fd:
            m = depre.match(line)
            if m:
                depfor = m.group(1)
                if depfor not in deps:
                    deps[depfor] = []
                deps[depfor].append(m.group(2))
                line = line[m.end():]
            m = endre.match(line)
            if m:
                break

    return depsfor(compstr, deps)

def depsfor(artstr, lookup):
    out = OrderedDict()
    if artstr in lookup:
        for dep in lookup[artstr]:
            comp = parse_artifact(dep)
            name = comp.groupid+':'+comp.artifactid
            out[name] = OrderedDict([
                ("version", comp.version),
                ("artifacttype", comp.type)
            ])
            if comp.neededfor:
                out[name]['neededfor'] = comp.neededfor
            if dep in lookup:
                out[name]['dependencies'] = depsfor(dep, lookup)
    return out

def make_depdata(compname, pkgver):
    depfile = os.path.join(targetdir, "deptree.dot")
    if not os.path.exists(depfile):
        raise RuntimeError("Missing deptree file: "+depfile)
    deps = OrderedDict([
        (pkgname, OrderedDict([ ("version", pkgver) ]))
    ])
    deps.update(parse_deptree(depfile, compname))

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

try: 
    data = make_depdata(distname, distvers)
    json.dump(data, sys.stdout, indent=2)
except ValueError as ex:
    fail(str(ex), 2)

