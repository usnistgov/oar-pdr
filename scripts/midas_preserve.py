#! /usr/bin/env python
"""
A command-line script for preserving a MIDAS SIP.
"""
from __future__ import print_function
import os, sys, logging
from argparse import ArgumentParser
import traceback as tb

try:
    import nistoar
except ImportError:
    oarpath = os.environ.get('OAR_PYTHONPATH')
    if not oarpath and 'OAR_HOME' in os.environ:
        oarpath = os.path.join(os.environ['OAR_HOME'], "lib", "python")
    if oarpath:
        sys.path.insert(0, oarpath)
    import nistoar

from nistoar.pdr.exceptions import ConfigurationException, PDRException
from nistoar.pdr.preserv.service import siphandler as sip
from nistoar.pdr import utils, config
from nistoar.id import PDRMinter

log = None

def define_options(progname):
    description = """Create preservation bags for given MIDAS SIP"""
    epilog = None

    parser = ArgumentParser(progname, None, description, epilog)
    
    parser.add_argument('-c', '--config', type=str, dest='cfgfile',
                        metavar='FILE', default=None,
                        help="get configuration from FILE")
    parser.add_argument('-C', '--multisip-style-config', dest="multisipcfg",
                        action='store_true',
                        help="config file has style like that returned from "+
                             "the config service (with an 'sip_type' property)")
    parser.add_argument('-D', '--identify-by-dir', dest="isdir",
                        action='store_true',
                        help="the given ID is actually a path to the directory "+
                             "containing the SIP (incompatible with -E)")
    parser.add_argument('-E', '--identify-by-ediid', dest="isediid",
                        action='store_true',
                        help="the given ID is the full EDI-ID; otherwise, it "+
                             "is the path relative to the review directory "+
                             "(incompatible with -D)")
    parser.add_argument('-R', '--review-dir', type=str, dest='revdir',
                        metavar='DIR', default=None,
                        help="override the review_dir property from the "+
                             "configuration with DIR")
    parser.add_argument('-W', '--working-dir', type=str, dest='workdir',
                        metavar='DIR', default=None,
                        help="override the working_dir property from the "+
                             "configuration with DIR")
    parser.add_argument('-S', '--store-dir', type=str, dest='storedir',
                        metavar='DIR', default=None,
                        help="override the store_dir property from the "+
                             "configuration with DIR")
    parser.add_argument('-l', '--log-file', type=str, dest='logfile',
                        metavar='FILE', default=None,
                        help="override the logfile property from the "+
                             "configuration with FILE")
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
                        help="don't write log messages to screen")
    parser.add_argument('sipid', metavar="ID", type=str, nargs=1,
                        help="the SIP's identifier (see also -D, -E)")

    return parser

class CLIError(RuntimeError):
    """
    A fatal exception of the command-line program that is expected to 
    result in the command exiting with a given exit code.
    """

    def __init__(self, message, exitcode=1):
        super(CLIError, self).__init__(message)
        self.exitcode = exitcode

    def exit(self):
        if log:
            log.critical(str(self))
        else:
            prog = os.path.basename(sys.argv[0])
            print("{0}: {1}".format(prog, str(self)), file=sys.stderr)
        try:
            code = int(self.exitcode)
        except:
            code = 10
        sys.exit(code)

def load_config(configfile=None, multisipstyle=False):
    if not configfile:
        from nistoar import pdr
        if not pdr.def_etc_dir:
            raise CLIError("Can't find default configuration; use -c", 1)
        configfile = os.path.join(pdr.def_etc_dir, "midas_preserve_cfg.yml")
        if not os.path.exists(configfile):
            raise CLIError("{0}: default config file not found; use -c", 1)
    elif not os.path.exists(configfile):
        raise CLIError("{0}: config file not found".format(configfile), 1)

    try:
        cfg = config.load_from_file(configfile)
    except (OSError, ValueError) as ex:
        raise CLIError("{0}: trouble reading file: {1}"
                       .format(configfile, str(ex)), 1)

    if multisipstyle or 'sip_type' in cfg:
        if 'sip_type' not in cfg:
            raise CLIError(configfile + ": Missing 'sip_type' property from " +
                           "multi-SIP-style configuration", 1)
        midascfg = self.cfg['sip_type']
        if 'midas' not in midascfg:
            raise CLIError(configfile + ": 'midas' not a configured SIP type",1)
        midascfg = self.cfg['midas']

        # fold the common parameters into the preserv parameters
        pcfg = deepcopy(midascfg.get('common', {}))
        pcfg.update(midascfg.get('preserv', {}))
                    
        if 'mdbag_dir' not in pcfg:
            pcfg['mdbag_dir'] = midascfg.get('mdserv',{}).get('working_dir')
            if not pcfg['mdbag_dir'] and 'working_dir' in midascfg:
                pcfg['mdbag_dir'] = os.path.join(midascfg['working_dir'],
                                                 'mdserv')
        cfg = pcfg

    return cfg

def get_minter(cfg):
    mntrdir = cfg.get('id_registry_dir', cfg.get('working_dir', '.'))
    mntcfg = cfg.get('id_minter', {})
    return PDRMinter(mntrdir, mntcfg)

def main(argv):
    global log

    # process the command-line options
    prog = os.path.splitext(os.path.basename(argv[0]))[0]
    parser = define_options(prog)
    opts = parser.parse_args(argv[1:])

    if opts.isdir and opts.isediid:
        raise CLIError("-D and -E options are incompatible", 1)

    cfg = load_config(opts.cfgfile, opts.multisipcfg)

    if opts.workdir:
        cfg['working_dir'] = opts.workdir
    if 'working_dir' not in cfg:
        cfg['working_dir'] = "_" + prog + str(os.getpid())
    cfg['working_dir'] = os.path.abspath(cfg['working_dir'])

    if opts.revdir:
        cfg['review_dir'] = os.path.abspath(opts.revdir)
    if opts.storedir:
        cfg['store_dir'] = os.path.abspath(opts.storedir)
    if opts.logfile:
        cfg['logfile'] = os.path.abspath(opts.logfile)

    if 'store_dir' not in cfg:
        cfg['store_dir'] = os.path.join(cfg['working_dir'], 'store')
        if os.path.exists(cfg['working_dir']) and \
           not os.path.exists(cfg['store_dir']):
            os.mkdir(cfg['store_dir'])

    termfmt = False
    if not opts.quiet:
        termfmt = "{0}: %(levelname)s: %(message)s".format(prog)
    config.configure_log(config=cfg, addstderr=termfmt)
    log = logging.getLogger()
    log.info("Using working dir: %s", cfg['working_dir'])

    sipdirname = None
    if opts.isdir or not opts.isediid:
        if opts.isdir:
            # ID is actually the directory containing the SIP
            if not os.path.isdir(opts.sipid[0]):
                raise CLIError("%{0}: not an existing directory".
                               format(opts.sipid[0]))

            sipdir = os.path.abspath(opts.sipid[0])
            cfg['review_dir'] = os.path.dirname(sipdir)
            sipdirname = os.path.basename(sipdir)

        else:
            # ID is a MIDAS record number
            try:
                sipdir = os.path.join(cfg['review_dir'], opts.sipid[0])
                if not os.path.isdir(sipdir):
                    raise CLIError("{0}: not an existing directory".
                                   format(sipdir), 2)
                sipdirname = opts.sipid[0]
            except KeyError as ex:
                raise CLIError("Review directory not specified", 1)

        # in either of these cases, we need to look up the EDI ID from the
        # POD record
        try:
            podfile = os.path.join(sipdir, "_pod.json")
            pod = utils.read_pod(podfile)
            opts.sipid[0] = pod['identifier']
        except KeyError as ex:
            raise CLIError("POD record is missing 'identifier' property", 2)
        except Exception as ex:
            raise CLIError(str(ex), 2)

    minter = get_minter(cfg)

    # start preservation
    try: 
        hndlr = sip.MIDASSIPHandler(opts.sipid[0], cfg, minter=minter,
                                    sipdirname=sipdirname)
        hndlr.bagit()
    except ConfigurationException as ex:
        raise CLIError(str(ex), 1)
    except ConfigurationException as ex:
        raise CLIError(str(ex), 1)
    except PDRException as ex:
        raise CLIError(str(ex), 3)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except CLIError as ex:
        ex.exit()
    except Exception as ex:
        if log:
            log.exception(str(ex))
        else:
            print(str(ex), file=sys.stderr)
            tb.print_exc()

