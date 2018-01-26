#! /usr/bin/python
#
# Usage: ppmdserver
#
# Launch a webserver that provides NERDm metadata for datasets under construction
# in MIDAS and the PDR.  
#
from __future__ import print_function
import sys, os, traceback as tb

from nistoar.pdr.publish.mdserv import webservice as ws

bagparent = "_ppmdserver_test"+str(os.getpid())
datadir = os.path.join(os.path.dirname(
                       os.path.dirname(os.path.dirname(ws.__file__))),
                       "preserv", "tests", "data")
midasdir = os.path.join(datadir, "midassip")
revdir = os.path.join(midasdir,"review")
upldir = os.path.join(midasdir,"upload")
midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

def default_config():
    if not os.path.exists(bagparent):
        os.mkdir(bagparent)
    return {
        'working_dir':     bagparent,
        'review_dir':      revdir,
        'upload_dir':      upldir,
        'id_registry_dir': bagparent
    }

    

if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    if progname.endswith(".py"):
        progname = progname[:-3]

    print("TEST EDI-ID: "+midasid)
    try:
        ws.from_cli(sys.argv[1:], progname, default_config())
        sys.exit(0)
    except ws.ConfigurationException, e:
        print(progname + ": ", str(e), file=sys.stderr)
        sys.exit(1)
    except ws.SIPDirectoryNotFound, e:
        print(progname + ": ", str(e), file=sys.stderr)
        sys.exit(2)
    except ws.StateException, e:
        print(progname + ": ", str(e), file=sys.stderr)
        tb.print_exc(file=sys.stderr)
        sys.exit(3)
    except Exception, e:
        print(progname + ": ", str(e), file=sys.stderr)
        tb.print_exc(file=sys.stderr)
        sys.exit(4)

