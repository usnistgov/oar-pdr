"""
CLI command that will setup a metadata bag based on the last published version of a specified dataset.
"""
import logging, argparse, os, shutil, tempfile
from copy import deepcopy

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.bagger.prepupd import UpdatePrepService
from nistoar.pdr.cli import PDRCommandFailure

default_name = "prepupd"
help = "create a metadata bag as basis for an update"
description = \
"""creates a metadata bag based on the last published version of a specified dataset to be used as 
the basis for an update.
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
    p.add_argument("aipid", metavar="AIPID", type=str, nargs=1, help="the AIP-ID for the dataset to prep")
    p.add_argument("-r", "--repo-url-base", metavar='BASEURL', type=str, dest='repourl',
                   help="the base URL to use for PDR data access services")
    p.add_argument("-d", "--output-dir", "-b", "--bag-parent-dir", metavar='DIR', type=str, dest='outdir',
                   help="the directory to cache write the bag into; if not provided, defaults to the "+
                        "working directory")
    p.add_argument("-C", "--cache-dir", metavar='DIR', type=str, dest='cachedir',
                   help="a local directory to cache retrieved head bags into")

    return None

def get_access_config(args, config):
    """
    update the given configuration based on the input provided by the command line arguments.  Note that 
    the logging configuration cannot be affected by this function.
    """
    out = deepcopy(config.get("repo_access", {}))
    
    if args.repourl or args.cachedir:
        if args.repourl:
            if not args.repourl.endswith('/'):
                args.repourl += '/'
            svc = out.setdefault("distrib_service", {})
            svc['service_endpoint'] = args.repourl + "od/ds/"
            svc = out.setdefault("metadata_service", {})
            svc['service_endpoint'] = args.repourl + "rmm/"

        if args.cachedir:
            d = args.cachedir
            if not os.path.isabs(d):
                d = os.path.join(config.get('working_dir', '.'), d)
                if not os.path.exists(d):
                    os.makedirs(d)
            if not os.path.isdir(d):
                raise PDRCommandFailure(default_name,"requested cache dir is not an existing directory: "+d,1)
            out['headbag_cache'] = d

    return out
    

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
    args.aipid = args.aipid[0]
    usenm = args.aipid
    if len(usenm) > 11:
        usenm = usenm[:4]+"..."+usenm[-4:]
    log = log.getChild(usenm)
    
    outdir = args.outdir
    if not outdir:
        outdir = config.get('working_dir')
    if not outdir:
        raise PDRCommandFailure(default_name, "Output directory not specified (use '-d' or '-w')", 1)
    outbag = os.path.join(outdir, args.aipid)
    if os.path.exists(outbag):
        raise PDRCommandFailure(default_name, "Output bag already exists: "+outbag, 2)

    cfg = get_access_config(args, config)
    cdir = None
    if 'headbag_cache' not in cfg:
        cdir = tempfile.mkdtemp(dir=config.get('working_dir', '.'))
        cfg['headbag_cache'] = cdir

    try:
        
        svc = UpdatePrepService(cfg)
        if not prepare_update_bag(svc, args.aipid, outbag, log=log):
            raise PDRCommandFailure(default_name, args.aipid + ": AIP was not previously published", 3)
        log.info("Working bag initialized with metadata from previous publication")
        
    except ConfigurationException as ex:
        raise ex
    except PDRServerError as ex:
        raise PDRCommandFailure(default_name, "Remote service error: "+str(ex), 4, ex)
    except PDRException as ex:
        raise PDRCommandFailure(default_name, "Unexpected error: "+str(ex), 5, ex)
    finally:
        if cdir:
            shutil.rmtree(cdir)

def prepare_update_bag(updsvc, aipid, destbag, log=None):
    """
    create a base metadata bag to update a dataset based on its last published version.  The output 
    bag's name will match the provided aipid.
    :param UpdatePrepService updsvc:   the update service to use
    :param str                aipid:   the AIP ID of the dataset to create the bag for
    :param str              destbag:   the full path to the root directory of the metadata bag to create
    :param Logger               log:   the Logger to use for messages
    :rtype bool:
    :return:  False if the AIP was not previously published
    """
    return updsvc.prepper_for(aipid, log=log).create_new_update(destbag)


    
    

    
    
    
