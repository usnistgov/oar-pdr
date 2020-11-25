"""
module for assembling command-line interface to PDR operational commands
"""
import logging, os, sys
from argparse import ArgumentParser
from copy import deepcopy

from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr import config as cfgmod

description = "execute PDR administrative operations"
epilog = None
default_prog_name = "pdr"

def define_opts(progname=None, parser=None):
    """
    define the top level arguments 
    """
    global default_prog_name

    if not parser:
        if not progname:
            progname = default_prog_name
        parser = ArgumentParser(progname, None, description, epilog)

    parser.add_argument("-w", "--workdir", type=str, dest='workdir', metavar='DIR', default=".", 
                        help="target input and output files with DIR by default (including log); default='.'")
    parser.add_argument("-c", "--config", type=str, dest='conf', metavar='FILE',
                        help="read configuration from FILE (over-rides --in-live-sys)")
    parser.add_argument("-S", "--in-live-system", action="store_true", dest='livesys',
                        help="operate within the live PDR data publishing environment; this is " +
                             "accomplished by loading a configuration from the configuration service")
    parser.add_argument("-l", "--logfile", type=str, dest='logfile', metavar='FILE', 
                        help="log messages to FILE, over-riding the configured logfile")
    parser.add_argument("-q", "--quiet", action="store_true", dest='quiet',
                        help="do not print error messages to standard error")
    parser.add_argument("-D", "--debug", action="store_true", dest='debug',
                        help="send DEBUG level messages to the log file")
    parser.add_argument("-v", "--verbose", action="store_true", dest='verbose',
                        help="print INFO and (with -d) DEBUG messages to the terminal")

    return parser

class PDRCommandFailure(Exception):
    """
    An exception that indicates that a failure occured while executing a command.  The CLI is 
    expected to exit with a non-zero exit code
    """
    
    def __init__(self, cmdname, message, exstat=1, cause=None):
        """
        Create the exception
        :param str cmdname:   the name of the command that failed to execute
        :param str message:   an explanation of what went wrong
        :param int exstat:    the recommended (relative) status to exit with.  As the parent command 
                                may offset form this actual value (by a factor of 10), it is recommended 
                                that it is a value less than 10.  
        """
        if not message:
            if cause:
                message = str(cause)
            else:
                message = "Unknown command failure"

        super(PDRCommandFailure, self).__init__(message)
        self.stat = exstat
        self.cmd = cmdname
        self.cause = cause

class CommandSuite(object):
    """
    an interface for running the sub-commands of a parent command
    """
    def __init__(self, suitename, parent_parser):
        """
        create a command interface
        :param str suitename:  the command name used to access this suites' subcommands
        :param argparse.ArgumentParser parent_parser:  the ArgumentParser for the command that this 
                               suite will be added into.
        """
        self.suitename = suitename
        self._subparser_src = None
        if parent_parser:
            self._subparser_src = parent_parser.add_subparsers(title="subcommands", dest=suitename+"_subcmd")
        self._cmds = {}

    def load_subcommand(self, cmdmod, cmdname=None):
        """
        load a subcommand into this suite of subcommands.  

        The cmdmod arguemnt is a module or object that must specify a load_into() function, a help string 
        property, and default_name string property.  The load_into() should accept two arguments: an 
        ArgumentParser instance and a string giving the name that the command suite should be accessed by
        (which can be None to use the default name).  Its implementation should load its command-line option 
        and argument defintions into ArgumentParser.  It should return either None or CommandSuite instance.  
        If None, then the given cmd module/object must also include an execute() function (that has the same 
        signature as the execute function in this class).  

        :param module|object cmdmod: the subcommand to load.  
        :param str cmdname:     the name to assign the sub-command, used on the command-line to invoke it;
                                if None, the default name provided in the module will be used.
        """
        if not cmdname:
            cmdname = cmdmod.default_name
        subparser = self._subparser_src.add_parser(cmdname, help=cmdmod.help)
        subcmd = cmdmod.load_into(subparser)
        if not subcmd:
            subcmd = cmdmod
        self._cmds[cmdname] = subcmd

    def execute(self, args, config=None, log=None):
        """
        execute a subcommand from this command suite
        :param argparse.Namespace args:  the parsed arguments
        :param dict             config:  the configuration to use
        :param Logger              log:  the log to send messages to 
        """
        if not log:
            log = logging.getLogger(self.suitename)

        subcmd = getattr(args, self.suitename+"_subcmd")
        cmd = self._cmds.get(subcmd)
        if cmd is None:
            raise PDRCommandFailure(args.cmd, "Unrecognized subcommand of "+cmdname+": "+subcmd, 1)

        log = log.getChild(subcmd)
        return cmd.execute(args, config, log)

        

class PDRCLI(CommandSuite):
    """
    a class for executing pluggable commands via a command-line interface.
    """
    default_name = default_prog_name

    def __init__(self, progname=None, defconffile=None):
        if not progname:
            progname = self.default_name

        super(PDRCLI, self).__init__(progname, None)
        self.parser = define_opts(self.suitename)
        self._subparser_src = self.parser.add_subparsers(title="commands", dest="cmd")
        self._defconffile = defconffile
        
        self._cmds = {}
        self._next_exit_offset = 10

    def parse_args(self, args):
        """
        parse the given list of arguments according to the current argument configuration
        :param list args:  the command line arguments where the first item is the first argument
        """
        return self.parser.parse_args(args)

    def load_subcommand(self, cmdmod, cmdname=None, exit_offset=None):
        """
        load a subcommand into this suite of subcommands.  

        The cmdmod arguemnt is a module or object that must specify a load_into() function, a help string 
        property, and default_name string property.  The load_into() should accept two arguments: an 
        ArgumentParser instance and a string giving the name that the command suite should be accessed by
        (which can be None to use the default name).  Its implementation should load its command-line option 
        and argument defintions into the ArgumentParser.  It should return either None or CommandSuite 
        instance.  If None, then the given cmd module/object must also include an execute() function (that 
        has the same signature as the execute function in the CommandSuite class).  

        :param module|object cmdmod: the subcommand to load.  
        :param str     cmdname: the name to assign the sub-command, used on the command-line to invoke it;
                                if None, the default name provided in the module will be used.
        :param int exit_offset: an integer offset to add to any status values that resutl from a 
                                  PDRCommandFailure is raised via the execute() command.  
        """
        if not hasattr(cmdmod, "load_into"):
            raise StateException("command module/object has no load_into() function: " + repr(cmdmod))
        if not cmdname:
            cmdname = cmdmod.default_name
        if not exit_offset:
            taken = [c[1] for c in self._cmds.values()]
            while self._next_exit_offset in taken:
                self._next_exit_offset += 10
            exit_offset = self._next_exit_offset
            self._next_exit_offset += 10
        if not isinstance(exit_offset, int):
            raise TypeError("load(): exit_offset not an int")

        subparser = self._subparser_src.add_parser(cmdname, help=cmdmod.help)
        cmd = cmdmod.load_into(subparser)
        if not cmd:
            cmd = cmdmod
        self._cmds[cmdname] = (cmd, exit_offset)

    def configure_log(self, args, config):
        """
        set-up logging according to the command-line arguments and the given configuration.
        """
        loglevel = (args.debug and logging.DEBUG) or cfgmod.NORMAL

        if not args.logfile and 'logfile' not in config:
            config['logfile'] = self.suitename + ".log"
        if 'logdir' not in config:
            config['logdir'] = config.get('working_dir', os.getcwd())
        
        if args.logfile:
            # if logfile given on cmd-line, it will always go into the working dir
            config['logfile'] = os.path.join(config.get('working_dir', os.getcwd()), args.logfile)
        cfgmod.configure_log(level=loglevel, config=config)

        if not args.quiet:
            level = logging.INFO
            format = self.suitename + " %(levelname)s: %(message)s"
            if args.verbose:
                level = (args.debug and logging.DEBUG) or cfgmod.NORMAL
                format = "%(name)s %(levelname)s: %(message)s"
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(level)
            handler.setFormatter(logging.Formatter(format))
            logging.getLogger().addHandler(handler)

        log = logging.getLogger("cli."+self.suitename)
        if args.verbose:
            log.info("FYI: Writing log messages to %s", cfgmod.global_logfile)

        return log

    def load_config(self, args):
        """
        load the configuration according to the specified arguments.  A specific config file can be 
        specified via --config, and --in-live-sys will pull the configuration from an available 
        configuration service (the former overrides the latter).  A configuration service is detected 
        when the OAR_CONFIG_SERVICE environment variable is set to the service URL.  If neither are set,
        the default configuration file, set at construction, will be loaded

        :param argparse.Namespace args:  the parsed command line arguments
        :rtype:  dict
        :return:  the configuration data
        """
        if args.conf:
            config = cfgmod.load_from_file(args.conf)
        elif args.livesys:
            if not cfgmod.service:
                raise PDRCommandFailure(args.cmd,
                                        "Live system not detected; config service not availalbe", 2)
            config = cfgmod.service.get(OAR_CONFIG_APP)
        elif self._defconffile and os.path.isfile(self._defconffile):
            config = cfgmod.load_from_file(self._defconffile)
        else:
            config = {}
        return config
                
    def execute(self, args, config=None, siptype='cli'):
        """
        execute the command given in the arguments
        :param list|object args:   the program arguments (including the command name).  Typically, 
                                     this is a string list; if it isn't, it's assumed to be an 
                                     already parsed version of the arguments--i.e., an 
                                     argparse.Namespace instance.  
        """
        if isinstance(args, list):
            args = parse_args(args)
        cmd = self._cmds.get(args.cmd)
        if cmd is None:
            raise PDRCommandFailure(args.cmd, "Unrecognized command: "+args.cmd, 1)

        if config is None:
            config = self.load_config(args)
        if 'sip_type' in config:
            config = extract_cli_config(config, siptype)
        if args.workdir:
            if not os.path.isdir(args.workdir):
                raise PDRCommandFailure(args.cmd, "Working dir is not an existing directory: "+args.workdir, 2)
            config['working_dir'] = args.workdir
        proglog = self.configure_log(args, config)

        try:
            cmd[0].execute(args, config, proglog.getChild(args.cmd))
        except PDRCommandFailure as ex:
            ex.cmd = args.cmd
            ex.stat += cmd[1]
            raise ex
        except ConfigurationException as ex:
            raise PDRCommandFailure(args.cmd, "Configuration error: "+str(ex), 2, ex)


def extract_cli_config(config, siptype="cli"):
    """
    from a common configuration shared with the various publication services, 
    extract the bits needed by the command line interface
    """
    if 'sip_type' not in config:
        # this is the old-style configuration, return it unchangesd
        return config

    if siptype not in config['sip_type']:
        raise ConfigurationException("CLI config: "+siptype+" missing as an sip_type")
    out = deepcopy(config)
    del out['sip_type']
    out = cfgmod.merge_config(config['sip_type'][siptype], out)

    return out

