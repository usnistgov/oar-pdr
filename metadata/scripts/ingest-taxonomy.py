#! /usr/bin/python
#
# Usage: ingest-taxonomy.py [-V] TAXONOMYFILE
#
# Load the taxonomy terms from a file into the MongoDB 'taxonomy' collections.
#
from __future__ import print_function
import os, sys, errno, json, re, warnings
from argparse import ArgumentParser

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
oarpypath = os.path.join(basedir, "python")
if 'OAR_HOME' in os.environ:
    basedir = os.environ['OAR_HOME']
    oarpypath = os.path.join(basedir, "lib", "python") +":"+ \
                os.path.join(basedir, "python")
schemadir = os.path.join(basedir, "etc", "schemas")
if not os.path.exists(schemadir):
    sdir = os.path.join(basedir, "model")
    if os.path.exists(sdir):
        schemadir = sdir
    
if 'OAR_PYTHONPATH' in os.environ:
    oarpypath = os.environ['OAR_PYTHONPATH']

sys.path.extend(oarpypath.split(os.pathsep))
try:
    import nistoar
except ImportError, e:
    nistoardir = os.path.join(basedir, "python")
    sys.path.append(nistoardir)
    import nistoar

from nistoar.rmm.mongo.taxon import (TaxonomyLoader, LoadLog, RecordIngestError,
                                     JSONEncodingError)

description = \
"""ingest taxonomy terms into the RMM"""

epilog = None

def define_opts(progname=None):
    parser = ArgumentParser(progname, None, description, epilog)
    parser.add_argument('taxfile', metavar='TAXONOMYFILE', type=str, nargs='+',
                        help="the JSON file containing the taxonomy")
    parser.add_argument('-V', '--skip-validate', dest='validate', default=True,
                        action="store_false",
                        help="do not attempt to validate the records before "+
                             "ingesting them")
    parser.add_argument('-q', '--quiet', dest='quiet', default=False,
                        action="store_true",
                        help="do not print non-fatal status messages")
    parser.add_argument('-s', '--silent', dest='silent', default=False,
                        action="store_true", help="print no messages at all")
    parser.add_argument('-U', '--warn-update', dest='warn', default=False,
                        action="store_true", help="print a warning message if "+
                               "one or more records overwrite/update previous "+
                               "existing records")
    parser.add_argument('-M', '--mongodb-url', metavar='URL',type=str,dest='url',
                        action='store', default="mongodb://mongodb:3333/TestDB",
                        help="the URL to the MongoDB database to load into (in "+
                             "the form 'mongodb://HOST:PORT/DBNAME'")

    return parser

def main(args):
    parser = define_opts()
    opts = parser.parse_args(args)
    if opts.silent:
        opts.quiet = True

    stat = 0
    loader = TaxonomyLoader(opts.url, schemadir)
    if opts.warn and not opts.quiet:
        loader.onupdate = 'warn'
        warnings.simplefilter("once")
    totres = LoadLog()

    for taxfile in opts.taxfile:
        validate = opts.validate

        try:
            with open(taxfile) as fd:
                doc = json.load(fd)
        except ValueError, ex:
            stat = 1
            totres.add(taxfile, [ JSONEncodingError(ex) ])
            if not opts.silent:
                print("{0}: JSON encoding error in {1}: {2}"
                      .format(parser.prog, taxfile, str(ex)),
                      file=sys.stderr)
            continue

        res = loader.load(doc, validate, id=taxfile)
        totres.merge(res)

        if not opts.silent and res.failure_count > 0:
            if not opts.quiet:
                print("{0}: The following records failed to load:"
                      .format(parser.prog), file=sys.stderr)
                for f in res.failures():
                    why = (isinstance(f.errs[0], RecordIngestError) and \
                               str(f.errs)) or "Validation errors"
                    print("\t{0}: \t{1}".format(str(f.key), why))
            else:
                print("{0}: {1}: {2} out of {3} records failed to load"
                      .format(parser.prog, taxfile, res.failure_count,
                              res.attempt_count))

    if not opts.quiet:
        print("Ingested {0} out of {1} records".format(totres.success_count,
                                                       totres.attempt_count))

    if totres.failure_count > 0:
        stat = 1
    return stat


    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
