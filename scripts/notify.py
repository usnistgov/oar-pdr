#! /usr/bin/python
import sys, os, logging, traceback as tb
from nistoar.pdr.notify import cli

prog = os.path.basename(sys.argv[0])
if prog.endswith('.py'):
    prog = prog[:-(len('.py'))]

fmt = prog + ": %(levelname)s: %(message)s"
logging.basicConfig(format=fmt, level=logging.INFO, stream=sys.stderr)

def err(msg):
    if prog:
        sys.stderr.write(prog)
        sys.stderr.write(": ")
    sys.stderr.write(msg)
    sys.stderr.write("\n")

try:
    
    cli.main(prog, sys.argv[1:])
    
except cli.Failure as ex:
    err(str(ex))
    sys.exit(ex.exitcode)

except Exception as ex:
    # unexpected failure
    tb.print_exc()
    err(str(ex))
    sys.exit(1)
    

