#! /usr/bin/env python
#
from __future__ import print_function
import os, sys, traceback as tb
from argparse import ArgumentParser

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
oarpypath = os.path.join(basedir, "python")
if 'OAR_HOME' in os.environ:
    basedir = os.environ['OAR_HOME']
    oarpypath = os.path.join(basedir, "lib", "python") +":"+ \
                os.path.join(basedir, "python")

if 'OAR_PYTHONPATH' in os.environ:
    oarpypath = os.environ['OAR_PYTHONPATH']

sys.path.extend(oarpypath.split(os.pathsep))
try:
    import nistoar
except ImportError, e:
    nistoardir = os.path.join(basedir, "python")
    sys.path.append(nistoardir)
    import nistoar

import nistoar.pdr.preserv.bagit as bagit
import nistoar.pdr.preserv.bagit.validate as vald8
from nistoar.pdr.exceptions import (PDRException, StateException)

prog = os.path.basename(sys.argv[0])
if not prog or prog == 'python':
    prog = "validate_bag"

description = \
"""validate that a bag is compliant with the NIST bag profile"""

epilog = None

def define_opts(progname=None):
    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('bagdir', metavar='BAGDIR', type=str,
                        help="the root directory of the bag to validate")

    return parser

def main(args):
    parser = define_opts()
    opts = parser.parse_args(args)
    config = {}

    bag = bagit.NISTBag(opts.bagdir)

    vld8r = vald8.NISTAIPValidator(config)
    results = vld8r.validate(bag)

    issues = results.failed(results.PROB)

    if len(issues):
        for iss in issues:
            print(iss.description)
        print(os.path.basename(opts.bagdir), "is not valid.")
    else:
        print(os.path.basename(opts.bagdir), "is valid!")
            

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
        sys.exit(0)
    except PDRException as e:
        print(prog+":", str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(prog+":", repr(e), file=sys.stderr)
        tb.print_exc()
        sys.exit(10)
