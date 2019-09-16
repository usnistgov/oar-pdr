"""
A WSGI web service front-end to the PrePubMetadataService.

This module provides the most basic implementation of a WSGI application 
necessary for integration into a WSGI server.  It should be replaced with 
a framework-based implementation if any further capabilities are needed.
"""
import os, sys, logging, json, re
from wsgiref.headers import Headers
from cgi import parse_qs, escape as escape_qp

from .. import PublishSystem
from .serv import (PrePubMetadataService, SIPDirectoryNotFound, IDNotFound,
                   ConfigurationException, StateException)
from ....id import NIST_ARK_NAAN

log = logging.getLogger(PublishSystem().subsystem_abbrev).getChild("mdserv")

# DEF_BASE_PATH = "/midas/"
DEF_BASE_PATH = "/"

class PrePubMetadaRequestApp(object):
    """
    A WSGI-compliant service app for serving per-publication (draft) NERDm 
    metadata currently being editing by MIDAS and the PDR through a web service
    interface.  This interface sits in front of a PrePubMetadataService instance.

    Endpoints:
    GET /{dsid} -- return the NERDm metadata for record with the EDI-ID, dsid
    HEAD /{dsid} -- determine the existence of a pre-publication record with the 
        EDI-ID, dsid: the status is 200 if the record is available; 404, 
        otherwise.
    PATCH /{dsid} -- update the NERDm metadata for the record with the EDI-ID, 
        dsid, with the data provided in the input JSON document.
    GET/HEAD /{dsid}/_perm/{perm}/{userid} -- return nothing with status=200 if the 
        user identified by userid has the permission having the label, perm, on 
        the record with the EDI-ID, dsid.  If the user does not have permission,
        the status will be 404.  
    GET /{dsid}/{filepath} -- return the pre-publication version of the file 
        identified by filepath within the dataset with the EDI-ID, dsid.
    GET /{dsid}/_perm/{perm} -- return a listing of userids for users that have 
        the permission perm on on the dataset with the EDI-ID, dsid.
    GET /{dsid}/_perm/{perm}?user={userid} -- return a listing of userids matching
        the search constraint that have the permission perm on on the dataset with 
        the EDI-ID, dsid.  Currently, this will essentially return ["{userid}"] if
        that user has permission, and an empty list, if not.  
    GET /{dsid}/_perm -- return a JSON object summarizing the publically viewable 
        permissions set on dataset with EDI-ID, dsid; currently, this only returns
        {"read": "all"}.  
    GET /{dsid}/_perm?action={perm}&user={userid} - return the permissions matching 
        the given constraints on the dataset with EDI-ID, dsid.  
    """

    def __init__(self, config):
        self.base_path = config.get('base_path', DEF_BASE_PATH)
        self.mdsvc = PrePubMetadataService(config)

        self.filemap = {}
        for loc in ('review_dir', 'upload_dir'):
            dir = config.get(loc)
            if dir:
                self.filemap[dir] = "/midasdata/"+loc

        ucfg = config.get('update', {})
        self.update_authkey = ucfg.get("update_auth_key");

        # set up client to MIDAS API service that will give us update authorization
        self._midascl = None
        if ucfg.get('update_to_midas', ucfg.get('midas_service')):
            # set up the client if have the config data to do it unless
            # 'update_to_midas' is False
            self._midascl = midas.MIDASClient(ucfg.get('midas_service', {}))

    def handle_request(self, env, start_resp):
        handler = Handler(self.mdsvc, self.filemap, env, start_resp,
                          self.update_authkey, self._midascl)
        return handler.handle()

    def __call__(self, env, start_resp):
        return self.handle_request(env, start_resp)

app = PrePubMetadaRequestApp

class Handler(object):

    badidre = re.compile(r"[<>\s]")

    def __init__(self, service, filemap, wsgienv, start_resp, auth=None, mdcl=None):
        self._svc = service
        self._fmap = filemap
        self._env = wsgienv
        self._start = start_resp
        self._meth = wsgienv.get('REQUEST_METHOD', 'GET')
        self._hdr = Headers([])
        self._code = 0
        self._msg = "unknown status"
        self._authkey = auth
        self._midascl = mdcl

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
        ###DEBUG:
        log.debug("sending header: %s", str(self._hdr.items()))
        ###DEBUG:
        self._start(status, self._hdr.items())

    def handle(self):
        meth_handler = 'do_'+self._meth

        path = self._env.get('PATH_INFO', '/')[1:]

        if hasattr(self, meth_handler):
            return getattr(self, meth_handler)(path)
        else:
            return self.send_error(403, self._meth +
                                   " not supported on this resource")


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
                perm = filepath.split('/', 2)
                if perm[0] != "_perm":
                    return self.send_error(404, "meta-resource for id={0} not found"
                                           .format(dsid))
                if len(perm) < 3:
                    perm += [None, None]

                if self._env.get('QUERY_STRING'):
                    query = parse_qs(self._env.get('QUERY_STRING', ""))
                    return self.query_permissions(dsid, query, perm[1])

                return self.test_permission(dsid, perm[1], perm[2])

            else:
                return self.get_datafile(dsid, filepath)

        return self.get_metadata(dsid)

    def get_metadata(self, dsid):
        
        try:
            mdata = self._svc.resolve_id(dsid)
        except IDNotFound as ex:
            self.send_error(404,"Dataset with ID={0} not available".format(dsid))
            return []
        except SIPDirectoryNotFound as ex:
            # shouldn't happen
            self.send_error(404,"Dataset with ID={0} not available".format(dsid))
            return []
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return []

        self.set_response(200, "Identifier found")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()

        return [ json.dumps(mdata, indent=4, separators=(',', ': ')) ]

    def get_datafile(self, id, filepath):

        try:
            loc, mtype = self._svc.locate_data_file(id, filepath)
        except IDNotFound as ex:
            self.send_error(404,"Dataset with ID={0} not available".format(id))
            return []
        except SIPDirectoryNotFound as ex:
            # shouldn't happen
            self.send_error(404,"Dataset with ID={0} not available".format(id))
            return []
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return []
        if not loc:
            self.send_error(404, "Dataset (ID={0}) does not contain file={1}".
                                 format(id, filepath))

        xsend = None
        prfx = [p for p in self._fmap.keys() if loc.startswith(p+'/')]
        if len(prfx) > 0:
            xsend = self._fmap[prfx[0]] + loc[len(prfx[0]):]
            log.debug("Sending file via X-Accel-Redirect: %s", xsend)

        self.set_response(200, "Data file found")
        self.add_header('Content-Type', mtype)
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
            return answer({"read": "all"})
        
        if action not in ["update", "read"]:
            return self.send_error(404, "Unrecognized permission action: "+action)

        if action == "read":
            if not user:
                return answer(["all"])
            return self.send_error(200, "User has read permission")

        if action == "update":
            if not user:
                return self.send_error(400, "Query required for resource")
            if user == "all":
                return self.send_error(404,
                                       "Update permission is not available for all")
            if self._update_authorized_for(dsid, user):
                return self.send_error(200, "User has update permission")
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
            if query['user']:
                query['action'].append("update")
        if not query.get("user"):
            query['user'] = ["all"]

        out = {}
        if 'read' in query.get('action',[]):
            out['read'] = query['user']
        if 'update' in query.get('action',[]):
            out['update'] = []
            for user in query['user']:
                if user == "all":
                    continue
                user = escape_qp(user)
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

    def send_methnotallowed(self):
        self.set_response(405, meth + " not allowed")
        self.add_header('WWW-Authenticate', 'Bearer')
        self.add_header('Allow', 'GET')
        self.end_headers()
        return []

    def do_PATCH(self, path):
        """
        update the NERDm metadata associated with a given identifier
        """
        if not self.authorized_for_update():
            return self.send_unauthorized()

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
            
        if filepath:
            self.send_methnotallowed();

        return self.update_metadata(dsid)

    def update_metadata(self, dsid):
        """
        attempt to update the metadata for the identified record from the 
        uploaded JSON.
        """

        # make sure we have the proper content-type; if not provided, assume
        # input is JSON
        if 'CONTENT_TYPE' in self._env and \
           self._env['CONTENT_LENGTH'] != "application/json":
            log.error("Client provided wrong content-type: "+
                      self._env['CONTENT_LENGTH']);
            return self.send_error(415, "Unsupported input format");
            
        try:
            clen = int(self._env['CONTENT_LENGTH'])
        except KeyError, ex:
            log.exception("Content-Length not provided for input record")
            return self.send_error(411, "Content-Length is required")
        except ValueError, ex:
            log.exception("Failed to parse input JSON record: "+str(e))
            return self.send_error(400, "Content-Length is not an integer")

        doc = None
        try:
            bodyin = self._env['wsgi.input']
            doc = bodyin.read(clen)
            frag = json.loads(doc)
        except Exception, ex:
            log.exception("Failed to parse input JSON record: "+str(ex))
            if doc is not None:
              log.warn("Input document starts...\n{0}...\n...{1} ({2}/{3} chars)"
                       .format(doc[:75], doc[-20:], len(doc), clen))
            return self.send_error(400,
                                   "Failed to load input record (bad format?): "+
                                   str(ex))

        try:
            updated = self._svc.patch_id(dsid, frag)
        except IDNotFound as ex:
            self.send_error(404,"Dataset with ID={0} not available".format(dsid))
            return []
        except SIPDirectoryNotFound as ex:
            # shouldn't happen
            self.send_error(404,"Dataset with ID={0} not available".format(dsid))
            return []
        except InvalidRequest as ex:
            # if input is invalid or includes metadata that cannot be updated
            self.send_error(400,"Invalid input: "+str(ex));
            return []
        except Exception as ex:
            log.exception("Internal error: "+str(ex))
            self.send_error(500, "Internal error")
            return []

        self.set_response(200, "Updates accepted")
        self.add_header('Content-Type', 'application/json')
        self.end_headers()

        return [ json.dumps(updated, indent=4, separators=(',', ': ')) ]
