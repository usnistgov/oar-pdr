"""
script to print the name of the latest bag
"""
import os, sys
import traceback as tb

from . import *
import nistoar.pdr.preserv.bagger.utils as bgrutils

def latest_bag(id, cachedir):
    """
    return the full path to the latest bag with the given ID
    """
    if not os.path.isdir(cachedir):
        raise FatalError(cachedir + ": not found as a directory")

    pfx = id+"."
    bags = [f for f in os.listdir(cachedir) if f.startswith(pfx)]
    if not bags:
        raise FatalError(id +": no bags found for this ID")
    lastseq=-1
    lastbag = None
    for bag in bags:
        seq = int(bgrutils.parse_bag_name(bag)[-2])
        if seq > lastseq:
            lastseq = seq
            lastbag = os.path.join(cachedir, bag)

    if not lastbag:
        raise FatalError(id +": failed to parse bag file names to find latest")
    return lastbag

def usage(prog=None, pkg=None):
    if not prog:
        prog = "latest_bag"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s AIPID BAGCACHEDIR" % prog

def main(args):
    if len(args) < 2:
        raise FatalError("Missing arguments", USAGE_ERROR)
    try:
        print latest_bag(args[1], args[0])
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

