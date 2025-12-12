"""
script to print properties that are different between two JSON metadata files
"""
import os, sys, json
import traceback as tb
from collections import OrderedDict

from . import *
import nistoar.pdr.preserv.bagger.utils as bgrutils

def cache_key_md(bagdir, mdfile, *keys):
    """
    save metadata from the specified metadata file as given by a set of top-level 
    property names.
    """
    if not os.path.isdir(bagdir):
        raise FatalError("%s: not found as a directory" % bagdir)
    if not keys:
        return
    src = os.path.join(bagdir, "metadata", mdfile)
    if not os.path.isfile(src):
        raise FatalError("%s: does not exist as a file")

    try: 
        with open(src) as fd:
            md = json.load(fd, object_pairs_hook=OrderedDict)
    except Exception as ex:
        raise FatalError("%s: Failed to read/parse as JSON: %s" % (mdfile, str(ex)))
    if not isinstance(md, OrderedDict):
        raise FatalError("%s: Does not contain a dictionary" % mdfile)

    updated = OrderedDict(p for p in md.iteritems() if p[0] in keys)

    dest = os.path.join(bagdir, "metadata", "__%s.update" % mdfile)
    try:
        with open(dest, 'w') as fd:
            json.dump(updated, fd, indent=4)
    except Exception as ex:
        raise FatalError("%s: Failed to write out modified POD as JSON: %s" %
                         (podfile, str(ex)))


def usage(prog=None, pkg=None):
    if not prog:
        prog = "cache_key_md"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s BAGDIR ID KEY [ KEY ... ]" % prog

def main(args):
    if len(args) < 2:
        raise FatalError("Missing arguments", USAGE_ERROR)
    try:
        out = cache_key_md(args[0], args[1], *args[2:])
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
