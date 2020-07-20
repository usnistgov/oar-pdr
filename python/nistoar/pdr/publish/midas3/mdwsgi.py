"""
A web service front end to the metadata managed via the MIDAS3PublishingService.

This service replaces the metadata service of the MIDAS (Mark I) SIP convention.  In 
the MIDAS3 convention, the MIDAS3PublishingService handles updates to the metadata.
This web service provides the public access to the metadata and the data files provided 
by the author to MIDAS.  
"""
import os, sys, logging, json, re
from wsgiref.headers import Headers
from cgi import parse_qs, escape as escape_qp
from collections import OrderedDict

from .. import PublishSystem
from ...exceptions import (SIPDirectoryNotFound, IDNotFound,
                           ConfigurationException, StateException)
from ...utils import read_json, build_mime_type_map
from . import midasclient as midas
from ...preserv.bagger.midas3 import MIDASSIP
from ....id import NIST_ARK_NAAN

pdrsys = PublishSystem()
log = logging.getLogger(pdrsys.system_abbrev)   \
             .getChild(pdrsys.subsystem_abbrev) \
             .getChild("m3mdserv")

DEF_BASE_PATH = "/midas/"

class MIDAS3DataAccessApp(object):
    """
    A WSGI-compliant service app for accessing data and metadata associated with a
    Submission Information Package (SIP).
    """
    def __init__(self, config):
        self.cfg = config
        level = config.get('loglevel')
        if level:
            log.setLevel(level)

        self.base_path = config.get('base_path', DEF_BASE_PATH)

        self.revdir = config.get('review_dir')
        self.upldir = config.get('upload_dir')

        self.filemap = OrderedDict()
        if self.revdir:
            self.filemap[self.revdir] = '/midasdata/review_dir'
        if self.upldir:
            self.filemap[self.upldir] = '/midasdata/upload_dir'

        self.prepubdir = config.get('prepub_nerd_dir')
        if not self.prepubdir:
            raise ConfigurationException("Missing config parameter: prepub_nerd_dir")
        self.postpubdir = config.get('postpub_nerd_dir')
        if not self.postpubdir:
            self.postpubdir = config.get('cachedir')
            if self.postpubdir:
                self.postpubdir = os.path.join(self.postpubdir, "_nerd")

        log.debug("Looking for records in:\n  %s\n  %s",
                  str(self.prepubdir), str(self.postpubdir))

        ucfg = config.get('update', {})
        self.update_authkey = ucfg.get("update_auth_key");

        # set up client to MIDAS API service that will give us update authorization
        self._midascl = None
        if ucfg.get('update_to_midas', ucfg.get('midas_service')):
            # set up the client if have the config data to do it unless
            # 'update_to_midas' is False
            self._midascl = midas.MIDASClient(ucfg.get('midas_service', {}),
                                         logger=log.getChild('midasclient'))

        # build regex that will match download URLs that use the PDR distribution service
        # baseurl = base url for downloading files via this service
        self.baseurl = self.cfg.get('download_base_url')  
        ddspath = self.cfg.get('datadist_base_urlpath', '/od/ds')
        if ddspath[0] != '/':
            ddspath = '/' + ddspath
        self.ddsre = re.compile(r'https?://[\w\.]+(:\d+)?'+ddspath)

        mimefiles = self.cfg.get('mimetype_files', [])
        self.mimetypes = build_mime_type_map(mimefiles)

    def handle_request(self, env, start_resp):
        handler = Handler(self, env, start_resp)
        return handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = MIDAS3DataAccessApp

class Handler(object):

    badidre = re.compile(r"[<>\s]")

    def __init__(self, app, wsgienv, start_resp):
        self.app = app
        self._dirs = (app.prepubdir, app.postpubdir)
        self._start = start_resp
        self._env = wsgienv
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        
        self._authkey = app.update_authkey
        self._fmap = app.filemap
        self._baseurl = app.baseurl
        self._distsvc = app.ddsre
        self._midascl = app._midascl

    def send_error(self, code, message):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], sys.exc_info())
        return []

    def send_ok(self, message="OK"):
        status = "{0} {1}".format(str(code), message)
        self._start(status, [], None)
        return []

    def add_header(self, name, value):
        # Caution: HTTP does not support Unicode characters (see
        # https://www.python.org/dev/peps/pep-0333/#unicode-issues);
        # thus, this will raise a UnicodeEncodeError if the input strings
        # include Unicode (char code > 255).
        e = "ISO-8859-1"
        self._hdr.add_header(name.encode(e), value.encode(e))

    def set_response(self, code, message):
        self._code = code
        self._msg = message

    def end_headers(self):
        status = "{0} {1}".format(str(self._code), self._msg)
        self._start(status, self._hdr.items())

    def handle(self):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')
        if '/' not in path:
            path += '/'
        if not path.startswith(self.app.base_path):
            return self.send_error(404, "Resource not found")
        path = path[len(self.app.base_path):].rstrip('/')

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path)
        else:
            return self.send_methnotallowed(self._meth)

    def do_GET(self, path):

        if not path:
            self.code = 403
            self.send_error(self.code, "No identifier given")
            return ["Server ready\n"]

        if path.startswith('/'):
            path = path[1:]
        parts = path.split('/')

        if parts[0] == "ark:":
            # support full ark identifiers
            if len(parts) > 2 and parts[1] == NIST_ARK_NAAN:
                dsid = parts[2]
            else:
                dsid = '/'.join(parts[:3])
            filepath = "/".join(parts[3:])
        else:
            dsid = parts[0]
            filepath = "/".join(parts[1:])
            
        if self.badidre.search(dsid):
            self.send_error(400, "Unsupported SIP identifier: "+dsid)
            return []

        if filepath:
            if filepath.startswith("_perm"):
                if not self.authorized_for_update():
                    return self.send_unauthorized()
                perm = filepath.split('/')
                if perm[0] != "_perm":
                    return self.send_error(404, "meta-resource for id={0} not found"
                                           .format(dsid))
                if len(perm) < 2:
                    perm += [None]
                elif len(perm) > 2:
                    return self.send_error(403, "Forbidden")

                return self.test_permission(dsid, perm[1])

            else:
                return self.send_datafile(dsid, filepath)

        return self.send_metadata(dsid)

    def do_POST(self, path):
        if not path:
            self.code = 403
            self.send_error(self.code, "No identifier given")
            return ["Server ready\n"]

        if path.startswith('/'):
            path = path[1:]
        parts = path.split('/')

        if parts[0] == "ark:":
            # support full ark identifiers
            if len(parts) > 2 and parts[1] == NIST_ARK_NAAN:
                dsid = parts[2]
            else:
                dsid = '/'.join(parts[:3])
            parts = parts[3:]
        else:
            dsid = parts[0]
            parts = parts[1:]
            
        if self.badidre.search(dsid):
            self.send_error(400, "Unsupported SIP identifier: "+dsid)
            return []

        if not parts or parts[0] != "_perm":
            return self.send_methnotallowed('POST')
        elif len(parts) > 2:
            return self.send_error(403, "Forbidden")
        if not self.authorized_for_update():
            return self.send_unauthorized()

        if "/json" not in self._env.get('CONTENT_TYPE', 'application/json'):
            return self.send_error(415, "Non-JSON input content type specified")
        
        try:
            bodyin = self._env.get('wsgi.input')
            if bodyin is None:
                return self.send_error(400, "Missing input query document")
            query = json.load(bodyin, object_pairs_hook=OrderedDict)
        except (ValueError, TypeError) as ex:
            if log.isEnabledFor(logging.DEBUG):
                log.error("Failed to parse input as JSON: %s", str(ex))
            return self.send_error(400, "Input not parseable as JSON")

        if len(parts) < 2:
            return self.query_permissions(dsid, query)
        return self.test_permission(dsid, parts[1], query.get('user'))
        
            
    def get_metadata(self, dsid):
        mdata = None
        mdfile = None
        try:
            for dir in self._dirs:
                if not dir:
                    continue
                mdfile = os.path.join(dir, dsid+".json")
                if os.path.isfile(mdfile):
                    mdata = read_json(mdfile)
                    log.info("Retrieving metadata record for id=%s from %s", dsid, mdfile)

        except ValueError as ex:
            log.exception("Internal error while parsing JSON file, %s: %s", mdfile, str(ex))
            raise ex

        return mdata
        

    def send_metadata(self, dsid):

        mdata = None
        try:
            mdata = self.get_metadata(dsid)
            if mdata is None:
                log.info("Metadata record not found for ID="+dsid)
                return self.send_error(404,
                                       "Dataset with ID={0} not being edited".format(dsid))
        except ValueError as ex:
            return self.send_error(500, "Internal parsing error")
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            return self.send_error(500, "Internal error")

        mdata = self._transform_dlurls(mdata)
        out = json.dumps(mdata, indent=4, separators=(',', ': '))

        self.set_response(200, "Identifier found")
        self.add_header('Content-Type', 'application/json')
        self.add_header('Content-Length', str(len(out)))
        self.end_headers()

        return [ out ]

    def _transform_dlurls(self, mdata):
        try: 
            sip = MIDASSIP.fromNERD(mdata, self.app.revdir, self.app.upldir)
            datafiles = sip.registered_files()
            
            pat = self._distsvc
            if self._baseurl and 'components' in mdata:
                for comp in mdata['components']:
                    # do a download URL substitution if 1) it looks like a
                    # distribution service URL, and 2) the file exists in our
                    # SIP areas.  
                    if 'downloadURL' in comp and pat.search(comp['downloadURL']):
                        # it matches
                        filepath = comp.get('filepath', pat.sub('',comp['downloadURL']))
                        if filepath in datafiles:
                            # it exists
                            comp['downloadURL'] = pat.sub(self._baseurl, comp['downloadURL'])

        except SIPDirectoryNotFound as ex:
            # (probably) because the record came from the post-pub cache
            log.debug("NOTE: No SIP directories found for ID=%s", str(midas.get('ediid')))
        
        return mdata

    def send_datafile(self, id, filepath):

        try:
            
            mdata = self.get_metadata(id)
            if mdata is None:
                log.info("send_datafile: Metadata record not found for ID="+id)
                return self.send_error(404,"Dataset with ID={0} not available".format(id))
            sip = MIDASSIP.fromNERD(mdata, self.app.revdir, self.app.upldir)
            
        except SIPDirectoryNotFound as ex:
            # shouldn't happen
            log.warn("No SIP directories for ID="+dsid)
            self.send_error(404,"Dataset with ID={0} not available".format(id))
            return []
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return []

        cmp = [c for c in mdata.get('components',[]) if c.get('filepath') == filepath]
        if len(cmp) == 0:
            return self.send_error(404, "Dataset (ID={0}) does not contain file={1}".
                                   format(id, filepath))
        if 'mediaType' in cmp[0] and cmp[0]['mediaType']:
            mtype = str(cmp[0]['mediaType'])
        else:
            mtype = self.app.mimetypes.get(os.path.splitext(loc)[1][1:],
                                           'application/octet-stream')

        loc = sip.find_source_file_for(filepath)
        if not loc:
            return self.send_error(404, "{0}: File={1} is not available from MIDAS".
                                   format(id, filepath))

        xsend = None
        prfx = [p for p in self._fmap.keys() if loc.startswith(p+'/')]
        if len(prfx) > 0:
            xsend = self._fmap[prfx[0]] + loc[len(prfx[0]):]
            log.debug("Sending file via X-Accel-Redirect: %s", xsend)

        self.set_response(200, "Data file found")
        self.add_header('Content-Type', mtype)
        self.add_header('Content-Disposition', os.path.basename(filepath))
        if xsend:
            self.add_header('X-Accel-Redirect', xsend)
        self.end_headers()

        if xsend:
            return []
        return self.iter_file(loc)

    def iter_file(self, loc):
        # this is the backup, inefficient way to send a file
        with open(loc, 'rb') as fd:
            buf = fd.read(5000000)
            yield buf

    def test_permission(self, dsid, action, user=None):
        def answer(data):
            self.set_response(200, "OK")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [ json.dumps(data, indent=4, separators=(',', ': ')) ]

        if not action:
            return self.send_error(404, "Missing permission action")
        
        if action not in ["update", "read"]:
            return self.send_error(404, "Unrecognized permission action: "+action)

        if action == "read":
            if not user:
                return answer({"user": "all"})
            return self.send_error(200, "User has read permission")

        if action == "update":
            if not user:
                return self.send_error(400, "Query required for resource")
            if user == "all":
                return self.send_error(404,
                                       "Update permission is not available for all")
            if self._update_authorized_for(dsid, user):
                return answer({"user": user})
            return self.send_error(404, "User does not have update permission")

        return self.send_error(404, "Permission not recognized")

    def _update_authorized_for(self, dsid, user):
        if self._midascl:
            return self._midascl.authorized(user, dsid)
        return True

    def query_permissions(self, dsid, query, action=None):
        def answer(data):
            self.set_response(200, "Query executed")
            self.add_header('Content-Type', 'application/json')
            self.end_headers()
            return [ json.dumps(data, indent=4, separators=(',', ': ')) ]

        if action and action not in ["read", "update"]:
            return self.send_error(404, "Permission not recognized")

        if action:
            query['action'] = [action]
        elif not query.get('action'):
            query['action'] = ["read"]
            if query.get('user'):
                query['action'].append("update")
        if not query.get("user"):
            query['user'] = ["all"]
        elif isinstance(query['user'], (str, unicode)):
            query['user'] = [query['user']]

        out = {}
        if 'read' in query.get('action',[]):
            out['read'] = query['user']
        if 'update' in query.get('action',[]):
            out['update'] = []
            for user in query['user']:
                if user == "all":
                    continue
                if self._update_authorized_for(dsid, user):
                    out['update'].append(user)

        if action:
            return answer(out[action])
        return answer(out)

    def do_HEAD(self, path):

        self.do_GET(path)
        return []
        
    def authorized_for_update(self):
        authhdr = self._env.get('HTTP_AUTHORIZATION', "")
        parts = authhdr.split()
        if self._authkey:
            return len(parts) > 1 and parts[0] == "Bearer" and \
                self._authkey == parts[1]
        if authhdr:
            log.warn("Authorization key provided, but none has been configured")
        return authhdr == ""

    def send_unauthorized(self):
        self.set_response(401, "Not authorized")
        self.add_header('WWW-Authenticate', 'Bearer')
        self.end_headers()
        return []

    def send_methnotallowed(self, meth):
        self.set_response(405, meth + " not allowed")
        self.add_header('WWW-Authenticate', 'Bearer')
        self.add_header('Allow', 'GET')
        self.end_headers()
        return []

    
