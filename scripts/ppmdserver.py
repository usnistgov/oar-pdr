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

if __name__ == '__main__':
    progname = os.path.basename(sys.argv[0])
    if progname.endswith(".py"):
        progname = progname[:-3]
        
    try:
        ws.from_cli(sys.argv[1:])
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

