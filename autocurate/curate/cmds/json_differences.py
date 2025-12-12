"""
script to print properties that are different between two JSON metadata files
"""
import os, sys, json
import traceback as tb
from collections import OrderedDict

from . import *
import nistoar.pdr.preserv.bagger.utils as bgrutils

def json_differences(mdfile1, mdfile2):
    """
    return a list of the top level properties whose values are different between two 
    files.
    """
    if not os.path.isfile(mdfile1):
        raise FatalError("%s: not found as a file" % mdfile1)
    if not os.path.isfile(mdfile2):
        raise FatalError("%s: not found as a file" % mdfile2)

    try:
        with open(mdfile1) as fd:
            md1 = json.load(fd, object_pairs_hook=OrderedDict)
    except Exception as ex:
        raise FatalError("%s: Failed to read/parse as JSON: %s" % (mdfile1, str(ex)))
    if not isinstance(md1, OrderedDict):
        raise FatalError("%s: Does not contain a dictionary" % mdfile1)
    try:
        with open(mdfile2) as fd:
            md2 = json.load(fd, object_pairs_hook=OrderedDict)
    except Exception as ex:
        raise FatalError("%s: Failed to read/parse as JSON: %s" % (mdfile2, str(ex)))
    if not isinstance(md2, OrderedDict):
        raise FatalError("%s: Does not contain a dictionary" % mdfile2)

    diff = []
    keys1 = list(md1.keys())
    for key in keys1:
        if key not in md2 or md1[key] != md2[key]:
            diff.append(key)
    for key in md2.keys():
        if key not in keys1:
            diff.append(key)

    return diff

def usage(prog=None, pkg=None):
    if not prog:
        prog = "json_differences"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s JSONFILE JSONFILE" % prog

def main(args):
    if len(args) < 2:
        raise FatalError("Missing arguments", USAGE_ERROR)
    try:
        out = json_differences(args[0], args[1])
        if out:
            print "\n".join(out)
    except FatalError as ex:
        raise
    except Exception as ex:
        tb.print_exc()
        raise FatalError(str(ex))

if __name__ == "__main__":
    prog = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    try:
        main(sys.argv[1:])
    except FatalError as ex:
        carp(prog, str(ex))
        if ex.excode == USAGE_ERROR:
            print >> sys.stderr, "Usage:", usage(prog, __package__)
        sys.exit(ex.excode)
