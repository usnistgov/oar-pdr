"""
Module providing client-side support for the RMM ingest service.  
"""
import os, sys, shutil, logging, requests
from collections import Mapping, Sequence

from ..exceptions import (StateException, ConfigurationException, PDRException,
                          NERDError)
from ..utils import write_json, read_nerd

def submit_for_ingest(record, endpoint, name=None,
                      authkey=None, authmeth='qparam'):
    """
    Send the given JSON data-object to the ingest service.

    :param record  dict:  the NERDm record object to be ingested
    :param endpoint str:  the URL endpoint for the ingest service to use.  
    :param name     str:  a name to refer to the input record if things go wrong.
    :param authkey  str:  an authorization token; this should be None if no
                             token is required.
    :param authmeth str:  the method to use to send the authorization token; 
                             recognized values are 'header' (send via an 
                             Authorization header field) or 'qparam' (send
                             as a query parameter to the URL).  If not provided,
                             'qparam' is assumed.

    :raises TypeError:          if the input is not a Mapping (dict-like) object.
    :raises IngestClientError:  raised ingest fails due to a client problem 
                                such as the record is found to be invalid.
    :raises IngestServerError:  raised if ingest fails due to a server error or 
                                otherwise does not respond.  
    :raises IngestAuthrError:   raised if the ingest fails due to an 
                                authorization error.  
    """
    hdrs = None
    if authkey:
        if authmeth == 'header':
            hdrs = { "Authorization": "Bearer "+authkey }
        elif '?' in endpoint:
            endpoint += "&auth="+authkey
        else:
            endpoint += "?auth="+authkey
    
    try:
        resp = requests.post(endpoint, json=record, headers=hdrs)
        if resp.status_code >= 500:
            raise IngestServerError(resp.status_code, resp.reason, name)
        elif resp.status_code == 401:
            raise IngestAuthzError(resp.status_code, resp.reason, name)
        elif resp.status_code == 400:
            errs = resp.json()
            raise NotValidForIngest(errs, resp.status_code, resp.reason, name)
        elif resp.status_code >= 400:
            raise IngestClientError(resp.status_code, resp.reason, name)
        elif resp.status_code != 200:
            raise IngestServerError(resp.status_code, resp.reason, name,
                            message="Unexpected response from server: {0} {1}"
                                    .format(resp.status_code, resp.reason))
    except ValueError as ex:
        if resp.text and ("<body" in resp.text or "<BODY" in resp.text):
            raise IngestServerError(message="HTML returned where JSON expected "+
                                    "(is service URL correct?)")
        else:
            raise IngestServerError(message="Unable to parse response as JSON "+
                                    "(is service URL correct?)")
    except requests.RequestException as ex:
        msg = "Trouble connecting to ingest service"
        if ex.request:
            msg += " via " + ex.request.url
        msg += ": "+ str(ex)
        raise IngestServerError(message=msg, cause=ex)
    
def get_endpoint(config):
    """
    return the URL to use as the ingest service endpoint based on the contents
    of the given configuration object.  None is returned if an endpoint is not 
    configured.
    """
    if not config.get("service_endpoint"):
        return None
    return config['service_endpoint']

class IngestClient(object):
    """
    Class that manages NERDm records for submission to the RMM ingest service.

    To enable asynchronous and auto-submits, 
    this class manages a holding area for records to be ingested below a single 
    directory on disk.  Within it are 4 subdirectories used to indicate the 
    ingest state of a record.  The staging subdirectory holds records (each in 
    an individual JSON file) that are ready to be ingested.  A file is moved to 
    the inprogress subdirectory while the record is being submitted to the 
    ingest service.  If the service responds with success, the file is moved to 
    the succeeded subdirectory.  If the service responds with client error 
    (4xx), it is moved to a failed subdirectory.  If the service responds with 
    a server error (5xx, or otherwise does not respond), the record is moved 
    back to the staging subdirectory so that a re-attempt can be tried later.  
    """
    def __init__(self, config, log=None):
        if not log:
            log = logging.getLogger("InjestClient")
        self.log = log
        
        if not config:
            config = {}
        self._cfg = config
        base = self._cfg.get('data_dir')
        missing = [name for name in 
                   "staging_dir succeeded_dir failed_dir inprogress_dir".split()
                   if not self._cfg.get(name)]
        if not base and missing:
            raise ConfigurationException("Missing config params: need '"+
                                         "', '".join(missing) +
                                         "' (or 'data_dir')")

        try:
            if missing and not os.path.exists(base):
                mdir = base
                os.mkdir(mdir)
                
            self._inprogdir  = self._cfg.get('inprogress_dir',
                                             os.path.join(base, "inprogress"))
            self._stagedir   = self._cfg.get('staging_dir',
                                             os.path.join(base, "staging"))
            self._successdir = self._cfg.get('succeeded_dir',
                                             os.path.join(base, "succeeded"))
            self._faildir    = self._cfg.get('failed_dir',
                                             os.path.join(base, "failed"))

            for mdir in (self._inprogdir, self._stagedir, self._successdir,
                         self._faildir):
                if not os.path.exists(mdir):
                    os.mkdir(mdir)
                    
        except OSError as ex:
            raise StateException("Failed to create needed directory: {0}: {1}"
                                 .format(mdir, str(ex)))

        self._endpt = get_endpoint(self._cfg)
        if self._endpt and not self._endpt.startswith('https://'):
            self.log.warn("Non-HTTPS endpoint for ingest service: " +
                          self._cfg.get("service_endpoint","?"))
        self._auth = [self._cfg.get('auth_method', 'qparam'),
                      self._cfg.get('auth_key', "")]
        if self._auth[0] not in ["qparam", "header"]:
            self.log.warn("authorization method not recognized: " +
                          self._auth[0] + "; reverting to 'header'")
            self._auth[0] = 'header'

        self.submit_mode = self._cfg.get("submit", "named")
        if self.submit_mode not in "named all none":
            self.log.warn("submit config value not recognized: %s",
                          self.submit_mode)

    @property
    def endpoint(self):
        """
        The service endpoint URL
        """
        return self._endpt

    def stage(self, record, name=None):
        """
        write the given NERDm record to a file in JSON format in the staging
        area for later submission to the ingest service.

        :param record dict:   the NERDm record object to be ingested
        :param name    str:   a name to give to the record filename (without
                              an extension).  If None, a name will be
                              generated.
        """
        if not isinstance(record, Mapping):
            raise TypeError("stage(): record not a JSON object; got "+
                            type(record))
        if not record.get('@id'):
            raise ValueError("Input does not look like a valid NERDm record; "+
                             "missing @id")
        if not name:
            name = os.path.split(record.get('@id'))[-1]

        outfile = os.path.join(self._stagedir, name+".json")
        write_json(record, outfile)

    def staged_names(self):
        """
        return the names of records that are currently staged for ingest

        :return list:  the list of names
        """
        return [os.path.splitext(f)[0] for f in os.listdir(self._stagedir)
                                       if not f.startswith('.') and
                                          not f.startswith('_') and
                             not os.path.isdir(os.path.join(self._stagedir, f))]

    def is_staged(self, name):
        """
        return True if there is a record with the given name is staged and 
        waiting to be submitted to the ingest service.
        """
        return name in self.staged_names()
            
    def submit_staged(self, name):
        """
        submit the record with the given name to the ingest service.  The 
        record file will be moved to the appropriate location based on the 
        outcome.  
        :raises IngestClientError:  raised ingest fails due to a client problem 
                                    such as the record is found to be invalid.
        :raises IngestServerError:  raised if ingest fails due to a server 
                                    error or otherwise does not respond.  
        :raises IngestAuthzError:   raised if the ingest fails due to an 
                                    authorization error.  
        :raises StateException:     raised if an error occurs while reading 
                                    the record file or moving the file between
                                    directories.  
        """
        if not self._endpt:
            raise ConfigurationException("No service endpoint provided in "+
                                         "configuration (service_endpoint)")
        
        recfile = os.path.join(self._stagedir, name+".json")
        if not os.path.exists(recfile):
            raise IngestFileNotStaged(name)
        try:
            shutil.move(recfile, self._inprogdir)
            recfile = os.path.join(self._inprogdir, name+".json")
            rec = read_nerd(recfile)

            try:

                submit_for_ingest(rec, self._endpt, name,
                                  self._auth[1], self._auth[0])

            except NotValidForIngest as ex:
                # the file is bad, send it to jail
                self.log.error("{0}: invalid record ({1} {2}):"
                          .format(name, ex.status, ex.reason))
                self._report_validation_errors(ex.errors, name)
                shutil.move(recfile, self._faildir)
                raise
            except IngestServerError as ex:
                # server's fault; try again later
                self.log.warn("Ingest Server problem: {0} (will try again later)"
                              .format(str(ex)))
                shutil.move(recfile, self._stagedir)
                raise
            except IngestClientError as ex:
                # our fault; we're probably calling it wrong; (resubmit after
                # code is fixed!)
                self.log.error("Bad call to ingest services: got response: " +
                               str(ex.status) + " " + ex.reason)
                shutil.move(recfile, self._stagedir)
                raise
            except Exception as ex:
                # Huh?  (resubmit after code is fixed!)
                self.log.error("Unexpected error during call to ingest "+
                               "service: " + str(ex))
                shutil.move(recfile, self._stagedir)
                raise

            # success; send file to millionaire acres
            shutil.move(recfile, self._successdir)
            
        except OSError as ex:
            # problem moving file
            if recfile.startswith(self._inprogdir):
                state = ("in-progress", "success")
            else:
                state = ("stage", "in-progress")
            msg = "{0}: Failed to move {1} file to {2}: {3}" \
                  .format(name, state[0], state[1], str(ex))
            self.log.exception(msg)
            raise StateException(msg, cause=ex)
        
        except (IOError, NERDError) as ex:
            # problem reading file
            self.log.exception("Problem reading data from JSON file, {0}: {1}"
                               .format(recfile, str(ex)))
            try:
                shutil.move(recfile, self._faildir)
            except OSError as e:
                msg = "Problem moving file from {0} to {1}: {3}" \
                      .format(recfile, self._faildir, str(e))
                self.log.exception(msg)
                raise StateException(msg, cause=ex)

    def _report_validation_errors(self, errs, name):
        if isinstance(errs, (str, unicode)):
            # shouldn't happen
            errs = [ errs ]
        elif not isinstance(errs, Sequence):
            # shouldn't happen
            self.log.warn("Unrecognized format for validation errors "+
                          "from ingest service")
            errs = [ str(errs) ]

        errmsg = "Validation Errors: \n * "
        errmsg += "\n * ".join([str(e) for e in errs])
        self.log.error(errmsg)

        # let's write the validation errors next to the record file
        with open(os.path.join(self._faildir, name + ".err.txt"),'w') as fd:
            fd.write(errmsg)
            fd.write("\n")
                    

    def submit_all(self):
        """
        submit all available records to the ingest service.

        :return dict:  3 lists accessed via the keys, 'succeeded', 'failed', 
                          'skipped', each listing the names of records that 
                          ended up in that state after submitting all to the 
                          ingest service.
        :raises IngestAuthzError:   raised if the ingest fails due to an 
                                    authorization error.  
        :raises OSError:            raised if an error occurs while reading 
                                    the record file or moving the file between
                                    directories.  
        """
        succeeded = []
        failed = []
        skipped = []
        for rec in self.staged_names():
            try:
                self.submit_staged(rec)
                succeeded.append(rec)
            except (NotValidForIngest, IngestServerError) as ex:
                failed.append(rec)

            # Let IngestClientError break the loop, because it's probably
            # a programming error somewhere.

        return {
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped
        }

    def submit(self, name=None):
        """
        Carry out the default submit action as controlled by the config
        property, 'submit'.  The possible values are 'named' (submit the 
        record with the given name), 'all' (submit all records available 
        in the staging area), or 'none' (submit no records).
        """
        staged = self.staged_names()
        if self.submit_mode == "named":
            if name:
                self.submit_staged(name)
                return { "succeeded": [name], "failed": [], "skipped": [] }
            else:
                self.log.warn("submit mode is named, but record name not "+
                              "provided")
                return { "succeeded": [], "failed": [],
                         "skipped": [n for n in staged if n==name] }

        elif self.submit_mode == "all":
            return self.submit_all()

        return { "succeeded": [], "failed": [], "skipped": staged }

                


class IngestServiceException(PDRException):
    """
    an exception indicating a problem using the ingest service.
    """

    def __init__(self, message, http_code=None, http_reason=None, name=None,
                 cause=None):
        super(IngestServiceException, self).__init__(message, cause=cause)
        self.status = http_code
        self.reason = http_reason
        self.recname = name

class IngestServerError(IngestServiceException):
    """
    an exception indicating an error occurred on the server-side while 
    trying to access the ingest service.  

    This exception includes three extra public properties, `status`, `reason`, 
    and `recname` which capture the HTTP response status code, the associated 
    HTTP response message, and (optionally) a name for the record being 
    submitted to it.  
    """

    def __init__(self, http_code=None, http_reason=None, name=None, message=None,
                 cause=None):
        if not message:
            message = "Ingest server-side error occurred"
            if name:
                message += " while processing " + name
            message += ": {0} {1}".format(http_code, http_reason)
          
        super(IngestServerError, self).__init__(message, http_code, http_reason,
                                                name, cause)

class IngestClientError(IngestServiceException):
    """
    an exception indicating an error occurred on the client-side while 
    trying to access the ingest service.  

    This exception includes three extra public properties, `status`, `reason`, 
    and `recname` which capture the HTTP response status code, the associated 
    HTTP response message, and (optionally) a name for the record being 
    submitted to it.  
    """

    def __init__(self, http_code, http_reason, name=None, message=None,
                 cause=None):
        if not message:
            message = "Ingest server-side error occurred"
            if name:
                message += " while processing " + name
            message += ": {0} {1}".format(http_code, http_reason)
          
        super(IngestClientError, self).__init__(message, http_code, http_reason,
                                                name, cause)

class NotValidForIngest(IngestClientError):
    """
    an error indicating that the submitted record to the ingest service is 
    not compliant with the JSON spec and/or the NERDm schema and has been 
    rejected.  

    This exception includes a public property, `errors`, which should be a 
    list of strings indicating the reasons why the submitted record is 
    invalid.  
    """
    
    def __init__(self, errors, http_code=400, http_reason="", name=None,
                 message=None, cause=None):
        if not message:
            message = ""
            if name:
                message += name + ": "
            message += "Record rejected from ingest due to validation errors"
        super(NotValidForIngest, self).__init__(http_code, http_reason, name,
                                                message, cause)
        self.errors = errors

class IngestAuthzError(IngestClientError):
    """
    an error indicating the client did not provide correct authorization
    to the ingest service.  
    """
    pass


