#! /usr/bin/python
#
# Usage: pdl2resources [-d DIR] [-i START] [-c COUNT] PDLFILE
#
# Extract the Dataset objects from the given PDL file, convert them to
# NERDm Resource records, and write them out into individual files.  New ARK
# identifiers will be assigned to each one.  
#
from __future__ import print_function
import os, sys, errno, json
from argparse import ArgumentParser

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
oarpypath = os.path.join(basedir, "python")
if 'OAR_HOME' in os.environ:
    basedir = os.environ['OAR_HOME']
    oarpypath = os.path.join(basedir, "python")
    jqlib = os.path.join(basedir, "lib", "jq")
    
if 'OAR_PYTHONPATH' in os.environ:
    oarpypath = os.environ['OAR_PYTHONPATH']
if 'OAR_JQ_LIB' in os.environ:
    jqlib = os.environ['OAR_JQ_LIB']
else:
    print("jq library location is unknown; please, set the OAR_HOME or "
          "OAR_JQ_LIB environment variable", file=sys.stderr)
    sys.exit(10)

sys.path.extend(oarpypath.split(os.pathsep))
try:
    import nistoar
except ImportError, e:
    nistoardir = os.path.join(basedir, "python")
    sys.path.append(nistoardir)
    import nistoar

from nistoar.nerdm.convert import PODds2Res
from nistoar.id.minter import PDRMinter

prog = os.path.basename(sys.argv[0])
if not prog or prog == 'python':
    prog = "pdl2resources"

IDSEQ = 2000

description = \
"""convert PDL Datasets to NERDm Resource records"""

epilog = None

def define_opts(progname=None):
    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('pdlfile', metavar='PDLFILE', type=str,
                        help="the PDL POD catalog document")
    parser.add_argument('-d', '--output-directory', type=str, dest='odir',
                        metavar='DIR', default='.',
      help="the directory to write output files to (default: current directory)")
    parser.add_argument('-i', '--start', metavar='START', type=int, dest='start',
                        help="skip the first START Dataset records found",
                        default=0)
    parser.add_argument('-c', '--count', metavar='COUNT', type=int, dest='count',
                        help="export no more than COUNT records", default=-1)

    return parser

def main(args):
    parser = define_opts()
    opts = parser.parse_args(args)

    seq = IDSEQ + opts.start
    minter = PDRMinter(seq, 'pdr0')
    cvtr = PODds2Res(jqlib)

    try:
        with open(opts.pdlfile) as fd:
            pdldata = json.load(fd)
    except IOError, e:
        raise RuntimeError("Unable to read PDL file ({0}): {1}".
                           format(opts.file, str(e)))
    except ValueError, e:
        raise RuntimeError("JSON Syntax error: "+str(e))

    if not pdldata.has_key('dataset'):
        raise RuntimeError("PDL catalog document is missing its 'dataset' property")
    dss = pdldata['dataset']

    if opts.start >= len(dss):
        raise RuntimeError("Not enough datasets found for requested starting record: start={0} > found={1}".format(opts.start, len(dss)))

    extracted = 0
    lim = len(dss)
    if opts.count >= 0:
        lim = opts.start + opts.count
    for i in range(opts.start, lim):
        id = minter.mint()
        basename = id[id.index("pdr0"):]
        res = cvtr.convert_data(dss[i], minter.mint())
        with open(os.path.join(opts.odir,basename+".json"), 'w') as fd:
            json.dump(res, fd, indent=4, separators=(',', ': '))
        extracted += 1

    if not extracted:
        print("Warning: No output files written.", file=sys.stderr)

    return extracted

if __name__ == '__main__':
    try:
        count = main(sys.argv[1:])
        if count > 0:
            print("Wrote {0} files".format(count))
        sys.exit(0)
    except RuntimeError, e:
        print("Error: ", str(e), file=sys.stderr)
        sys.exit(1)


        
                    
