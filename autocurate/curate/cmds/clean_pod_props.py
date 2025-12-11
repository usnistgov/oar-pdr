"""
script to remove pdr-specific properties (like "_preserve") from a pod file
"""
import os, sys, json
import traceback as tb
from collections import OrderedDict

from . import *
import nistoar.pdr.preserv.bagger.utils as bgrutils

def clean_pod_props(podfile):
    """
    read and then overwrite a POD file, removing all properties starting with "_".  
    The includes in particular "_preserve".
    """
    if not os.path.isfile(podfile):
        raise FatalError("%s: not found as a file" % podfile)

    try:
        with open(podfile) as fd:
            pod = json.load(fd, object_pairs_hook=OrderedDict)
    except Exception as ex:
        raise FatalError("%s: Failed to read/parse as JSON: %s" % (podfile, str(ex)))
    if not isinstance(pod, OrderedDict):
        raise FatalError("%s: Does not contain a dictionary" % poddfile)

    altered = False
    for key in pod:
        if key.startswith("_"):
            altered = True
            del pod[key]

    if not altered:
        return

    try:
        with open(podfile, 'w') as fd:
            json.dump(pod, fd, indent=4)
    except Exception as ex:
        raise FatalError("%s: Failed to write out modified POD as JSON: %s" %
                         (podfile, str(ex)))

def usage(prog=None, pkg=None):
    if not prog:
        prog = "clean_pod_props"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s JSONFILE" % prog

def main(args):
    if len(args) < 1:
        raise FatalError("Missing POD file name", USAGE_ERROR)
    try:
        clean_pod_props(args[0])
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
    
    
