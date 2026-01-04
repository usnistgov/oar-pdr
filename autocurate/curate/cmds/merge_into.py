"""
script to print properties that are different between two JSON metadata files
"""
import os, sys, json
import traceback as tb
from collections import OrderedDict

from nistoar.pdr.utils import read_nerd, NERDError, write_json
from . import *

def merge_into(srcf, destf):
    try: 
        src = read_nerd(srcf)
        dest = read_nerd(destf)
        dest.update(src)

        write_json(dest, destf)
    except NERDError as ex:
        raise FatalError(str(ex))
    except Exception as ex:
        tb.print_exc()
        raise FatalError("Trouble merging %s: %s" % (srcf, str(ex)), 2)

def usage(prog=None, pkg=None):
    if not prog:
        prog = "merge_into"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s SRCFILE DESTFILE" % prog

def main(args):
    if len(args) < 2:
        raise FatalError("Missing arguments", USAGE_ERROR)
    try:
        merge_into(args[0], args[1])
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

        

