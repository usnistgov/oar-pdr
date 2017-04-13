#! /usr/bin/python
#
# Usage: pdl2resources [-d DIR] [-i START] [-c COUNT] PDLFILE
#
# Extract the Dataset objects from the given PDL file, convert them to
# NERDm Resource records, and write them out into individual files.  New ARK
# identifiers will be assigned to each one.  
#
from __future__ import print_function
import os, sys, errno, json, re
from argparse import ArgumentParser
from collections import OrderedDict

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
oarpypath = os.path.join(basedir, "python")
if 'OAR_HOME' in os.environ:
    basedir = os.environ['OAR_HOME']
    oarpypath = os.path.join(basedir, "lib", "python") +":"+ \
                os.path.join(basedir, "python")
jqlib = os.path.join(basedir, "lib", "jq")
if not os.path.exists(jqlib):
    jqlib2 = os.path.join(basedir, "jq")
    if os.path.exists(jqlib2):
        jqlib = jqlib2
    
if 'OAR_PYTHONPATH' in os.environ:
    oarpypath = os.environ['OAR_PYTHONPATH']
if 'OAR_JQ_LIB' in os.environ:
    jqlib = os.environ['OAR_JQ_LIB']
if not os.path.exists(jqlib):
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

schemadir = os.path.join(basedir, "etc", "schemas")
if not os.path.exists(schemadir):
    sdir = os.path.join(basedir, "model")
    if os.path.exists(sdir):
        schemadir = sdir

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
    parser.add_argument('-T', '--fix-theme', dest='fixtheme',action='store_true',
                        help="add controlled topic values based on given themes")

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
                           format(opts.pdlfile, str(e)))
    except ValueError, e:
        raise RuntimeError("JSON Syntax error: "+str(e))

    if not pdldata.has_key('dataset'):
        raise RuntimeError("PDL catalog document is missing its 'dataset' property")
    dss = pdldata['dataset']

    if opts.start >= len(dss):
        raise RuntimeError("Not enough datasets found for requested starting record: start={0} > found={1}".format(opts.start, len(dss)))

    tax = None
    if opts.fixtheme:
        tax = load_theme_vocab()

    extracted = 0
    lim = len(dss)
    if opts.count >= 0:
        lim = opts.start + opts.count
    for i in range(opts.start, lim):
        id = minter.mint()
        basename = id[id.index("pdr0"):]
        res = cvtr.convert_data(dss[i], minter.mint())
        if opts.fixtheme:
            set_theme_as_topic(res, tax)
        with open(os.path.join(opts.odir,basename+".json"), 'w') as fd:
            json.dump(res, fd, indent=4, separators=(',', ': '))
        extracted += 1

    if not extracted:
        print("Warning: No output files written.", file=sys.stderr)

    return extracted

def load_theme_vocab():
    vocabfile = os.path.join(schemadir, "theme-taxonomy.json")
    if not os.path.exists(vocabfile):
        raise RuntimeError("Unable to find taxonomy file: "+vocabfile)

    with open(vocabfile) as fd:
        return json.load(fd)

_match_ignore = "& / and or".split()
_ignore_chars = re.compile(r"[()]")

def match_term(theme, terms):
    words = [w for w in _ignore_chars.sub('', theme).split()
               if w not in _match_ignore]

    # find the theme words in the same order
    patt = r"\b" + r"\b.*\b".join(words) + r"\b"
    matches = [t for t in terms if re.match(patt, t['term'], re.I)]

    # find the best match: pull out the matching words, the match with the least
    # left is considered the best match    
    min = 20
    best = -1
    for i,m in enumerate(matches):
        stripped = m['term']
        for word in words:
            stripped = re.sub(r'\b'+word+r'\b', '', stripped).strip()
        if len(stripped) < min:
            min = len(stripped)
            best = i

    if best >= 0:
        return matches[best]
    else:
        return None

def set_theme_as_topic(rec, tax):
    tmpl = OrderedDict([("@type", "Concept"), ("scheme", tax['@id'])])
    
    if rec.get('theme') and isinstance(rec.get('theme'), list):
        for term in rec['theme']:
            matched = match_term(term, tax['vocab'])
            if matched:
                if 'topic' not in rec:
                    rec['topic'] = []
                words=[w for w in [matched.get('parent'), matched['term']] if w]
                tag = tmpl.copy()
                tag.update( [("tag", ": ".join(words))] )
                rec['topic'].append(tag)
            

if __name__ == '__main__':
    try:
        count = main(sys.argv[1:])
        if count > 0:
            print("Wrote {0} files".format(count))
        sys.exit(0)
    except RuntimeError, e:
        print("Error: ", str(e), file=sys.stderr)
        sys.exit(1)


        
                    
