"""
a command-line interface to health checks.  The :py:func:`main` function provides the implementation.
"""
import argparse, sys, os, re, logging, textwrap, traceback as tb
from argparse import ArgumentParser

from ... import config
from ...exceptions import ConfigurationException
from ...notify.service import TargetManager, NotificationService
from ...notify.cli import StdoutMailer, StdoutArchiver, Failure
from . import check_and_notify

prog = re.sub(r'\.py$', '', os.path.basename(sys.argv[0]))

def define_options(progname):
    """
    return an ArgumentParser instance that is configured with options
    for the command-line interface.
    """
    description = "check the health of the PDR/SDP by checking web endpoints"
    epilog = None
    
    parser = ArgumentParser(progname, None, description, epilog)

    parser.add_argument('-c', '--config', type=str, dest='cfgfile', metavar='FILE', required=True,
                        help="a file containing the notification service configuration to use.")
    parser.add_argument('-m', '--smtp-server', type=str, dest='mailserver', metavar="SMTPSERVER[:PORT]", 
                        default=None, help="the SMTPSERVER to use to submit email to")
    parser.add_argument('-o', '--origin', type=str, metavar='LABEL', dest='origin', default="PDR.Health",
                        help="show LABEL as the origin of the message")
    parser.add_argument('-p', '--platform', type=str, metavar='PLAT', dest='platform', default="Unknown",
                        help="show PLAT as the name of the platform (e.g. prod, test, etc.) where the "+
                             "check was run on")
    parser.add_argument('-l' '--logfile', action='store', dest='logfile', type=str, metavar='FILE',
                        help="write messages that normally go to standard error to FILE as well.  If -q "+
                             "is also specified, the messages will only go to the logfile")
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help="print more (debug) messages to standard error and/or the log file")
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                        help="suppress all error and warning messages to standard error")
    parser.add_argument('-O', '--stdout', action='store_true', dest='stdout',
                        help="send the notification message to standard output instead of "+
                             "submitting it to its configured channels (overrides -m).")

    parser.add_argument('checks', metavar='CHECK', type=str, nargs='*', default=[],
                        
                        help='name of health checks to perform')
    return parser

def main(progname, args):
    """
    run health checks via command-line arguments.  
    :raises Failure:  if a fatal error occurs, requiring the command to exit with a particular exit code
    """
    parser = define_options(progname)
    opts = parser.parse_args(args)

    rootlog = logging.getLogger()
    level = (opts.verbose and logging.DEBUG) or logging.INFO
    if opts.logfile:
        # write messages to a log file
        fmt = "%(asctime)s " + (opts.origin or prog) + ".%(name)s %(levelname)s: %(message)s"
        hdlr = logging.FileHandler(opts.logfile)
        hdlr.setFormatter(logging.Formatter(fmt))
        hdlr.setLevel(logging.DEBUG)
        rootlog.addHandler(hdlr)
        rootlog.setLevel(level)

    # configure a default log handler
    if not opts.quiet:
        fmt = prog + ": %(levelname)s: %(message)s"
        hdlr = logging.StreamHandler(sys.stderr)
        hdlr.setFormatter(logging.Formatter(fmt))
        hdlr.setLevel(logging.DEBUG)
        rootlog.addHandler(hdlr)
        rootlog.setLevel(level)
    elif not rootlog.handlers:
        rootlog.addHandler(logging.NullHandler())

    # look for a provided configuration file
    config = {}
    if opts.cfgfile:
        try:
            cfg = read_config(opts.cfgfile)
        except EnvironmentError as ex:
            raise Failure("problem reading config file, {0}: {1}"
                          .format(opts.cfgfile, ex.strerror))
    else:
        cfg = config.service.get("pdr-health")

    # modify configuration based on command line options
    notcfg = cfg.get('notifier', {})
    if opts.mailserver:
        chnls = notcfg.get('channels', [])
        for chan in chnls:
            if chan.get('type') == "email":
                chan['smtp_server'] = opts.mailserver

    # Handle standard out request, if present
    tm = None
    if opts.stdout:
        # register the stdout channels
        tm = TargetManager()
        tm.register_channel_class("stdoutmail", StdoutMailer)
        chcfg = { "name": "stdoutmail",
                  "type": "stdoutmail" }
        tm.define_channel(chcfg)
        tm.register_channel_class("stdoutarch", StdoutArchiver)
        chcfg = { "name": "stdoutarch",
                  "type": "stdoutarch" }
        tm.define_channel(chcfg)

        # find the email and archive channels
        echans = set();  achans = set()
        for chan in notcfg.get('channels', []):
            if 'name' not in chan:
                continue
            if chan.get('type') == 'email':
                echans.add(chan['name'])
            elif chan.get('type') == 'archive':
                achans.add(chan['name'])
        echans.add('email')
        achans.add('archive')

        # now update the targets to swap out the channels
        for target in notcfg['targets']:
            if target.get('channel') in echans:
                target['channel'] = 'stdoutmail'
            elif target.get('channel') in achans:
                target['channel'] = 'stdoutarchive'

        # remove the regular email and archive channels from the configuration
        notcfg['channels'] = [c for c in notcfg.get('channels', [])
                                if c.get('type') != 'archive' and c.get('type') != 'email']
        if 'archive_targets' in notcfg:
            del notcfg['archive_targets']

    else:
        # create archive directory if necessary (but only if -O was not specified)
        ensure_archive_dir(notcfg.get('channels', []))

    # create the notification service
    try:
        notifier = NotificationService(notcfg, targetmgr=tm)
    except ConfigurationException as ex:
        raise Failure("config error: "+str(ex), 2, ex)

    # run the requested checks
    checks = {}
    for chk in cfg.get('checks', []):
        if 'name' in chk:
            checks[chk['name']] = chk

    unconfigured = []
    for chkname in opts.checks:
        if chkname in checks:
            chkcfg = checks.get(chkname)
            services = [s for s in cfg.get('services', []) if s.get('name') in chkcfg.get('services',[])]
            try:
                check_and_notify(services, notifier, chkcfg.get('failure'), chkcfg.get('success'),
                                 chkcfg.get('message'), opts.origin, opts.platform, chkname)
            except Exception as ex:
                raise Failure("Health check failure: "+str(ex), 3, ex)
        else:
            unconfigured.append(chkname)

    alerts = notcfg.get('alerts', [])
    if unconfigured:
        summ = "Requested unconfigured checks"
        if 'healthcheck.proofoflife' in alerts:
            notifier.alert('healthcheck.proofoflife', summ,
                           summ+": "+str(unconfigured)+".\nCheck configuration for errors.",
                           opts.origin)
        else:
            raise Failure(summ+": "+str(unconfigured))

def read_config(filepath):
    """
    read the configuration from a file having the given filepath

    :except Failure:  if the contents contains syntax or format errors
    :except IOError:  if a failure occurs while opening or reading the file
    """
    try:
        return config.load_from_file(filepath)
    except (ValueError, yaml.reader.ReaderError, yaml.parser.ParserError) as ex:
        raise Failure("Config parsing error: "+str(ex), 3, ex)

def ensure_archive_dir(chancfg):
    """
    Look through the given channel configurations and ensure the existence of the archive directory.
    If a directory does not exist, it will be created only its parent directory exists.
    """
    for chan in chancfg:
        if chan.get('type') == 'archive' and 'dir' in chan:
            archdir = os.path.abspath(chan['dir'])
            parent = os.path.dirname(archdir)
            if not os.path.exists(archdir) and os.path.isdir(parent):
                try:
                    os.mkdir(archdir)
                except OSError as ex:
                    raise Failure(chan['dir'] + ": Unable to create archive directory: " + str(ex), 2)

