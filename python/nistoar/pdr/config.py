"""
Utilities for obtaining configuration data for services
"""
from __future__ import print_function
import os, sys, logging, json, yaml, collections, time, re
import requests
from urlparse import urlparse

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
global_logdir = None         # this is set when configure_log() is run
global_logfile = None        # this is set when configure_log() is run
_log_levels_byname = {
    "NOTSET":   logging.NOTSET,
    "DEBUG":    logging.DEBUG,
    "NORM":     15,
    "NORMAL":   15,
    "INFO":     logging.INFO,
    "WARN":     logging.WARNING,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

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
    :param addstderr bool or str:  If True, send ERROR and more severe messages 
                         to the standard error stream (default: False).  If 
                         provided as a str, it is the formatting string for 
                         messages sent to standard error.
    """
    global global_logdir
    global global_logfile
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
        global_logdir = logdir
        logfile = os.path.join(logdir, logfile)
    global_logfile = logfile
    
    if level is None:
        level = config.get('loglevel', logging.DEBUG)
    if not isinstance(level, int):
        level = _log_levels_byname.get(str(level), level)
    if not isinstance(level, int):
        raise ConfigurationException("Unrecognized loglevel value: "+str(level))
    
    if not format:
        format = config.get('logformat', LOG_FORMAT)
    frmtr = logging.Formatter(format)

    global _log_handler
    _log_handler = logging.FileHandler(logfile)
    _log_handler.setLevel(level)
    _log_handler.setFormatter(frmtr)
    rootlogger = logging.getLogger()
    rootlogger.addHandler(_log_handler)
    rootlogger.setLevel(logging.DEBUG-1)

    # jsonmerge is way too chatty at the DEBUG level
    if level >= logging.DEBUG:
        jmlevel = max(level, logging.INFO)
        logging.getLogger("jsonmerge").setLevel(jmlevel)

    # filelock is one level too chatty
    if level >= logging.DEBUG:
        logging.getLogger("filelock").setLevel(level+10)

    if addstderr:
        if not isinstance(addstderr, (str, unicode)):
            addstderr = format
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter(addstderr))
        rootlogger.addHandler(handler)
        rootlogger.error("FYI: Writing log messages to %s",logfile)
        
class ConfigService(object):
    """
    an interface to the configuration service
    """

    def __init__(self, urlbase, envprof=None):
        """
        initialize the service.
        :param urlbase str:  the base URL for the service which must include 
                             the scheme (either http: or https:), the server,
                             and the base path.  It can also include a port
                             number.
        :param envprof str:  the label indicating the default environment 
                             profile (usually, one of 'local', 'dev', 'test',
                             or 'prod').
        """
        self._base = urlbase
        self._prof = envprof
        if not self._base.endswith('/'):
            self._base += '/'

        u = urlparse(self._base)
        msg = "Insufficient config service URL: "+self._base+" ({0})"
        if not u.scheme:
            raise ConfigurationException(msg.format("missing http/https"))
        if not u.netloc:
            raise ConfigurationException(msg.format("missing server name"))

    def url_for(self, component, envprof=None):
        """
        return the proper URL for access the configuration for a given 
        component.  
        :param component   the name for the service or component that 
                              configuration data is desired for
        :param envprof     the desired version of the configuration given 
                              its environment/profile name.  If not provided,
                              the profile set at construction time will 
                              be assumed.
        """
        if not envprof:
            envprof = self._prof
        if envprof:
            component = '/'.join([component, envprof])
        
        return self._base + component

    def is_up(self):
        """
        return true if the service appears to be up.  
        """
        try:
            resp = requests.get(self.url_for("ready"))
            return resp.status_code and resp.status_code < 500
        except requests.exceptions.RequestException:
            return False

    def wait_until_up(self, timeout=10, rais=True, verboseout=None):
        """
        poll the service until responds.  
        :param timeout int:  the maximum number of seconds to wait before 
                             timing out.
        :param rais bool:    if True, raise a ConfifigurationException if
                             the timeout period is reached without a response 
                             from the service.
        :param verboseout file:  a file stream to send message about waiting;
                             if None, no messages are printed.
        :return bool:  True if the service is detected as up; False, if the 
                       timeout period is exceeded (unless rais=True).
        :raises ConfifigurationException: if rais=True and the timeout period
                       is exceeded without getting a response from the service.
        """
        start = time.time()
        if self.is_up():
            if verboseout:
                print("PDR: configuration service is ready", file=verboseout)
            return True
        if verboseout:
            print("PDR: Waiting for configuration service...", file=verboseout)

        updated = start
        while time.time()-start < timeout:
            if verboseout and time.time()-updated > 10:
                print("PDR: ...waiting...")
                updated = time.time()
                
            time.sleep(2)
            
            if self.is_up():
                if verboseout:
                    print("PDR: ...ready", file=verboseout)
                return True

        if verboseout:
            print("PDR: ...timed out!")        
        if rais:
            raise ConfigurationException("Waiting for configuration service "+
                                         "timed out")
        return False
        

    def get(self, component, envprof=None, flat=False):
        """
        retrieve the configuration for the service or component with the 
        given name.  Internally, this will transform the raw output from 
        the service into a configuration ready to give to the PDR component
        (including combining the profile specializations with default values).

        :param component str: the name for the service or component that 
                              configuration data is desired for
        :param envprof   str: the desired version of the configuration given 
                              its environment/profile name.  If not provided,
                              the profile set at construction time will 
                              be assumed.
        :param flat     bool: if true, keep the flat structure provided directly
                              by the config server.
        :return dict:  the parsed configuration data 
        """
        try:
            resp = requests.get(self.url_for(component, envprof))
            resp.raise_for_status()
            return self._extract(resp.json(), component, flat)
        except ValueError as ex:
            raise ConfigurationException("Config service response: "+str(ex))
        except requests.exceptions.RequestException as ex:
            raise ConfigurationException("Failed to access configuration for "+
                                         component + ": " + str(ex))

    def _extract(self, rawdata, comp="unknown", flat=False):
        return self.__class__.extract(rawdata, comp, flat)

    @classmethod
    def _deep_update(cls, defdict, upddict):
        for k, v in upddict.iteritems():
            if isinstance(v, collections.Mapping):
                defdict[k] = cls._deep_update(defdict.get(k, v.__class__()), v)
            else:
                defdict[k] = v
        return defdict

    _idxre = re.compile(r'\[(\d+)\]')
    @classmethod
    def _inflate(cls, flat):
        out = flat.__class__()
        for key in flat:
            levs = cls._idxre.sub(r'.\g<0>', key)
            levs = levs.split('.')
            pv = out
            while levs:
                lev = levs.pop(0)
                if len(levs) == 0: 
                    pv[lev] = flat[key]
                else:
                    if not isinstance(pv.get(lev), collections.Mapping):
                        pv[lev] = flat.__class__()
                    pv = pv[lev]

        return cls._cvtarrays(out)

    @classmethod
    def _cvtarrays(cls, md):
        if not isinstance(md, collections.Mapping):
            return md
        
        keys = md.keys()
        m = [cls._idxre.match(k) for k in keys]
        if all(m):
            ary = [( int(m[i].group(1)), md[keys[i]] ) for i in range(len(m))]
            ary.sort(lambda x,y: cmp(x[0], y[0]))
            return [ cls._cvtarrays(el[1]) for el in ary ]
        else:
            for k in keys:
                md[k] = cls._cvtarrays(md[k])
            return md

    @classmethod
    def extract(cls, rawdata, comp="unknown", flat=False):
        """
        extract component configuration from the config service response.
        This includes combining the environment/profile-specific data
        with the defaults.  
        """
        try:
            name = rawdata.get('name') or comp 
            vers = rawdata['propertySources']
        except KeyError, ex:
            raise ConfigurationException("Missing config param for label="+name+
                                         ": "+str(ex))
        if not isinstance(vers, list):
            raise ConfigurationException("Bad data schema for label="+name+
                                      ": wrong type for propertySources: "+
                                      str(type(vers)))
        if len(vers) == 0:
            raise ConfigurationException(name+": config data for app name not "+
                                         "found")

        try:
            out = vers[-1]['source']
            out.update(vers[0]['source'])
            if not flat:
                out = cls._inflate(out)
        except TypeError as ex:
            raise ConfigurationException("Bad data schema for label="+name+
                                         ": wrong type for propertySources "+
                                         "item: "+ str(type(vers)))
        except KeyError as ex:
            raise ConfigurationException("Bad data schema for label="+name+
                                         ": missing property: "+str(ex))

        return out

    @classmethod
    def from_env(cls):
        """
        return an instance of ConfigService based on environment variables
        or None if the proper environment is not set up.  To return an instance,
        the OAR_CONFIG_SERVICE environment variable needs to contain the 
        service's base URL.  If OAR_CONFIG_ENV is set, it will be taken as 
        the environment/platform label.  

        :raise ConfigurationException: if base URL in OAR_CONFIGSERVICE is 
                                       malformed.
        """
        if 'OAR_CONFIG_SERVICE' in os.environ:
            prof = os.environ.get('OAR_CONFIG_ENV')
            return ConfigService(os.environ['OAR_CONFIG_SERVICE'], prof)
        return None

service = None
try:
    service = ConfigService.from_env()
except:
    pass

def merge_config(primary, defconf):
    """
    do a deep merge of a default configuration dictionary into a primary one
    provided to an application.  A value in the primary dictionary will override
    those given in the default.  This function may update one of the input 
    dictionaries.

    :param primary dict:  the configuration dictionary provided to the 
                          application at run-time.
    :param defconf dict:  the default configuration dictionary 
    :return dict:   the merged dictionary.  This may be one of the input 
                    instances updated as needed (i.e. not a copy)
    """
    for key in primary:
        if isinstance(primary[key], collections.Mapping) and \
           isinstance(defconf.get(key), collections.Mapping):
            defconf[key] = merge_config(primary[key], defconf[key])
        else:
            defconf[key] = primary[key]

    return defconf

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

