"""
CLI command that will update apply various validation tests to a specified bag.
"""
import logging, argparse, sys, os, shutil, tempfile, json
from copy import deepcopy

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
from nistoar.pdr.cli import PDRCommandFailure
from nistoar.pdr import def_schema_dir
from nistoar.nerdm.validate import validate
import nistoar.pdr.preserv.bagit.validate as vald8
from . import define_pub_opts, determine_bag_path

default_name = "validate"
help = "validate a bag's compliance to the NIST BagIt profile"
description = """
  This command will run a battery of tests that determines its compliance with the NIST BagIt profile
  or parts of it.  By default, it will run the full suite of validation tests agains the specified bag; 
  however, command line options will restrict tests to validating against portions of the full battery, 
  including the core BagIt profile, the NERDm metadata, or just the multibag profile.  
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
    p.add_argument("-n", "--nerdm", action="append_const", dest='parts', const='n',
                   help="just validate the metadata's compliance with the NERDm schema")
    p.add_argument("-r", "--nerdm-resource", action="append_const", dest='parts', const='r',
                   help="just validate the resource level's metadata compliance with the NERDm schema; "+
                        "ignored if -n or -f is specified")
    p.add_argument("-f", "--nerdm-filepath", metavar='FILEPATH', type=str, dest='fpath', 
                   help="just validate the metadata compliance with the NERDm schema of a component "+
                        "having the filepath FILEPATH; ignored if -n is specified")
    p.add_argument("-B", "--bagit", action="append_const", dest='parts', const='B',
                   help="just validate the bag against the core BagIt standard")
    p.add_argument("-M", "--multibag", action="append_const", dest='parts', const='M',
                   help="just validate the bag against the multibag BagIt profile")
    p.add_argument("-s", "--schema-dir", metavar="DIR", type=str, dest='schemadir',
                   help="directory containing required metadata schemas; if not provided the default "+
                        "location will be determined.")
    p.add_argument("-a", "--merge-annotations", action="store_true", dest="merge",
                   help="merge annotations before doing NERDm validation; ignored unless -n, -r, or -f "+
                        "is used")

    return None

def execute(args, config=None, log=None):
    if not log:
        log = logging.getLogger(default_name)
    if not config:
        config = {}

    if isinstance(args, list):
        # cmd-line arguments not parsed yet
        p = argparse.ArgumentParser()
        load_command(p)
        args = p.parse_args(args)
    if args.parts is None:
        args.parts = []

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

    bag = NISTBag(bagdir)
    if not args.parts and not args.fpath:
        # do a full NIST Preservation bag validation (and exit)
        if not validate_aip(bag, log, config):
            raise PDRCommandFailure(default_name, "Bag Validation problems detected", 6)
        return

    # run only portions of the compliance checks
    ok = True
    if 'B' in args.parts:     # run the BagIt compliance checks
        ok = validate_bag(bag, log, config) and ok

    if 'M' in args.parts:     # run Multibag BagIt profile compliance checks
        ok = validate_multibag(bag, log, config) and ok

    if 'n' in args.parts:     # validate the full NERDm metadata record
        ok = validate_nerdm(bag, log, args.merge) and ok

    else:
        if 'r' in args.parts: # validate the resource-level metadata
            ok = validate_nerdm_for(bag, '', log, args.merge)
        if args.fpath:        # validate the metadata for a component with a specific file path
            ok = validate_nerdm_for(bag, args.fpath, log, args.merge)

    if not ok:
        raise PDRCommandFailure(default_name, "Bag Validation problems detected", 6)
        

def validate_nerdm_for(bag, filepath, log, merge=True, success=None, schemadir=None):
    """
    validate the NERm metadata for a particular portion of the resource.
    :param str filepath:   the path to the data component to validate or an empty string to 
                           validate the resource-level metadata
    :param Logger   log:   the log to record the results to.  
    :param bool   merge:   if True, merge the annotations into the metadata before validating
    :param str  success:   The message to record to the log if the metadata proves valid
    """
    if not schemadir:
        schemadir = def_schema_dir
    nerd = bag.nerd_metadata_for(filepath, merge)
    errs = validate(nerd, schemadir)
    if errs:
        if filepath:
            log.error("%i validation error%s detected in metadata for %s",
                      len(errs), (len(errs) > 1 and "s") or "", filepath)
        else:
            log.error("%i validation error%s detected in resource-level metadata:",
                      len(errs), (len(errs) > 1 and "s") or "")
        for err in errs:
            log.error(str(err))
        return False
    else:
        if success is None:
            if filepath:
                success = "NERDm metadata for "+filepath+" is valid"
            else:
                success = "NERDm resource-level metadata is valid."
        if success:
            log.info(success)
        return True

def validate_nerdm(bag, log, merge=True, success=None, schemadir=None):
    """
    validate the NERDm metadata for a particular portion of the resource.
    :param str filepath:   the path to the data component to validate or an empty string to 
                           validate the resource-level metadata
    :param Logger   log:   the log to record the results to.  
    :param bool   merge:   if True, merge the annotations into the metadata before validating
    :param str  success:   The message to record to the log if the metadata proves valid
    """
    if not schemadir:
        schemadir = def_schema_dir
    nerd = bag.nerdm_record(merge)
    errs = validate(nerd, schemadir)
    if errs:
        log.error("%i validation%s detected in NERDm metadata:",
                  len(errs), (len(errs) > 1 and "s") or "")
        for err in errs:
            log.error(str(err))
        return False
    else:
        if success is None:
            success = "NERDm metadata is valid."
        if success:
            log.info(success)
        return True

def validate_aip(bag, log, config=None, failon=vald8.ERROR):
    """
    validate the given bag against the full NIST Preservation Bag Profile
    """
    if not config:
        config = {}
    vld8r = vald8.NISTAIPValidator(config)
    return log_validation_results(vld8r.validate(bag), log, bag.name, failon)

def validate_bag(bag, log, config=None, failon=vald8.ERROR):
    """
    validate the given bag against the full NIST Preservation Bag Profile
    """
    if not config:
        config = {}
    vld8r = vald8.BagItValidator(config)
    return log_validation_results(vld8r.validate(bag), log, bag.name, failon)

def validate_multibag(bag, log, config=None, failon=vald8.ERROR):
    """
    validate the given bag against the full NIST Preservation Bag Profile
    """
    if not config:
        config = {}
    vld8r = vald8.MultibagValidator(config)
    return log_validation_results(vld8r.validate(bag), log, bag.name, failon)

def log_validation_results(results, log, name, failon=vald8.ERROR):
    """
    log the results of a bag validation to the log
    """
    issues = results.failed(vald8.ALL)
    if len(issues):
        log.warn("Bag Validation issues detected for AIP id="+name)
        for iss in issues:
            if iss.type == iss.ERROR:
                log.error(iss.description)
            elif iss.type == iss.WARN:
                log.warn(iss.description)
            else:
                log.info(iss.description)

        if results.count_failed(failon):
            return False

    else:
        log.info("bag validation completed without issue")

    return True
