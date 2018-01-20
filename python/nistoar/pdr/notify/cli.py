"""
provide command-line interface support to the notification framework
"""
import os, sys, re, yaml, logging
from argparse import ArgumentParser

from .service import NotificationService, TargetManager
from .email import Mailer
from .archive import Archiver
from .base import ChannelService, Notice
from ..config import load_from_file
from ..exceptions import ConfigurationException

log = logging.getLogger("Notify").getChild("cli")

def define_options(progname):
    """
    return an ArgumentParser instance that is configured with options
    for the command-line interface.
    """
    description = "send a notification message to subscribers via configured channels"
    epilog = None

    parser = ArgumentParser(progname, None, description, epilog)

    parser.add_argument('-c', '--config', type=str, dest='cfgfile',
                        metavar='FILE', default=None,
                        help="a file containing the notification service "+
                             "configuration to use.  If not provided, a simple "+
                             "default is created from command-line options")

    parser.add_argument('-m', '--smtp-server', type=str, dest='mailserver',
                        metavar="SMTPSERVER[:PORT]", default=None,
                        help="the SMTPSERVER to use to submit email to")
    parser.add_argument('-f', '--from', type=str, dest='frm',
                        metavar="EMAIL_ADDRESS", default=None,
                        help="the address to indicate as the origin of email "+
                             "notifications; accepts either a bare email "+
                             "address or name-annotated one (use quotes to "+
                             "escape shell parsing)")
    parser.add_argument('-t', '--to', type=str, dest='to', action='append',
                        metavar="EMAIL_ADDRESS", default=[],
                        help="addresses to send messages to when the target is "+
                             "'ops'; can be provided multiple times; "+
                             "accepts either a bare email "+
                             "address or name-annotated one (use quotes to "+
                             "escape shell parsing)")
    parser.add_argument('-T', '--target-name', type=str, metavar='LABEL',
                        default='ops', dest='etarget',
                        help="set the name of the email target created from "+
                             "the -ftm options")
    parser.add_argument('-O', '--stdout', action='store_true', dest='stdout',
                        help="send the notification message to standard output "+
                             "instead of submitting it to its configured "+
                             "channels (overrides -m).")
    parser.add_argument('-A', '--archive-dir', type=str, dest='archdir',
                        metavar='DIR',
                        help="a directory to archive email notifications to")

    parser.add_argument('-o', '--origin', type=str, metavar='LABEL',
                        dest='origin',
                        help="show LABEL as the origin of the message")
    parser.add_argument('-s', '--summary', type=str, metavar='DESC',
                        dest='summary', required=True,
                        help="use DESC as the subject or summary of the "+
                             "notification (use quotes to escape shell parsing)")
    parser.add_argument('-l', '--status', type=str, metavar='LABEL',
                        default='INFO', dest='status',
                        help="show LABEL the status or type of message "+
                             "(e.g. 'FAILURE', 'INFO')")
    parser.add_argument('-I', '--stdin', action='store_true',
                        help="read standard input for text to use as the "+
                             "lengthier description of the notification")

    parser.add_argument('targets', metavar='TARGET', type=str, nargs='*',
                        default=[],
                        help='name of notification target(s) to send the '+
                             "notification to (default: -T value or 'ops')")
    return parser

def main(progname, args):
    """
    send out a notification message.  This function provides the main 
    script logic.
    """
    parser = define_options(progname)
    opts = parser.parse_args(args)

    # look for a provided configuration file
    config = {}
    if opts.cfgfile:
        try:
            config = read_config(opts.cfgfile)
        except EnvironmentError as ex:
            raise Failure("problem reading config file, {0}: {1}"
                          .format(opts.cfgfile, ex.strerror))

    # build a configuration from command-line arguments (if present); the aim
    # is to build a target called 'ops' that will send an email alert
    try:
        clicfg = build_ops_config(opts)
    except ValueError as ex:
        raise Failure(exitcode=4, cause=ex)

    # combine configs
    if clicfg:
        config['channels'] = clicfg.get('channels', []) + \
                             config.get('channels', [])
        config['targets']  = clicfg.get('targets',  []) + \
                             config.get('targets',  [])
        if 'archive_targets' in clicfg:
            config['archive_targets'] = \
                              list(set(clicfg['archive_targets'] + \
                                       config.get('archive_targets', [])))
    
    # adjust the configuration to send to stdout if requested
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
        for chan in config.get('channels', []):
            if 'name' not in chan:
                continue
            if chan.get('type') == 'email':
                echans.add(chan['name'])
            elif chan.get('type') == 'archive':
                achans.add(chan['name'])
        echans.add('email')
        achans.add('archive')

        # now update the targets to swap out the channels
        for target in config['targets']:
            if target.get('channel') in echans:
                target['channel'] = 'stdoutmail'
            elif target.get('channel') in achans:
                target['channel'] = 'stdoutarchive'

    # create the notification service
    try:
        service = NotificationService(config, targetmgr=tm)
    except ConfigurationException as ex:
        raise Failure("config error: "+str(ex), 2, ex)

    # create the notification
    notice = create_notice(opts)

    # send the notification
    if not opts.targets:
        opts.targets = [opts.etarget]
    try:
        service.distribute(opts.targets, notice)
    except ValueError as ex:
        raise Failure(exitcode=3, cause=ex)


class Failure(Exception):
    """
    an exception wrapping an expected possible error.  This allows the 
    main script (that calls main()) to distinguish between expected and 
    unexpected errors (of which the latter may cause a stack trace to be 
    printed).  This exception encodes a recommended exit code for the script.
    """
    def __init__(self, message=None, exitcode=1, cause=None):
        if not message:
            if cause:
                message = str(cause)
            else:
                message = "Failure of unknown cause"
        super(Failure, self).__init__(message)
        self.cause = cause
        self.exitcode = exitcode

def read_config(filepath):
    """
    read the configuration from a file having the given filepath

    :except Failure:  if the contents contains syntax or format errors
    :except IOError:  if a failure occurs while opening or reading the file
    """
    try:
        return load_from_file(filepath)
    except (ValueError, yaml.reader.ReaderError, yaml.parser.ParserError) as ex:
        raise Failure("Config parsing error: "+str(ex), 3, ex)

def build_ops_config(opts):
    """
    create a NotificationService configuration from the command-line 
    options
    """
    out = {}
    if not (opts.mailserver or opts.frm or opts.to):
        return out

    if not opts.frm:
        raise Failure("--from argument required for email notifications", 1)
    if not opts.to:
        raise Failure("One or more recipients required via --to argument " +
                      "for email notifications", 1)
    if not opts.mailserver and not opts.stdout:
        log.warn("unable to define 'email' channel without --mailserver "+
                 "argument")

    if opts.mailserver:
        echan = { "name": "email", "type": "email" }
        parts = opts.mailserver.split(':', 1)
        echan['smtp_server'] = parts[0]
        if len(parts) > 1:
            try:
                echan['smtp_port'] = int(parts[1])
            except ValueError as ex:
                raise Failure("Port number not an integer: "+parts[1])
        out['channels'] = [echan]

    etarget = { "name": opts.etarget, "type": "email", "channel": "email" }
    parts = _parse_addr(opts.frm)
    if len(parts) == 2:
        etarget['from'] = parts[0]
    else:
        etarget['from'] = parts[0:2]

    etarget['to'] = []
    for arg in opts.to:
        while arg:
            parts = _parse_addr(arg)
            if len(parts) == 2:
                etarget['to'].append( parts[0] )
            else:
                etarget['to'].append(parts[0:2])
            arg = parts[-1]

    out['targets'] = [etarget]

    if opts.archdir:
        if not os.path.isdir(opts.archdir):
            raise Failure("Requested archive directory does not exist: "+
                          opts.archdir)
        chan = { "name": "archive", "type": "archive",
                 "dir": opts.archdir }
        if 'channels' in out:
            out['channels'].append(chan)
        else:
            out['channels'] = [chan]
        out['archive_targets'] = [opts.etarget]
    
    return out


def _parse_addr(addrstr):
    annotatedre = re.compile(r'^\s*"([^"]+)"\s*\<([^\>]+)\>\s*')
    barere = re.compile(r'^\w+@\w+(\.\w+)+$')
    sepre = re.compile(r'\s*,\s*')

    annotated = annotatedre.search(addrstr)
    more = sepre.search(addrstr)
    if annotated:
        more = sepre.match(addrstr, annotated.end())
        next = (more and more.end()) or annotated.end()
        out = [ annotated.group(1), annotated.group(2),
                addrstr[next:] ]
        if not barere.match(out[1]):
            raise ValueError("Illegally formed email address: "+out[1])

    elif more:
        out = [ addrstr[:more.start()], addrstr[more.end():] ]
        if not barere.match(out[0]):
            raise ValueError("Illegally formed email address: "+out[0])

    else:
        out = [ addrstr.strip(), "" ]
        if not barere.match(out[0]):
            raise ValueError("Illegally formed email address: "+out[0])

    return out

def create_notice(opts, istrm=sys.stdin):
    """
    return a Notice instance constructed from the command-line options
    """
    desc = None
    if opts.stdin:
        desc = istrm.read()
    return Notice(opts.status, opts.summary, desc, opts.origin)

class StdoutMailer(Mailer):
    """
    an email ChannelService which writes notifications to standard output
    rather than delivering it via a mail server.
    """

    def __init__(self, config, stdout=sys.stdout):
        ChannelService.__init__(self, config)
        self._stdout = stdout

    def send_email(self, froma, addrs, message=""):
        """
        send an email to a list of addresses

        :param from str:   the email address to indicate as the origin of the 
                           message
        :param addrs list:  a list of (raw) email addresses to send the email to
        :param message str:  the formatted contents (including the header) to 
                           send.
        :param fd file:    an open file stream to write to (default: sys.stdout)
        """
        fd = self._stdout
        fd.write("To ")
        fd.write(" ".join(addrs))
        fd.write("\n")
        fd.write("From "+froma)
        fd.write("\n")
        fd.write(message)

class StdoutArchiver(Archiver):
    """
    an Archiver ChannelService which writes notifications to standard output
    rather than writing it to a file on disk.
    """
    def __init__(self, config, stdout=sys.stdout):
        ChannelService.__init__(self, config)
        self._pretty = self.cfg.get('pretty', True)
        self._stdout = stdout

    def open_archive_file(self, target):
        """
        return the open file stream to write the notification to.  By 
        default, this returns sys.stdout
        """
        return self._stdout


        
    
        
