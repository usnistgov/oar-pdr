"""
CLI command that will preserve an SIP according to the MIDAS3 conventions
"""
from __future__ import print_function
import logging, argparse, os, shutil, tempfile, re
from copy import deepcopy

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.service.siphandler import MIDAS3SIPHandler
from nistoar.pdr.preserv.service import status
from nistoar.pdr.preserv.bagger.prepupd import UpdatePrepService
from nistoar.pdr.preserv.bagit import NISTBag
from nistoar.pdr.cli import PDRCommandFailure
from nistoar.pdr.notify import NotificationService
from nistoar.id import PDRMinter

ARKIDre = re.compile("^ark:/\d+/")

default_name = "midas3"
help = "preserve a MIDAS3 SIP"
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
    p.add_argument("sipid", metavar="SIPID", type=str, nargs='?',
                   help="the ID for the SIP to process or the path to its metadata bag; as an ID, it "+
                        "can either be an AIP ID or an EDI ID")
    p.add_argument("-d", "--data-dir", metavar="DIR", type=str, dest="datadir",
                   help="directory that contains the data files that are part of this submission "+
                   "(This is equivalent to reviewdir/record-number.)")
    p.add_argument("-b", "--bag-parent-dir", metavar="DIR", type=str, dest="bagparent",
                   help="directory that contains the bag directory with the given SIPID")
    p.add_argument("-s", "--status-only", action="store_true", dest='statusonly',
                   help="report only on the status of the preservation for the SIP (does not preserve)")



def execute(args, config=None, log=None):
    """
    execute this command: preserve an SIP according to the MIDAS3 conventions
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

    if not args.sipid:
        raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
    if ARKIDre.match(args.sipid):
        args.sipid = ARKIDre.sub('', args.sipid)
        
    elif os.sep in args.sipid:
        # sipid is actually a path to the metadata bag; if relative, should either be relative to
        # current directory or the working directory
        sippath = os.path.abspath(args.sipid)
        if not os.path.exists(sippath):
            if args.workdir:
                sippath = os.path.join(args.workdir, args.sipid)
        if not os.path.isdir(sippath):
            raise PDRCommandFailure(default_name, args.sipid+": bag does not exist as a directory", 1)
        config['bagparent_dir'] = os.path.dirname(sippath)
        args.sipid = os.path.basename(args.sipid)
        
    elif args.bagparent:
        # sipid is just an ID; we'll look for it (or set it up) under the state bag parent directory
        # (over-riding the configuration)
        if not os.path.isabs(args.bagparent):
            if args.workdir:
                config['bagparent_dir'] = os.path.join(args.workdir, args.bagparent)
            else:
                config['bagparent_dir'] = os.path.abspath(args.bagparent)

    usenm = args.sipid
    if len(usenm) > 11:
        usenm = usenm[:4]+"..."+usenm[-4:]
    log = log.getChild(usenm)

    # set the data directory
    datadir = None
    tmpdatadir = None
    if args.datadir:
        datadir = os.path.abspath(args.datadir)
        if not os.path.exists(datadir) and args.workdir:
            datadir = os.path.join(args.workdir, args.datadir)
        log.info("Will look for data files in %s", datadir)
        if not os.path.isdir(datadir):
            raise PDRCommandFailure(default_name, args.datadir+": does not exist as a directory", 1)
        config['review_dir'] = os.path.dirname(datadir)
        datadir = os.path.basename(datadir)
    elif 'review_dir' not in config:
        # we will assume that there are no data files to include; create a place-holder
        config['review_dir'] = config['working_dir']
        tmpdatadir = tempfile.mkdtemp(prefix=".pdrcli-tmpdatadir", dir=config['working_dir'])
        datadir = os.path.basename(tmpdatadir)
    elif re.match(r'^mds\d+\-', args.sipid):
        datadir = re.sub(r'^mds\d+\-','', args.sipid)

    try:
        _check_config(config, log)

        # create the SIP handler instance
        notifier = None
        if 'notifier' in config:
            notifier = NotificationService(config['notifier'])
        minter = None
        if 'id_minter' in config:
            mntrdir = config.get('id_registry_dir')
            if not mntrdir:
                mntrdir = os.path.join(config.get('working_dir'), 'idreg')
                if config.get('working_dir') and os.path.isdir(config.get('working_dir')) and \
                   not os.path.exists(mntrdir):
                    log.warn("Creating ID Minter's working dir: "+mntrdir)
                    os.makedirs(mntrdir)
            minter = PDRMinter(mntrdir, config.get('id_minter', {}))

        hdlr = MIDAS3SIPHandler(args.sipid, config, minter, None, notifier, asupdate=True, sipdatadir=datadir)
        if not datadir and hdlr.bagger:
            log.info("Will look for data files in %s", hdlr.bagger.datadir)

        if args.statusonly:
            print_status(args.sipid, hdlr)
            return

        if not hdlr.isready():
            raise PDRCommandFailure(default_name, args.sipid+" is not ready for preservation: "+hdlr.state, 3)

        hdlr.bagit("zip")

        if hdlr.state != status.SUCCESSFUL:
            raise PDRCommandFailure(default_name, "%s: preservation failed (%s)" % (args.sipid,hdlr.status), 4)
    finally:
        if tmpdatadir:
            shutil.rmtree(tmpdatadir)

def print_status(reqid, hdlr):
    bagdirstat = "does not yet exist"
    bagdir = hdlr.bagdir
    version = None
    if os.path.isdir(bagdir):
        bag = NISTBag(bagdir)
        bagdirstat = "exists"
        try: 
            nerd = bag.nerd_metadata_for('', True)
            version = nerd.get('version', "(not yet set)")
        except PDRException as ex:
            bagdirstat = "appears incomplete or invalid"
    else:
        mdbag = os.path.join(hdlr.mdbagdir, hdlr.bagname)
        if os.path.isdir(mdbag):
            bagdirstat += "; can generate from midas draft"

    datadir = hdlr.datadir
    datadirstat = (os.path.isdir(hdlr.datadir) and "exists") or "missing"
    if os.path.basename(datadir).startswith(".pdrcli-tmpdatadir"):
        datadir = ''
        datadirstat = "not provided"

    print()
    print(reqid, "Preservation Status:", hdlr.state)
    print()
    print("Metadata Bag:", bagdir, "(%s)" % bagdirstat)
    if version is not None:
        print("Target version:", version)
    print("Data file source dir:", datadir, "(%s)" % datadirstat)
    print("Output Destination:", hdlr.storedir)
    print()
    
def _check_config(cfg, log):
    def _complain(msg):
        raise ConfigurationException(msg)
    def _complain_about(paramname):
        _complain("Missing configuration property: "+paramname)

    for prop in "store_dir".split():
        if prop not in cfg:
            _complain_about(prop)

    # set critical paths that are relative to be relative to workdir
    if 'working_dir' in cfg and os.path.isdir(cfg['working_dir']):

        if 'notifier' in cfg:
            for chnl in _find_archive_channels(cfg['notifier'].get('channels',[])):
                if chnl and 'dir' in chnl:
                    if not os.path.isabs(chnl['dir']):
                        chnl['dir'] = os.path.abspath(os.path.join(cfg['working_dir'], chnl['dir']))
                        if not os.path.exists(chnl['dir']):
                            log.warn("Creating notifier archive dir: "+chnl['dir'])
                            os.makedirs(chnl['dir'])

        if not os.path.isabs(cfg['store_dir']):
            cfg['store_dir'] = os.path.join(cfg['working_dir'], cfg['store_dir'])
            if not os.path.exists(cfg['store_dir']):
                log.warn("Creating notifier output store dir: "+chnl['dir'])
                os.makedirs(cfg['store_dir'])

        if not os.path.isabs(cfg['review_dir']):
            cfg['review_dir'] = cfg['working_dir']

        if 'status_manager' in cfg:
            smgr = cfg['status_manager']
            if 'cachedir' in smgr and not os.path.isabs(smgr['cachedir']):
                smgr['cachedir'] = os.path.join(cfg['working_dir'], smgr['cachedir'])
                if not os.path.exists(smgr['cachedir']):
                    log.warn("Creating preservation status cache dir: "+cfg['cachedir'])
                    os.makedirs(cfg['cachedir'])
                    

def _find_archive_channels(chcfg):
    if not isinstance(chcfg, list):
        return []
    return [ch for ch in chcfg if ch.get('type','') == "archive"]
