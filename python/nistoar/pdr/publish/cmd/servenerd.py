"""
CLI command that will extract a full NERDm record from a bag and copy it into a directory used to serve 
NERDm records.
"""
import logging, argparse, sys, os, shutil, tempfile, json
from copy import deepcopy

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.bagger.prepupd import UpdatePrepService
from nistoar.pdr.preserv.bagit.bag import NISTBag
from nistoar.pdr.utils import write_json
from nistoar.pdr.cli import PDRCommandFailure
from . import define_pub_opts, determine_bag_path

default_name = "servenerd"
help = "copy the NERDm record from a bag to NERDm serve directory"
description = \
"""extracts a full NERDm record from the specified bag and copies it to an output directory.  Unless 
specified via --nerd-serve-dir, the output directory will be configured prepub_nerd_dir directory.
"""

def load_into(subparser):
    """
    load this command into a CLI by defining the command's arguments and options.
    :param argparser.ArgumentParser subparser:  the argument parser instance to define this command's 
                                                interface into it 
    :rtype: None
    """
    p = subparser
    p.description = description

    # args common to all pub subcommands
    define_pub_opts(p)

    # setver-specific args
    p.add_argument("-n", "--nerd-serve-dir", metavar="DIR", type=str, dest='nrdserv',
                   help="the output directory to write the record to; if set to '-', the record will be"+
                        "printed to standard out")

    return None

def execute(args, config=None, log=None):
    """
    execute this command: extract a full NERDm record from a bag and copy it into a directory used to serve 
    NERDm records.
    """
    if not log:
        log = logging.getLogger(default_name)
    if not config:
        config = {}

    if isinstance(args, list):
        # cmd-line arguments not parsed yet
        p = argparse.ArgumentParser()
        load_command(p)
        args = p.parse_args(args)

    if not args.aipid:
        raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
    args.aipid = args.aipid[0]
    usenm = args.aipid
    if len(usenm) > 11:
        usenm = usenm[:4]+"..."+usenm[-4:]
    log = log.getChild(usenm)

    # set the input bag
    workdir, bagparent, bagdir = determine_bag_path(args, config)
    if not os.path.isdir(bagdir):
        raise PDRCommandFailure(default_name, "Input bag does not exist (as a dir): "+bagdir, 2)

    # set the output destination
    outdir = args.nrdserv
    if not outdir:
        outdir = config.get('prepub_nerd_dir')
    if not outdir:
        outdir = "nrdserv"
    if not os.path.isabs(outdir) and not outdir.startswith('.') and outdir != '-':
        outdir = os.path.join(workdir, outdir)
        if not os.path.exists(outdir):
            log.info("Creating NERD service directory, nrdserv, within work directory")
            os.makedirs(outdir)
    if outdir != '-' and not os.path.isdir(outdir):
        raise PDRCommandFailure(default_name, "Output directory does not exist: "+outdir, 1)

    dest = outdir
    if outdir != '-':
        dest = os.path.join(outdir, os.path.basename(bagdir)+".json")
    serve_nerdm(bagdir, dest, log)


def serve_nerdm(bagdir, nerdmfile, log=None):
    bag = NISTBag(bagdir)
    nerdm = bag.nerdm_record(True)

    if nerdmfile == '-':
        json.dump(nerdm, sys.stdout, indent=4, separators=(',', ': '))
    else:
        write_json(nerdm, nerdmfile)
    if log:
        log.info("Updated NERDm record in export directory: %s", os.path.dirname(nerdmfile))


