"""
A web service front-end to the PrePubMetadataService.
"""
import os, logging, json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from .. import PublishSystem
from .serv import (PrePubMetadataService, SIPDirectoryNotFound,
                   ConfigurationException, StateException)

log = logging.getLogger(PublishSystem().subsystem_abbrev).getChild("webserver")

DEF_BASE_PATH = "/midas/"

class PrePubMetadataWebServer(HTTPServer, PublishSystem):
    """
    a dedicated web server for serving pre-publication metadata for the 
    pre-publication landing page service.
    """

    def __init__(self, server_address, config):
        self.base_path = config.get('base_path', DEF_BASE_PATH)
        self.mdsvc = PrePubMetadataService(config)
        self.reqlim = 0
        super(PrePubMetadataWebServer, self).__init__(server_address,
                                                PrePubMetadataRequestHandler)

    def handle_limited_requests(self):
        while self.reqlim > 0:
            self.handle_request()
            self.reqlim -= 1

class PrePubMetadataRequestHandler(BaseHTTPRequestHandler):
    """
    An HTTP handler that will take requests in the form of an identifier 
    and return the associated metadata.
    """

    def __init__(self, req, addr, srvr):
        self.code = 0
        BaseHTTPRequestHandler.__init__(self, req, addr, srvr)

    def do_GET(self):
        if not self.path.startswith(self.server.base_path):
            self.code = 404
            self.send_error(self.code, "Not found")
            self.end_headers()
            return

        id = self.path[len(self.server.base_path):]
        if '/' in id:
            id = id[:id.index('/')]

        try:
            mdata = self.server.mdsvc.resolve_id(id)
        except SIPDirectoryNotFound, ex:
            #TODO: consider sending a 301
            self.code = 404
            self.send_error(self.code,
                            "Dataset with ID={0} not available".format(id))
            self.end_headers()
            return
        except Exception, ex:
            log.exception("Internal error: "+str(ex))
            self.code = 500
            self.send_error(self.code, "Internal error: "+ str(ex))
            self.end_headers()
            return

        self.code = 200
        self.send_response(self.code)
        self.send_header('ContentType', 'application/json')
        self.end_headers()

        json.dump(mdata, self.wfile, indent=4, separators=(',', ': '))

    def log_message(self, fmt, *args, **kwds):
        if self.code >= 500:
            log.error(fmt, *args, **kwds)
        elif self.code >= 400:
            log.error(fmt, *args, **kwds)
        else:
            log.info(fmt, *args, **kwds)

def retrieve_configuration(serverport):
    """
    retrieve the metadata server's configuration from the configuration server
    """
    raise NotImplemented

def lookup_config_server(serverport):
    """
    consult the discovery service to get the location of the configuration 
    service.
    """
    raise NotImplemented

def _define_cli_options(progname):
    from argparse import ArgumentParser

    description = """launch the pre-publication metadata webservice."""
    epilog = None

    parser = ArgumentParser(progname, None, description, epilog)
    
    parser.add_argument('-c', '--config', type=str, dest='cfgfile',
                        metavar='FILE', default=None,
                        help="start the server with a configuration from the "+
                             "given file; if not provided, a configuration is "+
                             "retrieved from the configuration server")
    parser.add_argument('-p', '--port', type=int, dest='port', metavar="PORT",
                        default=0,
                        help="listen to this given port number; if not "+
                             "provided, the port will be gotten from the "+
                             "configuration.")
    parser.add_argument('-H', '--host', type=str, dest='host', 
                        metavar="HOSTNAME", default=None,
                        help="listen to this given port number; if not "+
                             "provided, the port will be gotten from the "+
                             "configuration.")
    parser.add_argument('-l', '--log-file', type=str, dest='logfile',
                        metavar="FILE", default=None,
                        help="write log messages to FILE")
    parser.add_argument('-C', '--config-server', type=str, dest='cfgsrv', 
                        metavar="ADDRESS[:PORT]", default=None,
                        help="use this server as the config server; if not "+
                             "provided, the location will be gotten from the "+
                             "discovery service")
    parser.add_argument('-d', '--daemonize', action='store_true', dest='detach',
                        help="launch into a separate thread")
    parser.add_argument('-D', '--discovery-server', type=str, dest='cfgsrv', 
                        metavar="ADDRESS[:PORT]", default=None,
                        help="use this server as the discovery server; if not "+
                             "provided, a default server will be consulted as "+
                             "needed")
    parser.add_argument('-L', '--response-limit', type=int, dest='reqlim',
                        default=0, metavar='NUM',
                        help="limit the number of requests that are accepted "+
                             "to NUM before exiting (0=run forever)")
    
    return parser

LOG_FORMAT = "%(asctime)s %(name) %(levelname)s: %(message)s"

def _configure_log(logfile, level=None, format=None):
    if level is None:
        level = logging.INFO
    if not format:
        format = LOG_FORMAT
    frmtr = logging.Formatter(format)

    hdlr = logging.FileHandler(logfile)
    hdlr.setLevel(level)
    hdlr.setFormatter(format)
    logging.getLogger().addHandler(hdlr)

def from_cli(args, progname="ppmdserve"):
    """
    Launch the web server from the command line.

    """
    parser = _define_cli_options(progname)
    opts = parser.parse_args(args)

    config = {}
    if opts.cfgfile:
        if not os.path.exists(opts.cfgfile):
            raise ConfigurationException("Config file not found: " +
                                         opts.cfgfile)

        with open(opts.cfgfile) as fd:
            if opts.cfgfile.endswith('.json'):
                config = json.load(fd)
            else:
                # YAML format
                raise NotImplemented

    else:
        # get configuration from the configuration service
        raise NotImplemented

    if not opts.detach:
        # send messages to screen, too
        logging.basicConfig(format=LOG_FORMAT, stream=sys.stdout)

    logfile = opts.logfile
    if not logfile:
        logfile = config.get('logfile', progname+".log")
        if not os.path.abspath(logfile):
            if 'OAR_LOG_DIR' in os.environ:
                logfile = os.path.join(os.environ['OAR_LOG_DIR'], logfile)
            elif 'OAR_HOME' in os.environ:
                logfile = os.path.join(os.environ['OAR_HOME'], "var", "logs",
                                       logfile)
    
    _configure_log(logfile, config.get('logging_level'),
                   config.get('logging_format'))

    host = config.get('hostname', 'localhost')
    if opts.host:
        host = opts.host
    port = config.get('port', 7070)
    if opts.port:
        port = opts.port

    server = PrePubMetadataWebServer((host, port), config)

    if opts.reqlim:
        server.reqlim = opts.reqlim
        target = server.handle_limited_requests
    else:
        target = server.handle_forever
    thread = threading.Thread(target=target)
    if opts.detach:
        thread.daemon = True

    thread.start()



        

        
