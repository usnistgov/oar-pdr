"""
Module providing client-side support for the RMM ingest service.  
"""
import os, sys, shutil, logging, json
from collections import Mapping, Sequence, OrderedDict

from .exceptions import (StateException, ConfigurationException, PDRException, NERDError)
from .utils import write_json, read_nerd, read_json
from ..doi import datacite as dc
from ..pdr import def_jq_libdir, def_schema_dir
from .. import jq
from ..nerdm import validate as valid8, constants as nerdconst

class DOIMintingClient(object):
    """
    a client class for minting and updating DataCite DOIs as part of the PDR preservation 
    process.
    """

    def __init__(self, config, log=None):
        """
        create the client
        """
        self._cfg = config
        if not log:
            log = logging.getLogger("OOIClient")
        self.log = log

        self.naan = self._cfg.get('minting_naan')
        if not self.naan:
            raise ConfigurationException("Missing required config param: minting_naan")
        if isinstance(self.naan, (float, int)):
            self.log.warn("DOIMintingClient: Numeric 'minting_naan' specified in configuration; "+
                          "converting to string")
            self.naan = str(self.naan)

        dccfg = self._cfg.get('datacite_api')
        if dccfg and not dccfg.get('service_endpoint'):
            raise ConfigurationException("Missing required datacite config param: service_endpoint")

        self.dccli = None
        if dccfg:
            creds = None
            if 'user' in dccfg or 'pass' in dccfg:
                creds = (dccfg.get('user'), dccfg.get('pass'))
            self.dccli = dc.DataCiteDOIClient(dccfg['service_endpoint'], creds, [self.naan],
                                              dccfg.get('default_data',{}))
        self._publish_by_default = self._cfg.get('publish', True)

        base = self._cfg.get('data_dir')
        missing = [name for name in 
                   "staging_dir reserved_dir published_dir failed_dir inprogress_dir".split()
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
            self._publishdir = self._cfg.get('published_dir',
                                             os.path.join(base, "published"))
            self._reservedir = self._cfg.get('reserved_dir',
                                             os.path.join(base, "reserved"))
            self._faildir    = self._cfg.get('failed_dir',
                                             os.path.join(base, "failed"))

            for mdir in (self._inprogdir, self._stagedir, self._publishdir,
                         self._reservedir, self._faildir):
                if not os.path.exists(mdir):
                    os.mkdir(mdir)
                    
        except OSError as ex:
            raise StateException("Failed to create needed directory: {0}: {1}"
                                 .format(mdir, str(ex)))

        self.submit_mode = self._cfg.get("submit", "named")
        if self.submit_mode not in "named all none":
            self.log.warn("submit config value not recognized: %s",
                          self.submit_mode)

        jqlib = self._cfg.get('jq_lib', def_jq_libdir)
        self._jqt = jq.Jq('datacite::resource2datacite', jqlib, ["nerdm2datacite:datacite"])

    def _nerd2dc(self, nerdm, validate=False):
        # convert a nerdm record to datacite.  This will do some basic checks on the nerdm record
        schema = nerdm.get('_schema')
        if not schema:
            schema = nerdm.get('$schema','')
        if not schema.startswith(nerdconst.core_schema_base):
            raise NERDError("Input does not appear to be a NERDm record; schema="+schema)
        if 'doi' not in nerdm:
            raise NERDError("NERDm record is missing doi property")

        if validate:
            try:
                valid8r = valid8.create_validator(self._cfg.get('schema_dir', def_schema_dir), nerdm)
                valid8r.validate(nerdm, strict=True, raiseex=True)
            except valid8.ValidationError as ex:
                raise NERDError("Input record (id=%s) is not a valid record" % nerdm.get("@id"), ex)
            except valid8.RefResolutionError as ex:
                raise NERDError("Input record (id=%s) has validation markup issues(?): %s" %
                                (nerdm.get("@id"), str(ex)), ex)

        else:
            # in lieu of full validation, let's just do some quick sanity checking
            missing = []
            for prop in "title landingPage contactPoint".split():
                if prop not in nerdm:
                    missing.append(prop)
            if missing:
                raise NERDError("NERDm record is missing properties: "+str(missing))

        try:
            return self._jqt.transform(json.dumps(nerdm))
        except RuntimeError as ex:
            raise NERDError("NERDm record (id=%s) not transformable: %s" %
                            (nerdm.get("@id"), str(ex)), ex)

    def stage(self, record, publish=None, name=None, validate=False):
        """
        convert the given NERDm record to a DataCite metadata submission and 
        file it in the staging area for later submission to DataCite.

        :param record  dict:  the NERDm record object to be ingested
        :param bool publish:  if True, submit the record to be set to the 
                              published state; otherwise, it will just be 
                              reserved.  
        :param name     str:  a name to give to the record filename (without
                              an extension).  If None, a name will be
                              generated.
        :except NERDError:  if there is a problem with the input NERDm record--
                            i.e. it is invalid or otherwise insufficient
        """
        if not isinstance(record, Mapping):
            raise TypeError("stage(): record not a JSON object; got "+
                            type(record))
        if not record.get('@id'):
            raise NERDError("Input does not look like a valid NERDm record; "+
                            "missing @id")
        if not name:
            name = os.path.split(record.get('@id'))[-1]

        if publish is None:
            publish = self._publish_by_default

        dcmd = self._nerd2dc(record, validate)
        if publish:
            dcmd['event'] = "publish"
        elif 'event' in dcmd:
            del dcmd['event']
            
        outfile = os.path.join(self._stagedir, name+".json")
        write_json(dcmd, outfile)

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
        :param str name:      name of the record to submit
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
        if not self.dccli:
            raise ConfigurationException("No service endpoint provided in "+
                                         "configuration (service_endpoint)")

        recfile = os.path.join(self._stagedir, name+".json")
        if not os.path.exists(recfile):
            raise IngestFileNotStaged(name)
        try:
            self._move_status_file(recfile, self._inprogdir)
            recfile = os.path.join(self._inprogdir, name+".json")
            rec = read_json(recfile)
            publish = (rec.get('event') == "publish")

            try:

                self.submit_rec(rec)

            except dc.DOIClientException as ex:
                # the file is bad, send it to jail
                if hasattr(ex.errdata, 'explain'):
                    self.log.error("%s: %s", name, ex.errdata.explain())
                else:
                    self.log.error("%s: invalid DOI request: %s", name, str(ex))
                self._move_status_file(recfile, self._faildir)
                raise
            except dc.DOIResolverError as ex:
                # server's fault; try again later
                self.log.warn("%s: unexpected service error: %s (will try again later)",
                              name, str(ex))
                shutil.move(recfile, self._stagedir)
                raise
            except dc.DOICommunicationError as ex:
                # network's fault; try again later
                self.log.warn("%s: unexpected comm error: %s (will try again later)",
                              name, str(ex))
                shutil.move(recfile, self._stagedir)
                raise
            except Exception as ex:
                # Huh?  (resubmit after code is fixed!)
                self.log.error("Unexpected error during call to ingest "+
                               "service: " + str(ex))
                shutil.move(recfile, self._stagedir)
                raise

            # success; send file to millionaire acres
            dest = (publish and self._publishdir) or self._reservedir
            self._move_status_file(recfile, dest)
            
        except (OSError, shutil.Error) as ex:
            # problem moving file
            if recfile.startswith(self._inprogdir):
                state = ("in-progress", (publish and "publish") or "reserve")
            else:
                state = ("stage", "in-progress")
            msg = "{0}: Failed to move {1} file to {2}: {3}" \
                  .format(name, state[0], state[1], str(ex))
            self.log.exception(msg)
            raise StateException(msg, cause=ex)
        
        except (IOError, ValueError) as ex:
            # problem reading file
            self.log.exception("Problem reading data from JSON file, {0}: {1}"
                               .format(recfile, str(ex)))
            try:
                self._move_status_file(recfile, self._faildir)
            except (OSError, IOError, shutil.Error) as e:
                msg = "Problem moving file from {0} to {1}: {3}" \
                      .format(recfile, self._faildir, str(e))
                self.log.exception(msg)
                raise StateException(msg, cause=ex)

    def _move_status_file(self, recfile, statdir):
        try:
            dest = os.path.join(statdir, os.path.basename(recfile))
            if os.path.isfile(dest):
                os.remove(dest)
            shutil.move(recfile, dest)
        except OSError as ex:
            self.log.exception("Problem moving status file: "+str(ex))

    def submit_rec(self, rec):
        """
        Submit a DataCite metadata record to DataCite to create the DOI or update its metadata
        """
        if not self.dccli:
            raise ConfigurationException("No service endpoint provided in "+
                                         "configuration (service_endpoint)")

        if 'doi' not in rec:
            raise ValueError("Datacite metadata record is missing req. prop: 'doi'")
        self.log.debug("%s metadata for doi:%s",
                       (rec.get('event') == 'publish' and "Publishing") or "Submitting", rec['doi'])

        doi = self.dccli.lookup(rec['doi'], relax=True)
        if doi.exists:
            if rec.get('event') == 'publish' and doi.state != dc.STATE_FINDABLE:
                self.log.debug("doi:%s: publishing currently %s record", rec['doi'], doi.state)
                doi.publish(rec)
            else:
                self.log.debug("doi:%s: updating %s record", rec['doi'], doi.state)
                doi.update(rec)
        else:
            
            if rec.get('event') == 'publish':
                self.log.debug("doi:%s: creating new findable record", rec['doi'])
                doi.publish(rec)
            else:
                self.log.debug("doi:%s: creating new draft record", rec['doi'])
                doi.reserve(rec)


    def submit_all(self):
        """
        submit all staged datacite records to the datacite service.

        :return dict:  3 lists accessed via the keys, 'succeeded', 'failed', 
                          'skipped', each listing the names of records that 
                          ended up in that state after submitting all to the 
                          ingest service.
        """
        succeeded = []
        failed = []
        skipped = []
        for rec in self.staged_names():
            try:
                self.submit_staged(rec)
                succeeded.append(rec)
            except dc.DOIResolverError as ex:
                failed.append(rec)

            # Let DOIClientExcpetion and other PDR exceptions break the loop, 
            # because it's probably a programming error somewhere.

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

    def find_named(self, name):
        """
        return the paths to cached records with the given name.  The result is 
        returned as a dictionary that maps states under which the record is found 
        ("pulished", "reserved", "failed", "staged", and "in_progress") to a file path for 
        the cached record.  Because a record with a given name can be ingested 
        multiple times, versions may exist under multiple states (such as 
        "published" from the first ingest, and "staged" for the subsequent ingest).
        """
        bases = OrderedDict([
            ("published", self._publishdir),
            ("reserved", self._reservedir),
            ("in_progress", self._inprogdir),
            ("staged", self._stagedir),
            ("failed", self._faildir)
        ])

        out = OrderedDict()
        for state in bases:
            path = os.path.join(bases[state], name+".json")
            if os.path.exists(path):
                out[state] = path

        return out



                                          
    
