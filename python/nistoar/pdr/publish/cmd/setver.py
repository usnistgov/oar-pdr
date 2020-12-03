"""
CLI command that will update the version metadatum for a bag
"""
import logging, argparse, sys, os, shutil, tempfile, json, re
from copy import deepcopy
from datetime import date
from collections import OrderedDict

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
from nistoar.pdr.cli import PDRCommandFailure
from . import validate as vald8

default_name = "setver"
help = "set the release version in a bag's NERDm metadata"
description = """
  This command will set or increment string version string in bag's NERDm metadata.  
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
    p.add_argument("aipid", metavar="AIPID", type=str, nargs='?', help="the AIP-ID for the bag to examine "+
                   "or the file path to the bag's root directory")
    p.add_argument("-b", "--bag-parent-dir", metavar="DIR", type=str, dest='bagparent',
                   help="the directory to look for the specified bag; if not specified, it will either set "+
                        "to the metadata_bag_dir config or otherwise to the working directory")
    p.add_argument("-s", "--set-version", metavar="VERSION", type=str, dest='setver',
                   help="set the full version value to VERSION, an arbitrary string")
    p.add_argument("-i", "--increment-level", metavar="LEV", type=int, dest='level',
                   help="increment the version at a particular level where LEV is a positive integer "+
                        "(usually 1, 2, or3) which indicates the version field as counted (from 1) from "+
                        "the left.  That is, LEV=1 increases the right-most or most-minor field by one.  "+
                        "When LEV > 1, field to the right of that level get set to 0.")
    p.add_argument("-m", "--increment-for-metadata", action='store_true', dest='incr4md',
                   help="increment the right most version field, appropriate for metadata updates "+
                        "(equivalent to --increment-level=1)")
    p.add_argument("-d", "--increment-for-data", action='store_true', dest='incr4d',
                   help="increment the right most version field, appropriate for data updates "+
                        "(equivalent to --increment-level=2)")
    p.add_argument("-V", "--validate", action="store_true", dest="validate",
                   help="validate the NERDm metadata after update.")
    p.add_argument("-H", "--history-message", metavar="MSG", type=str, dest="why",
                   help="update the version history and use MSG as the message describing the reason for "+
                        "the update.  If the version is not being updated (via -m, -d, -i, or -s), the "+
                        "history for the current version is set")
    p.add_argument("-a", "--as-annotations", action="store_true", dest="asannots",
                   help="save the updated version and history as annotations")
    p.add_argument("-r", "--repo-url-base", metavar='BASEURL', type=str, dest='repourl',
                   help="the base URL to use for PDR data access services (ignored if used with -H)")

    return None

def _check_opt_choices(args, config):
    opts = [args.setver, args.incr4md, args.incr4d, args.level]
    if len([bool(o) for o in opts if bool(o)]) > 1:
        raise PDRCommandFailure(default_name, "Pick only one of -s, -i, -m, and -d", 1)
    elif len([bool(o) for o in opts+[args.why] if bool(o)]) == 0:
        raise PDRCommandFailure(default_name, "Must specify one of -s, -i, -m, -d, or -H", 1)

    if args.incr4md:
        args.level = 1
    elif args.incr4d:
        args.level = 2

    if args.repourl:
        if not args.repourl.endswith('/'):
            args.repourl += '/'
        svc = config.setdefault("landing_page_service", {})
        svc['service_endpoint'] = args.repourl + "od/id/"

def increment_version(version, level=1):
    """
    increment the given version at a particular level
    """
    if level < 1:
        raise ValueError("increment_version: level must be positive: "+str(level))

    m = re.compile(r'^(\d+(.\d+)*)\+ \(.*\)').search(version)
    if m:
        # version is marked as "+ (in edit)"; remove marking
        version = m.group(1)
    parts = version.split('.')
    
    if level > len(parts):
        raise ValueError("increment_version: version has insufficient levels to increment level "+str(level))

    if not re.match(r'^\d+$', parts[-1*level]):
        raise ValueError("increment_version: version does not have an integer at level "+str(level)+
                         ": "+version)
    parts[-1*level] = str(int(parts[-1*level]) + 1)

    if level > 1:
        for i in range(-1,-1*level,-1):
            parts[i] = '0'

    return ".".join(parts)

def execute(args, config=None, log=None):
    """
    execute this command: create a base metadata bag to update a dataset based on its last 
    published version
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
    usenm = args.aipid
    if len(usenm) > 11:
        usenm = usenm[:4]+"..."+usenm[-4:]
    log = log.getChild(usenm)
    
    # set the input bag
    workdir = config.get('working_dir', '.')
    bagparent = config.get('metadata_bag_dir')
    if os.sep in args.aipid:
        bagpath = os.path.abspath(args.aipid)
        if not os.path.exists(bagpath):
            if args.workdir:
                bagpath = os.path.join(args.workdir, args.aipid)
        bagparent = os.path.dirname(bagpath)
        args.aipid = os.path.basename(bagpath)
    elif args.bagparent:
        bagparent = args.bagparent
    if not bagparent:
        bagparent = workdir
    elif not bagparent.startswith('./') and not bagparent.startswith('../') and not os.path.isabs(bagparent):
        bagparent = os.path.join(workdir, bagparent)
    bagdir = os.path.join(bagparent, args.aipid)
    if not os.path.isdir(bagdir):
        raise PDRCommandFailure(default_name, "Input bag does not exist (as a dir): "+bagdir, 2)
    log.info("Found input bag at "+bagdir)

    _check_opt_choices(args, config)

    # now do the work
    bag = NISTBag(bagdir)
    nerd = bag.nerd_metadata_for('', args.asannots)
    version = args.setver
    if args.level and not version:
        version = nerd.get('version')
        if not version:
            version = "1.0.0"
        else:
            try:
                version = increment_version(version, args.level)
            except ValueError as ex:
                raise PDRCommandFailure(default_name,
                                        "Unable to increment unconventional version: "+version, 7, ex)

    update = OrderedDict()
    if version:
        update['version'] = version
    else:
        version = nerd['version']

    # update the history if requested
    if args.why:
        history = nerd.get('versionHistory', [])
        if len(history) > 1 and history[-1].get('version') == version:
            # history entry already exists for current version; just update the message
            history[-1]['description'] = args.why

        else:
            # append a new entry to the history
            if '@id' not in nerd:
                raise PDRCommandFailure(default_name, "Unable to update version history as @id is not set", 2)
            baseurl = config.get('repo_access', {}).get('landing_page_service', {})  \
                            .get('service_endpoint', "https://data.nist.gov/od/id/")
            history.append(OrderedDict([
                ('version', version),
                ('issued', date.today().isoformat()),
                ('@id', nerd['@id']),
                ('location', baseurl+nerd['@id']),
                ('description', args.why)
            ]))

        update['versionHistory'] = history

    # write out the update
    try:
        bldr = BagBuilder(os.path.dirname(bag.dir), os.path.basename(bag.dir), logger=log)
        msg = "version updated to "+version
        if not args.setver and not args.level:
            msg = "version history updated for "+version

        if args.asannots:
            bldr.update_annotations_for('', update, message=msg+" (to annotations)")
        else:
            bldr.update_metadata_for('', update, message=msg)
    finally:
        bldr.disconnect_logfile()

    # validate the update if requested
    if args.validate:
        vald8.validate_nerdm_for(bag, '', log, args.asannots, "Updated metadata is valid")

