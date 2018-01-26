"""
Utilities for obtaining a configuration for the metadata service
"""
import os, sys, logging, json, yaml

from .exceptions import ConfigurationException

oar_home = None
try:
    import uwsgi
    oar_home = uwsgi.opt.get('oar_home')
except ImportError:
    pass

if not oar_home:
    oar_home = os.environ.get('OAR_HOME', '/app/pdr')

def resolve_configuration(location):
    """
    return a dictionary for configuring the metadata service.  

    :param location str:  a filename, file path, or URL where the configuration
                          can be found.
    """
    if not location:
        raise ValueError("resolve_configration(): location arg not provided")
    
    if location.startswith('file:') or ':' not in location:
        # From a file in the filesystem
        if location.startswith('file://'):
            location = location[len('file://'):]
        elif location.startswith('file:'):
            location = location[len('file:'):]

        if not location.startswith('/') and os.path.isabs(location):
            cfgfile = os.path.join(oar_home, 'etc', 'config', location)
            if not os.path.exists(cfgfile):
                raise ConfigurationException("Config file not found: " +
                                             cfgfile)
        else:
            cfgfile = location
        return load_from_file(cfgfile)

    if location.startswith('configserver:'):
        # retrieve from a configuration service
        return load_from_service(location[len('configserver:'):])
            
    if ':' in location:
        # simple URL; do not feed a configuration service URL through this
        # as the response will be not parsed correctly
        raise NotImplementedError()

    raise ConfigurationException("Config file location could not be "+
                                 "interpreted: " + location)

def load_from_file(configfile):
    """
    read the configuration from the given file and return it as a dictionary.
    The file name extension is used to determine its format (with YAML as the
    default).
    """
    with open(configfile) as fd:
        if configfile.endswith('.json'):
            return json.load(fd)
        else:
            # YAML format
            return yaml.load(fd)

LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
_log_handler = None

def configure_log(logfile=None, level=None, format=None, config=None,
                  addstderr=False):
    """
    configure the log file, setting the output file, threshold, and format
    as necessary.  These can be provided explicitly or provided via the 
    configuration; the former takes precedence.  

    :param logfile str:  the path to the output logfile.  If given as a relative
                         path, it will be assumed that it is relative to a 
                         configured log directory.
    :param level int:    the logging threshold to set for sending messages to 
                         the logfile.  
    :param format str:   the formatting string to configure the logfile with
    :param config dict:  a configuration dictionary to draw logging configuration
                         values from.  
    :param addstderr bool:  If True, send ERROR and more severe messages to 
                         the standard error stream (default: False).
    """
    if not config:
        config = {}
    if not logfile:
        logfile = config.get('logfile', 'pdr.log')

    if not os.path.isabs(logfile):
        # The log directory can be set either from the configuration or via
        # the OAR_LOG_DIR environment variable; the former takes precedence
        deflogdir = os.path.join(oar_home,'var','logs')
        logdir = config.get('logdir', os.environ.get('OAR_LOG_DIR', deflogdir))
        if not os.path.exists(logdir):
            logdir = "/tmp"
        logfile = os.path.join(logdir, logfile)
    
    if level is None:
        level = logging.DEBUG
    if not format:
        format = LOG_FORMAT
    frmtr = logging.Formatter(format)

    global _log_handler
    _log_handler = logging.FileHandler(logfile)
    _log_handler.setLevel(level)
    _log_handler.setFormatter(frmtr)
    rootlogger = logging.getLogger()
    rootlogger.addHandler(_log_handler)
    rootlogger.setLevel(logging.DEBUG)

    if addstderr:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter(format))
        rootlogger.addHandler(handler)
        rootlogger.error("FYI: Writing log messages to %s",logfile)
        

def load_from_service(handle):
    """
    retrieve the metadata server's configuration from the configuration server.
    The handle identifies what configuration to pull from the service.  If not 
    fully specified, defaults are determined by lookup_config_server(), called
    internally.  The handle has the form:

       [[http:|https:]//server[:port]/]component/env

    where,
       [http:|https:]  is the web URL scheme to use, either unencrypted or 
                         encrypted (optional)
       server          is the host name of the configuration server
       part            is the port to access the server by
       component       the name of component registered with the service to 
                         retrieve the configuration for
       env             the environemnt (local|dev|test|prod) to retrieve the
                         configuration for.
    """
    raise NotImplementedError()

def lookup_config_server(serverport):
    """
    consult the discovery service to get the location of the configuration 
    service.
    """
    raise NotImplementedError()

