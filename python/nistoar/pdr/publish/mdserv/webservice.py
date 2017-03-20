"""
A web service front-end to the PrePubMetadataService.
"""
import os, logging, json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from .. import PublishSystem
from .serv import PrePubMetadataService, SIPDirectoryNotFound

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
        super(PrePubMetadataWebServer, self).__init__(server_address,
                                                PrePubMetadataRequestHandler)

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

def retrieve_configuration():
    """
    retrieve the metadata server's configuration from the configuration server
    """
    raise NotImplemented

def _define_cli_options():
    raise NotImplemented

def from_cli():
    """
    Launch the web server from the command line.
    """
    raise NotImplemented


        

        
