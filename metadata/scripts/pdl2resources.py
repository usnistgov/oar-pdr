#! /usr/bin/python
#
# Usage: pdl2resources [-d DIR] [-i START] [-c COUNT] PDLFILE
#
# Extract the Dataset objects from the given PDL file, convert them to
# NERDm Resource records, and write them out into individual files.  New ARK
# identifiers will be assigned to each one.  
#

import os, sys, errno, json
from argparse import ArgumentParser
from nistoar.nerdm.convert import PODds2Res

prog = os.path.basename(sys.argv[0])
if not prog or prog == 'python':
    prog = "pdl2resources"

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jqlib = os.path.join(basedir, "jq")
IDSEQ = 2000

description = \
"""convert PDL Datasets to NERDm Resource records"""

epilog = None

def define_opts(progname=None):
    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('pdlfile', metavar='PDLFILE', type=str, nargs=1,
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
        with open(opts.file) as fd:
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

    lim = len(dss)
    if opts.count >= 0:
        lim = start + opts.count
    for i in range(start, lim):
        id = minter.mint()
        basename = id[id.index("pdr0"):]
        res = cvtr.convert_data(dss[i], minter.mint())
        with open(os.path.join(opts.dir,basename+".json"), 'w') as fd:
            json.dump(fd, res)


        
                    
