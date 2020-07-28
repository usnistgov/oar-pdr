"""
The implementation module for the MIDAS-to-PDR publishing service (pubserver), Mark III version.  
It is designed to operate on SIP work areas created and managed by MIDAS for publishing.
"""
import os, logging, re, json, copy, time, threading, shutil
from collections import Mapping, OrderedDict
from copy import deepcopy

from ...exceptions import (ConfigurationException, StateException, 
                           SIPDirectoryNotFound, IDNotFound, PDRServiceException)
from ...preserv.bagger.midas3 import (MIDASMetadataBagger, UpdatePrepService, PreservationBagger,
                                      midasid_to_bagname, DEF_POD_DATASET_SCHEMA)
from ...preserv import PreservationStateError

from ...preserv import PreservationException
from ...preserv.bagit import NISTBag, DEF_MERGE_CONV
from ...preserv.service import status as ps
from ...preserv.service.service import MultiprocPreservationService
from ...utils import build_mime_type_map, read_nerd, write_json, read_pod
from ... import config as _configmod
from ....id import PDRMinter, NIST_ARK_NAAN
from ....nerdm.convert import Res2PODds, topics2themes
from ....nerdm.taxonomy import ResearchTopicsTaxonomy
from ....nerdm import validate
from .... import pdr
from .customize import CustomizationServiceClient

import ejsonschema as ejs
from ejsonschema import schemaloader

# we will use a relaxed version to validate potentially incomplete POD submissions
POD_DATASET_SCHEMA = re.sub(r'/v([^#]+)#/', '/relaxed-\g<1>#', DEF_POD_DATASET_SCHEMA)

bg_sync = False

from .. import PublishSystem, sys as pdrsys
log = logging.getLogger(pdrsys.system_abbrev)   \
             .getChild(pdrsys.subsystem_abbrev) 

class MIDAS3PublishingService(PublishSystem):
    """
    This service class manages creation of data publications based on inpug from 
    the MIDAS front-end tool, according to the MIDAS Mark 3 conventions.  

    This service manages the publishing process through four major capabilities:
      1.  It accepts POD records that describe a MIDAS submission record; this service 
          uses them to create and update PDR Submission Information Packages (SIPs).

      2.  It serves as an intermediary that temporarily transfer update control from 
          MIDAS to the PDR customization service.

      3.  It provides NERDm descriptions of SIP for presentation (via the landing page 
          service).  

      4.  It can complete the publishing process by converting the SIP to an AIP and 
          sending it to long-term-storage and ingesting it into the public PDR.

    This class takes a configuration dictionary at construction; the following
    properties are supported:

    :prop working_dir str #req:  an existing directory where working data can
                      can be stored.  
    :prop review_dir  str #req:  an existing directory containing MIDAS review
                      data directories
    :prop upload_dir  str #req:  an existing directory containing MIDAS upload
                      data directories
    :prop id_registry_dir str:   a directory to store the minted ID registry.
                      the default is the value of the working directory.
    :prop mimetype_files list of str ([]):   an ordered list of filepaths to 
                      files that map file extensions to default MIME types.  
                      Mappings in the latter files override those in the former 
                      ones.
    :prop id_minter dict ({}):  a dictionary for configuring the ID minter 
                      instance.
    :prop bagger dict ({}):  a dictionary for configuring the SIPBagger instance
                      used to process the SIP (see SIPBagger implementation 
                      documentation for supported sub-properties).  
    """

    def __init__(self, config, workdir=None, reviewdir=None, uploaddir=None,
                 idregdir=None):
        """
        initialize the service.

        :param config   dict:  the configuration parameters for this service
        :param workdir   str:  the path to the workspace directory where this
                               service will write its data.  If not provided,
                               the value of the 'working_dir' configuration 
                               parameter will be used.
        :param reviewdir str:  the path to the MIDAS-managed directory for SIPs 
                               in the review state.  If not provided,
                               the value of the 'review_dir' configuration 
                               parameter will be used.
        :param uploaddir str:  the path to the MIDAS-managed directory for SIPs
                               in the upload state.  If not provided,
                               the value of the 'upload_dir' configuration 
                               parameter will be used.
        """
        if not isinstance(config, Mapping):
            raise ValueError("MIDAS3PublishingService: config argument not a " +
                             "dictionary: " + str(config))
        self.cfg = config

        self.log = log.getChild("m3svc")

        # set some working areas
        self.workdir = None     # default location for output/internal data
        self.mddir = None       # location to write metadata bags
        self.nrddir = None      # location to place nerdm records for pre-publication md service
        self.podqdir = None     # location where POD records get queued to be processed
        self.storedir = None    # location to write out zipped bags before delivery to LTS
        if not workdir:
            workdir = self.cfg.get('working_dir')
        self._set_working_dir(workdir)

        if not reviewdir:
            reviewdir = self.cfg.get('review_dir')
        if not reviewdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "review_dir", sys=self)
        if not os.path.isdir(reviewdir):
            raise StateException("MIDAS review directory does not exist as a " +
                                 "directory: " + reviewdir, sys=self)
        self.reviewdir = reviewdir

        if not uploaddir:
            uploaddir = self.cfg.get('upload_dir')
        if not uploaddir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "upload_dir", sys=self)
        if not os.path.isdir(uploaddir):
            raise StateException("MIDAS Upload directory does not exist as a " +
                                 "directory: " + uploaddir, sys=self)
        self.uploaddir = uploaddir

        if not idregdir:
            idregdir = self.cfg.get('id_registry_dir', self.workdir)
        if not os.path.isdir(idregdir):
            raise StateException("ID Registry directory does not exist as a " +
                                 "directory: " + idregdir, sys=self)

        self._minter = self._create_minter(idregdir)

        # used for validating during updates (via patch_id())
        self._schemadir = self.cfg.get('nerdm_schema_dir', pdr.def_schema_dir)
        self._podvalid8r = None
        if self.cfg.get('require_valid_pod', True):
            if not self._schemadir:
                raise ConfigurationException("'reuqire_valid_pod' is set but cannot find schema dir")
            self._podvalid8r = validate.create_validator(self._schemadir, "_")


        # used to convert NERDm to POD
        self._nerd2pod = Res2PODds(pdr.def_jq_libdir, logger=self.log)

        # used to interact with the customization service
        if 'customization_service' not in self.cfg:
            raise ConfigurationException("Missing required config parameters: "+
                                         'customization_service', sys=self)
        self._custclient = CustomizationServiceClient(self.cfg.get('customization_service'),
                                                      logger=self.log.getChild("customclient"))

        self._bagging_workers = {}
        self.pressvc = MultiprocPreservationService(self.cfg.get('preservation_service',
                                                                 self._presv_config()))

    def _presv_config(self):
        comm = {
            "review_dir": self.reviewdir
        }
        for prop in "upload_dir id_minter mimetype_files".split():
            if prop in self.cfg:
                comm[prop] = self.cfg[prop]
            
        out = {
            "working_dir": self.workdir,
            "store_dir": self.storedir,
            "id_registry_dir": self.cfg.get('id_registry_dir', self.workdir),
            "auth_key": self.cfg.get('auth_key', 'INCORRECT_AUTH_KEY'),
            "auth_method": self.cfg.get('auth_method', "header"),
            "sip_type": {
                "midas3": {
                    "common": comm,
                    "preserv": {}
                }
            }
        }
        return out 
            

    def _set_working_dir(self, workdir):
        if not workdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "working_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir

        self.mddir = self.cfg.get('metadata_bags_dir', "mdbags")
        if not os.path.isabs(self.mddir):
            self.mddir = os.path.join(workdir, self.mddir)
            if not os.path.exists(self.mddir):  os.makedirs(self.mddir)
        self.nrddir = self.cfg.get('nerdm_serve_dir', "nrdserv")
        if not os.path.isabs(self.nrddir):
            self.nrddir = os.path.join(workdir,self.nrddir)
            if not os.path.exists(self.nrddir):  os.makedirs(self.nrddir)
        self.podqdir = self.cfg.get('pod_queue_dir', "podq")
        if not os.path.isabs(self.podqdir):
            self.podqdir = os.path.join(workdir, self.podqdir)
            if not os.path.exists(self.podqdir):  os.makedirs(self.podqdir)
        self.storedir = self.cfg.get('store_dir')
        if not self.storedir:
            self.log.warn("store_dir config param not set; setting it to %s",
                          os.path.join(workdir, "store"))
            self.storedir = "store"
        if not os.path.isabs(self.storedir):
            self.storedir = os.path.join(workdir, self.storedir)
            if not os.path.exists(self.storedir):  os.makedirs(self.storedir)

    def _create_minter(self, parentdir):
        cfg = self.cfg.get('id_minter', {})
        out = PDRMinter(parentdir, cfg)
        if not os.path.exists(out.registry.store):
            self.log.warn("Creating new ID minter")
        return out

    def restart_workers(self):
        """
        Examine the POD queue and restart worker threads for any pending POD files found
        """
        pending = set()
        for qdir in ["current", "next"]:
            poddir = os.path.join(self.podqdir, qdir)
            if not os.path.isdir(poddir):
                continue
            for podf in [f for f in os.listdir(poddir)
                                           if f.endswith(".json")]:
                pending.add(podf[:-len(".json")])

        for id in pending:
            worker = self._get_bagging_worker(id)
            if not worker.is_working():
                worker.launch()
        

    def wait_for_all_workers(self, timeout):
        """
        wait for all service threads to finish
        """
        for key in list(self._bagging_workers.keys()):
            worker = self._bagging_workers.get(key)
            if not worker:
                continue
            if worker.is_working() and worker._thread is not threading.current_thread():
                worker._thread.join()
            if worker.bagger.fileExaminer.running():
                worker.bagger.fileExaminer.waitForCompletion(timeout)

    def update_ds_with_pod(self, pod, async=True):
        """
        create or update a pre-publication dataset described by the given POD 
        record (from MIDAS).  This converts the POD to NERDm metadata, and both are 
        saved to the targeted metadata bag.  Afterwards, the files cited in the POD
        are reviewed to see if they have been updated and require further examination. 

        Much of the work creating and updating the dataset is done asynchronously
        in a separate thread.  PODs are placed in a two-position queue that includes
        the POD currently being processed and the next one in line.  If a third POD 
        update comes in, it replaces the next-in-line one.  If async=True, this 
        method returns after confirming the POD is valid; the conversion and 
        integration is done asynchronously.  If async=False, conversion is done 
        synchronously, but file examination is asynchronously.  
        """
        # First validate the POD
        if self.cfg.get('require_valid_pod', True):
            self._validate_pod(pod)

        return self._apply_pod_async(pod, async)

    def _validate_pod(self, pod):
        if self._podvalid8r:
            self._podvalid8r.validate(pod, schemauri=POD_DATASET_SCHEMA,
                                      strict=True, raiseex=True)
        else:
            self.log.warning("Unable to validate submitted POD data")

    def _create_bagger(self, id):
        cfg = self.cfg.get('bagger', {})
        if 'store_dir' not in cfg and 'store_dir' in self.cfg:
            cfg['store_dir'] = self.cfg['store_dir']
        if 'repo_access' not in cfg and 'repo_access' in self.cfg:
            cfg['repo_access'] = self.cfg['repo_access']
            if 'store_dir' not in cfg['repo_access'] and 'store_dir' in cfg:
                cfg['repo_access']['store_dir'] = cfg['store_dir']
        if 'doi_minter' not in cfg and 'doi_minter' in self.cfg:
            cfg['doi_minter'] = self.cfg['doi_minter']
        if not os.path.exists(self.workdir):
            os.mkdir(workdir)
        elif not os.path.isdir(self.workdir):
            raise StateException("Working directory path not a directory: " +
                                 self.workdir)

        bagger = MIDASMetadataBagger.fromMIDAS(id, self.mddir, self.reviewdir,
                                               self.uploaddir, cfg, self._minter)
        return bagger

    def _get_bagging_worker(self, id):
        worker = self._bagging_workers.get(id)
        if not worker:
            bagger = self._create_bagger(id)
            # bagger.prepare()
            worker = self.BaggingWorker(self, id, bagger, self.log)
            self._bagging_workers[id] = worker
        return worker

    def delete(self, id):
        """
        delete the working metadata bag for the given identifier.  Afterward, it must be recreated 
        via a call to update_ds_with_pod(id).
        """
        worker = self._bagging_workers.get(id)
        if not worker:
            bagger = self._create_bagger(id)
            worker = self.BaggingWorker(self, id, bagger, self.log)

        if os.path.exists(worker.bagger.bagdir):
            worker = self._get_bagging_worker(id)
            worker.delete_bag()
        self._drop_bagging_worker(worker)

        # now delete the built landing page
        nerdf = os.path.join(self.nrddir, worker.bagger.name+".json")
        if os.path.exists(nerdf):
            os.remove(nerdf)

    def _drop_bagging_worker(self, worker, timeout=None):
        if worker.is_working() and worker._thread is not threading.current_thread():
            worker._thread.join()
        worker.bagger.fileExaminer.waitForCompletion(timeout)
        worker.bagger.done()
        if worker.id in self._bagging_workers:
            del self._bagging_workers[worker.id]

    def _drop_all_workers(self, timeout=None):
        wids = list(self._bagging_workers.keys())
        for wid in wids:
            if wid in self._bagging_workers:
                self._drop_bagging_worker(self._bagging_workers[wid])

    def _apply_pod_async(self, pod, async=True):
        id = pod.get('identifier')
        if not id:
            # shouldn't happen since identifier is required for validity
            raise ValueError("POD record is missing required identifier")

        worker = self._get_bagging_worker(id)
        if not os.path.exists(worker.bagger.bagdir):
            # prep the bag synchronously (in case there's an issue)
            worker.bagger.prepare()

        worker.queue_POD(pod)

        if not worker.is_working():
            if async:
                worker.launch()
            else:
                worker.run("sync")
        return worker.bagger


    def serve_nerdm(self, nerdm, name=None):
        """
        export the given nerdm data to the export directory where it can be served to 
        clients (e.g. pre-publication landing page service)

        :param dict nerdm:   the nerdm record of a JSON file containing the data
        :param str   name:   the basename to use to store the data under; if not provided,
                             it will be generated from the EDI identifier.
        """
        nerdf = None
        if not isinstance(nerdm, Mapping):
            nerdm = read_nerd(nerdm)

        if not name:
            if 'ediid' not in nerdm:
                raise ValueError("serve_nerdm(): NERDm record is missing req. property, ediid")
            name = re.sub(r'^ark:/\d+/', '', nerdm['ediid'])

        # the NERDm metadata may be under-specified
        self._pad_nerdm(nerdm)
                        
        # first stage to a temp file (this helps avoid collisions)
        nerdf = os.path.join(self.nrddir, "_"+name+".json")
        write_json(nerdm, nerdf)

        os.rename(nerdf, os.path.join(self.nrddir, name+".json"))

    def _pad_nerdm(self, nerdm):
        if not nerdm.get('contactPoint'):
            nerdm['contactPoint'] = { }
        if not nerdm['contactPoint'].get('@type'):
            nerdm['contactPoint']['@type'] = "vcard:Contact"
        if not nerdm['contactPoint'].get('fn'):
            nerdm['contactPoint']['fn'] = ""
        if not nerdm['contactPoint'].get('hasEmail'):
            nerdm['contactPoint']['hasEmail'] = ""
        if not nerdm.get('keyword'):
            nerdm['keyword'] = []

    def get_pod(self, ediid):
        """
        return the last committed POD record for the dataset with the given identifier.  

        :param str ediid:  the EDI identifier for the desired record
        """
        worker = self._bagging_workers.get(ediid)
        if not worker:
            try:
                bagger = self._create_bagger(ediid)
                if not os.path.isdir(bagger.bagdir):
                    raise IDNotFound(ediid)
            except SIPDirectoryNotFound as ex:
                raise IDNotFound(ediid, cause=ex)
        else:
            bagger = worker.bagger

        bag = NISTBag(bagger.bagdir)
        if worker and not os.path.exists(bag.pod_file()):
            if worker._thread:
                worker._thread.join(0.5)
        return bag.pod_record()
        

    def start_customization_for(self, pod):
        """
        start a customization session of the given POD data.  This transfers update control to 
        the PDR customization service until end_customization_for() is called.  
        """
        # find the bag;  if not found, create one and process the pod into it
        id = pod.get('identifier')
        if not id:
            raise ValueError("POD is missing required property, identifier")

        if self.cfg.get('require_valid_pod', True):
            self._validate_pod(pod)

        self._apply_pod_async(pod, True)
        worker = self._bagging_workers.get(id)
        if worker:
            # lock the bag from further updates via update_ds_with_pod()
            self._lock_out_pod_updates(worker.bagger)
            
            # wait for the update to complete
            if worker.is_working():
                try: 
                    worker._thread.join(10.0)
                except RuntimeError as ex:
                    self.log.error("Trouble waiting for POD update operation: "+str(ex))
                if worker.is_working():
                    self.log.warning("Waiting for POD update timed out (after 10s); "
                                     "Record may not be up to date!")

        nerdf = os.path.join(self.nrddir, midasid_to_bagname(id)+".json")
        if not os.path.isfile(nerdf):
            raise StateException("Missing NERDm file in cache: "+os.path.basename(nerdf))
        nerdm = read_nerd(nerdf)

        # nerdm record may be underspecified
        self._pad_nerdm(nerdm)

        # put nerdm to customization to start session (will raise exception on failure)
        self._custclient.create_draft(nerdm)

    def end_customization_for(self, ediid):
        """
        end the customization session of the given POD data.  This transfers update control back
        to MIDAS.
        """
        # pull nerdm draft from customization service
        updmd = self._custclient.get_draft(midasid_to_bagname(ediid), True)

        worker = self._bagging_workers.get(ediid)
        if worker:
            bagger = worker.bagger
        else:
            bagger = self._create_bagger(ediid)
            bagger.prepare()

        if updmd.get('_editStatus') == "done":
            # if the user didn't press "Done", don't save this

            #   filter out changes that are not allowed
            updates = self._filter_and_check_cust_updates(updmd, bagger.bagbldr)

            #   combine changes with current nerdm
            forannots = ["authors"]
            msg = "User-generated metadata updates to path='{0}': {1}"
            for destpath in updates:
                if destpath == '':
                    # POD-native metadata goes into main metadata
                    upd = OrderedDict([(k,v) for (k,v) in updates[''].items() if k not in forannots])
                    bagger.bagbldr.update_metadata_for(destpath, upd,
                                          message=msg.format(destpath, str(upd.keys())))
                    # non-POD metadata goes into annotations
                    upd = OrderedDict([(k,v) for (k,v) in updates[''].items() if k in forannots])
                    bagger.bagbldr.update_annotations_for(destpath, upd,
                                          message=msg.format(destpath, str(upd.keys())))
                elif destpath is not None:
                    bagger.bagbldr.update_annotations_for(destpath, upd,
                                          message=msg.format(destpath, str(upd.keys())))
            nerdm = updates[None]
            self.serve_nerdm(nerdm)

            #   convert to pod
            pod = self._nerd2pod.convert_data(nerdm)

            #   save pod -- SHOULD WE MAKE MIDAS apply_pod()?
            bagger.bagbldr.save_pod(pod)

        # send delete request
        self._custclient.delete_draft(ediid)
        self._lock_out_pod_updates(bagger, False)

    def _lock_out_pod_updates(self, bagger, lock=True):
        pass

    def _filter_and_check_cust_updates(self, data, bldr):
        # filter out properties that are not updatable; check the values of
        # the remaining.  The returned value is a dictionary mapping filepath
        # values to the associated metadata for that component; the empty string
        # key maps to the resource-level metadata (which can include none-filepath
        # components.

        custcfg = self.cfg.get('customization_service', {})
        updatable = custcfg.get('updatable_properties',[])
        mergeconv = custcfg.get('merge_convention', DEF_MERGE_CONV)

        def _filter_props(fromdata, todata, parent=''):
            # fromdata and todata are either Mapping objects or lists
            if isinstance(fromdata, list):
                # parent should end with '[]'
                for el in fromdata:
                    if parent in updatable:
                        todata.append(el)
                        continue
                    elif isinstance(el, list):
                        if not any([e.startswith(parent+'[]') for e in updatable]):
                            continue
                        subdata = []
                        _filter_props(el, subdata, parent+'[]')
                        if subdata:
                            todata.append(subdata)
                    elif isinstance(el, Mapping):
                        subdata = OrderedDict()
                        _filter_props(el, subdata, parent)
                        if subdata:
                            todata.append(subdata)
                        
            elif isinstance(fromdata, Mapping):
                pkey = parent;
                for key in fromdata:
                    pkey = parent;
                    if pkey:  pkey += "."
                    pkey += key

                    if pkey in updatable:
                        todata[key] = fromdata[key]

                    elif isinstance(fromdata[key], list):
                        if not any([e.startswith(pkey+'[]') for e in updatable]):
                            continue
                        subdata = []
                        _filter_props(fromdata[key], subdata, pkey+'[]')
                        if subdata:
                            todata[key] = subdata

                    elif isinstance(fromdata[key], Mapping):
                        if not any([e.startswith(pkey+'.') for e in updatable]):
                            continue
                        subdata = OrderedDict()
                        _filter_props(fromdata[key], subdata, pkey)
                        if subdata:
                            todata[key] = subdata

                if pkey!='' and '@id' in fromdata and todata and '@id' not in todata:
                    todata['@id'] = fromdata['@id']

        fltrd = OrderedDict()
        _filter_props(data, fltrd)    # filter out properties you can't edit

        # if authors was updated, filter out unrecognized sub-properties
        if 'authors' in fltrd:
            if not isinstance(fltrd['authors'], list):
                del fltrd['authors']
            else:
                self._filter_author_subprops(fltrd['authors'])

        # if topic was updated, migrate these to theme
        if ('topic' in fltrd) != ('theme' in fltrd):
            if 'topic' in fltrd:
                fltrd['theme'] = topics2themes(fltrd['topic'], False)
            elif self._schemadir and 'theme' in fltrd:
                taxon = ResearchTopicsTaxonomy.from_schema_dir(self._schemadir)
                fltrd['topic'] = taxon.themes2topics(fltrd['theme'])
        
        oldnerdm = bldr.bag.nerdm_record(mergeconv)
        newnerdm = self._validate_update(fltrd, oldnerdm, bldr, mergeconv)  # may raise InvalidRequest

        # separate file-based components from main metadata; return parts
        # by destination path.  Every component is now guaranteed to have an
        # '@id' property
        out = OrderedDict()
        if 'components' in fltrd:
            for i in range(len(fltrd['components'])-1, -1, -1):
                cmp = fltrd['components'][i]
                oldcmp = self._item_with_id(oldnerdm['components'], cmp['@id'])
                if 'filepath' in oldcmp:
                    del cmp['@id']  # don't update the ID
                    out[oldcmp['filepath']] = cmp
                    del fltrd['components'][i]
            if len(fltrd['components']) <= 0:
                del fltrd['components']
        out[''] = fltrd
        out[None] = newnerdm
        return out

    def _filter_author_subprops(self, authors):
        def _filter_subprops(obj, subprops):
            for subprop in obj:
                if subprop not in subprops:
                    del obj[subprop]
                    
        authprops = "fn familyName givenName middleName orcid affiliation proxyFor".split()
        afflprops = "title proxyFor location label description subunits".split()
        for i in reversed(range(len(authors))):
            if not isinstance(authors[i], Mapping):
                del authors[i]
                continue

            _filter_subprops(authors[i], authprops)
            authors[i]['@type'] = "foaf:Person"
            if 'affiliation' in authors[i]:
                if not isinstance(authors[i]['affiliation'], list):
                    del authors[i]['affiliation']
                else:
                    for j in reversed(range(len(authors[i]['affiliation']))):
                        if not isinstance(authors[i]['affiliation'][j], Mapping):
                            del authors[i]['affiliation'][j]
                            continue
                        _filter_subprops(authors[i]['affiliation'][j], afflprops)
                        authors[i]['affiliation'][j]['@type'] = "org:Organization"
                        affid = self._affil_id_for(authors[i]['affiliation'][j].get('title'))
                        if affid:
                            authors[i]['affiliation'][j]['@id'] = affid
                        if 'subunits' in authors[i]['affiliation'][j] and \
                           not authors[i]['affiliation'][j]['subunits']:
                            del authors[i]['affiliation'][j]['subunits']

    def _affil_id_for(self, afftitle):
        if not afftitle:
            return None
        if "NIST" in afftitle or "National Institute of Standards and Technology" in afftitle:
            return "ror:05xpvk416"

    def _item_with_id(self, array, id):
        out = [e for e in array if e['@id'] == id]
        return (len(out) > 0 and out[0]) or None

    def _validate_update(self, updata, nerdm, bagbldr, mergeconv):
        # make sure the update produces valid NERDm.  This is done primarily by
        # merging the update with the current metadata and validating the results.
        # Other checks may be encapsulated in this function.  If any of the checks
        # fail, this function will raise a InvalidRequest exception

        if 'components' in updata and 'components' not in nerdm:
            del updata['components']
        if 'components' in updata:
            cmps = updata['components']

            # make sure the component updates correspond to components already
            # defined (as specified by the component's identifier); eliminate
            # those that do not.  
            for i in range(len(cmps)-1, -1, -1):
                if '@id' not in cmps[i] or \
                   not self._item_with_id(nerdm['components'], cmps[i]['@id']):
                    del cmps[i]
            if len(cmps) == 0:
                del updata['components']

        # mergeconv = bagbldr.cfg.get('merge_convention', DEF_MERGE_CONV)
        merger = bagbldr.bag._make_merger(mergeconv, "Resource")

        # nerdm = bagbldr.bag.nerdm_record(mergeconv)
        updated = merger.merge(nerdm, updata)
        for prop in [p for p in updata.keys() if p.startswith('_')]:
            updated[prop] = updata[prop]

        # we will validate a version of the nerdm with minimal defaults added in
        checked = deepcopy(updated)
        if not checked.get('contactPoint'):
            checked['contactPoint'] = OrderedDict([("@type", "vcard:Contact")])
        checked['contactPoint'].setdefault('fn',"_")
        checked['contactPoint'].setdefault('hasEmail',"mailto:a@b.c")
        if not checked.get('keyword'):
            checked['keyword'] = []
        if len(checked['keyword']) == 0 or checked['keyword'] == [""]:
            checked['keyword'] = ['k']
        if not checked.get('modified'):
            checked['modified'] = '0000-01-01'

        errs = self._validate_nerdm(checked, bagbldr.cfg.get('validator', {}))
        if len(errs) > 0:
            self.log.error("User update will make record invalid " +
                           "(see INFO details below)")
            self.log.info("metadata patch:\n" +
                           json.dumps(updata,indent=2))
            self.log.info("problems:\n " + "\n ".join(errs))
            raise InvalidRequest("Update makes record invalid", errs)

        return updated

    def _validate_nerdm(self, nerdm, valcfg):
        if not self._schemadir:
            self._schemadir = valcfg.get('nerdm_schema_dir', pdr.def_schema_dir)
            if not self._schemadir:
                raise ConfigurationException("Need to set "+
                                            "bag_builder.validator.nerdm_schema_dir")
            if not os.path.isdir(self._schemadir):
                raise ConfigurationException("nerdm_schema_dir directory does not "+
                                             "exist as a directory: " +
                                             self._schemadir)

        return [str(e) for e in validate.validate(nerdm, self._schemadir)]
        
    def get_customized_pod(self, ediid):
        """
        return the POD data as edited from the customization service.
        """
        # pull nerdm draft from customization service
        updmd = self._custclient.get_draft(midasid_to_bagname(ediid), True)

        # filter out changes that are not allowed
        worker = self._bagging_workers.get(ediid)
        if worker:
            bagger = worker.bagger
        else:
            try:
                bagger = self._create_bagger(ediid)
                bagger.prepare()
            except (IDNotFound, SIPDirectoryNotFound) as ex:
                msg = "A draft exists for dataset not being edited: " + ediid + ": " + str(ex)
                log.error(msg)
                raise StateException(msg=msg, cause=ex, sys=self)

        updates = self._filter_and_check_cust_updates(updmd, bagger.bagbldr)

        #   convert to pod
        pod = self._nerd2pod.convert_data(updates[None])
        for prop in [p for p in updates[''] if p.startswith('_')]:
            pod[prop] = updates[''][prop]
        return pod

    def preserve_new(self, ediid, async=None):
        """
        request that the SIP given by ediid be preserved for the first time.  

        This is done by marking the last POD submitted via update_ds_from_pod() as the final 
        one for publishing so that it can be queued for preservation.  The bag worker will see 
        the mark and take responsibility for starting the preservation process.

        :param str ediid:   the EDI ID for the dataset to be preserved.
        :param bool async:  if True (default), process any pending PODs asynchronously.  Note that this 
                            only affects POD processing, not the actual preservation.
        :rtype dict:  a status JSON object giving the status of the preservation.  
        :raise PreservationStateError:  if the SIP has been published before under the requested ID
                            and preserve_update() should have been used.  
        """
        self.log.info("Queuing (first-time) preservation of SIP=%s", ediid)
        if async is None:
            async = not bg_sync
        stat = self.pressvc.status(ediid, "midas3")
        if stat['state'] in [ ps.NOT_FOUND, ps.PENDING, ps.IN_PROGRESS ]:
            # can't comply with request; just return stat, which tells the story
            return stat

        worker = self._get_bagging_worker(ediid)
        prepr = worker.bagger.get_prepper()
        if stat['state'] == ps.SUCCESSFUL or (prepr and prepr.aip_exists()):
            raise PreservationStateError("AIP with ID already exists (need to request update?): " +
                                         ediid)
            
        halted = worker.get_halt_reason()
        if halted is not None:
            raise PreservationStateError("Publishing service processing is (unexpectedly) halted; reason: "
                                         + halted)
        worker.mark_for_preservation()

        if not worker.is_working():
            if async:
                timeout = self.cfg.get('preservation_service',{}).get('sync_timeout', 2)
                worker.launch()
                if worker.is_working:
                    # wait around for a little while to see if finishes quickly
                    # (this is a bit of hack and not optimal)
                    worker._thread.join(timeout/2.0)
                    if not worker.is_working():
                        # this is for the preservation service
                        time.sleep(timeout/2.0)
            else:
                worker.run("sync")

        return self.pressvc.status(ediid, "midas3")

    def preserve_update(self, ediid, async=None):
        """
        request that the update to the SIP given by ediid be preserved.  

        This is done by marking the last POD submitted via update_ds_from_pod() as the final 
        one for publishing so that it can be queued for preservation.  The bag worker will see 
        the mark and take responsibility for starting the preservation process.

        :param str ediid:   the EDI ID for the dataset to be preserved.
        :param bool async:  if True (default), process any pending PODs asynchronously.  Note that this 
                            only affects POD processing, not the actual preservation.
        :rtype dict:  a status JSON object giving the status of the preservation.  
        :raise PreservationStateError:  if the SIP has not been published before under the requested ID
                            and preserve_new() should have been used.  
        """
        self.log.info("Queuing (update) preservation of SIP=%s", ediid)
        if async is None:
            async = not bg_sync
        stat = self.pressvc.status(ediid, "midas3")
        if stat['state'] in [ ps.NOT_FOUND, ps.PENDING, ps.IN_PROGRESS ]:
            # can't comply with request; just return stat, which tells the story
            return stat

        worker = self._get_bagging_worker(ediid)
        prepr = worker.bagger.get_prepper()
        if prepr and not prepr.aip_exists():
            raise PreservationStateError("AIP with ID does not exist (not updateable?): " +
                                         ediid)

        # worker may still be finishing up with preservation
        timeout = self.cfg.get('preservation_service',{}).get('sync_timeout', 2)
        halted = worker.get_halt_reason()
        if halted is not None:
            if worker.is_working():
                self.log.debug("Waiting for worker to finish launch of preservation for %s", worker.id)
                worker._thread.join(timeout/2.0)
                halted = worker.get_halt_reason()
        if halted is not None:
            if worker.is_working():
                msg = "Previous preservation request still being processed; please wait"
            else:
                msg = "Publishing service processing is (unexpectedly) halted; reason: " + halted
            raise PreservationStateError(msg)
        
        worker.mark_for_preservation(True)

        if not worker.is_working():
            if async:
                worker.launch()
                if worker.is_working():
                    # wait around for a little while to see if finishes quickly
                    # (this is a bit of hack and not optimal)
                    worker._thread.join(timeout/2.0)
                    if not worker.is_working():
                        # this is for the preservation service
                        time.sleep(timeout/2.0)
            else:
                worker.run("sync")

        return self.pressvc.status(ediid, "midas3")

    def preservation_status(self, ediid):
        """
        return the status of the last preservation request of the specified dataset

        :param str ediid:   the EDI ID for the dataset of interest
        """
        # If this dataset has been idle since last preservation, clean it up
        worker = self._get_bagging_worker(ediid)
        return worker.preservation_status()

    def preservation_requests(self):
        """
        return a list of identifiers for datasets for which there have been 
        (unforgotten) requests for preservation.
        """
        return self.pressvc.requests()


    class BaggingWorker(object):

        def __init__(self, service, id, bagger, svclog):
            self.id = id
            self.bagger = bagger
            self.service = service
            self.name = midasid_to_bagname(id)
            self._thread = None
            
            lgnm = self.name
            if len(lgnm) > 11:
                lgnm = lgnm[0:4]+"..."+lgnm[-4:]
            self.log = svclog.getChild(lgnm)
            
            self.service._bagging_workers[id] = self

            working_pod_dir = os.path.join(self.service.podqdir, "current")
            next_pod_dir = os.path.join(self.service.podqdir, "next")
            presv_pod_dir = os.path.join(self.service.podqdir, "preserve")
            halt_dir = os.path.join(self.service.podqdir, "halt")

            for dir in [working_pod_dir, next_pod_dir, presv_pod_dir, halt_dir]:
                if not os.path.exists(dir):
                    os.mkdir(dir)

            self.working_pod = os.path.join(working_pod_dir, self.name+".json")
            self.next_pod    = os.path.join(next_pod_dir, self.name+".json")
            self.presv_pod    = os.path.join(presv_pod_dir, self.name+".json")
            self.halt_sema   = os.path.join(halt_dir, self.name+".txt")
            self.qlock = None

        class _Thread(threading.Thread):
            def __init__(self, worker):
                self.worker = worker
                super(MIDAS3PublishingService.BaggingWorker._Thread, self). \
                    __init__(name="bagger:"+worker.bagger.name)
            def run(self):
                self.worker.run()
        
        def is_working(self):
            return self._thread and self._thread.is_alive()

        def launch(self):
            self._thread = self._Thread(self)
            self.log.debug("Starting worker thread %s", self._thread.name)
            self._thread.start()

        def queue_POD(self, pod):
            self.ensure_qlock()
            with self.qlock:
                write_json(pod, self.next_pod)

        def mark_for_preservation(self, asupdate=False):
#            self.service.pressvc._make_handler(self.id, "midas3")._status.reset(
#                                            "completing metadata updates before preservation")
            self.ensure_qlock()
            with self.qlock:
                if os.path.exists(self.next_pod):
                    # read and mark the last one in the POD queue
                    pod = read_pod(self.next_pod)

                elif os.path.exists(self.working_pod):
                    # read first one in the queue, mark it, and resubmit it to the queue
                    pod = read_pod(self.working_pod)

                else:
                    # read the pod from the metadata bag, mark it and resubmit it to queue
                    if not os.path.exists(self.bagger.bagbldr._bag.pod_file()):
                        raise StateException("POD has yet to be submitted for ID="+self.name)
                    pod = self.bagger.bagbldr._bag.pod_record()
                    
                pod['_preserve'] = (asupdate and "update") or "new"
                write_json(pod, self.presv_pod)
                if os.path.exists(self.next_pod):
                    os.remove(self.next_pod)

        def ensure_qlock(self):
            if not self.qlock:
                self.qlock = threading.RLock()

        def _whendone(self):
            self.service.serve_nerdm(self.bagger.bagbldr.bag.nerdm_record(True))

            # clean up the worker
            self.service._drop_bagging_worker(self)
                
        def run(self, examine="async"):
            whendone = None
            if examine == "async":
                whendone = self._whendone
            self.process_queue()

            # remove this thread from bagger threads
            # del self.service._bagging_workers[self.id]

        def process_queue(self):
            self.ensure_qlock()
            pod = None
            i = 0
            while os.path.exists(self.working_pod) or os.path.exists(self.next_pod) or \
                  os.path.exists(self.presv_pod):
                if not os.path.exists(self.halt_sema):
                    with self.qlock:
                        if i > 0:
                            self.log.info("Processing next POD submission for id="+self.id)
                        else:
                            self.log.info("Processing POD submission for id="+self.id)
                        if not os.path.exists(self.working_pod):
                            if os.path.exists(self.presv_pod):
                                os.rename(self.presv_pod, self.working_pod)
                            elif os.path.exists(self.next_pod):
                                os.rename(self.next_pod, self.working_pod)

                if os.path.exists(self.working_pod):
                    try:
                        pod = None
                        with self.qlock:
                            pod = read_pod(self.working_pod)
                        self.bagger.apply_pod(pod, False)
                        self.service.serve_nerdm(self.bagger.bagbldr.bag.nerdm_record(True))

                        if pod.get('_preserve'):
                            # turn off pod queue processing
                            self.log.info("Pausing processing of POD updates for preservation")
                            self.halt_pod_processing("preserve")
                            self.log.debug("enhancing file metadata...")
                            self.bagger.enhance_metadata(examine="sync")
                            self.log.debug("preparing preservation process...")
                            self.launch_preservation(pod['_preserve'] == "update")

                    except PreservationException as ex:
                        self.log.error(str(ex))
                        raise
                    except Exception as ex:
                        self.log.exception("failure while processing POD update: "+str(ex))
                    finally:
                        if pod.get('_preserve'):
                            self.log.debug("resuming POD processing...")
                            self.resume_pod_processing()
                            self.log.info("POD update processing resumed")
                        with self.qlock:
                            try:
                                os.remove(self.working_pod)
                            except Exception as ex:
                                self.log.warn("Trouble removing current consumed POD: %s", str(ex))

                if os.path.exists(self.halt_sema):
                    break

                # let other threads have a chance
                time.sleep(0.1)
                i += 1

            if pod and not pod.get('_preserve'):
                # the last POD we processed did not have the preserve flag; if it did,
                # then metadata enhancement would have already been done.
                self.bagger.enhance_metadata(examine="sync")

        def halt_pod_processing(self, reason):
            try:
                with open(self.halt_sema, 'a') as fd:
                    fd.write(reason)
                    fd.write("\n")
            except IOError as ex:
                msg = "Trouble {0} halt semaphore, {1}: {2}"
                if not os.path.exists(self.halt_sema):
                    raise PreservationException(msg.format("setting", self.halt_sema, ex), cause=ex)
                else:
                    self.log.warning(msg.format("updating", self.halt_sema, ex)+": ignoring")

        def get_halt_reason(self):
            if not os.path.exists(self.halt_sema):
                return None
            with open(self.halt_sema) as fd:
                return ", ".join([r for r in fd])

        def resume_pod_processing(self):
            # resume processing pod updates
            if os.path.exists(self.halt_sema):
                try:
                    os.remove(self.halt_sema)
                except Exception as ex:
                    self.log.error("Trouble removing halt file: %s", str(ex))
            else:
                self.log.warn('POD processing apparently already resumed')

        def launch_preservation(self, asupdate=False):
            try: 
                self.bagger.fileExaminer.waitForCompletion(None)

                # determine preservation bagger configuration
                pcfg = self.service.pressvc._get_handler_config("midas3").get('bagger',{})
                pbagparent = pcfg.get('bagparent_dir', self.service.cfg.get('bagparent_dir', '_preserv'))
                isrel = pcfg.get('relative_to_indir')
                if not os.path.isabs(pbagparent):
                    if isrel:
                        pbagparent = os.path.join(self.bagger.sip.revdatadir, pbagparent)
                    else:
                        pbagparent = os.path.join(pcfg.get('working_dir',self.service.workdir), pbagparent)
                if not os.path.exists(pbagparent):
                    os.makedirs(pbagparent)

                # assign next version to this submission
                nerd = self.finalize_version()
                nerd['_preserve'] = True
                self.service.serve_nerdm(nerd)

                # copy the metadata bag to the preservation queue
                if self.bagger.prepsvc:
                    self.log.debug("Will pull multibag info from previous published bag")
                    prepper = self.bagger.get_prepper()
                    prepper.set_multibag_info(self.bagger.bagdir)
                pbagger = PreservationBagger.fromMetadataBagger(self.bagger, pbagparent, pcfg)
                pbagger.establish_output_bag()

                # Further updates from MIDAS are possible, so we'll return the version
                # in the metadata to update status
                nerd['version'] += "+ (in edit)"
                self.bagger.bagbldr.update_annotations_for('', {'version': nerd['version']}, 
                                                           None, '')

                if asupdate:
                    stat = self.service.pressvc.update(self.id, "midas3")
                else:
                    stat = self.service.pressvc.preserve(self.id, "midas3")

                # if successful, clean-up
                self._check_preservation(stat, True)
                return stat
            except PreservationException as ex:
                raise
            except Exception as ex:
                self.log.exception("Unexpected error while managing preservation process: %s", str(ex))
                raise PreservationException("Failure while managing preservation process: "+str(ex),
                                            cause=ex)

        def _check_preservation(self, stat, _inprogress=False):
            if os.path.exists(self.bagger.bagdir) and \
               (stat['state'] == ps.SUCCESSFUL or stat['state'] == ps.FORGOTTEN):
                self.ensure_qlock()
                with self.qlock:
                    if not os.path.exists(self.next_pod) and not os.path.exists(self.presv_pod) and \
                       (_inprogress or not os.path.exists(self.working_pod)):
                        # last preserve was successful and nothing's in the queue;
                        # now determine if we have processed other POD updates since
                        # starting the preservation
                        pod = self.bagger.bagbldr.bag.pod_record()
                        if '_preserve' in pod:
                            # it's safe to clean up metadata bag
                            self.bagger.done()
                            shutil.rmtree(self.bagger.bagdir)

        def delete_bag(self):
            """
            throw the working metadata bag away, forcing MIDAS to start over with the current dataset
            """
            if os.path.exists(self.bagger.bagdir):
                self.ensure_qlock()
                with self.qlock:
                    self.bagger.done()
                    self.bagger.sip.nerd = None
                    self.bagger.sip.pod = None
                    shutil.rmtree(self.bagger.bagdir)
                
        def preservation_status(self):
            # signal that preservation of this dataset has completed.
            stat = self.service.pressvc.status(self.bagger.midasid, "midas3")
            self._check_preservation(stat)  # this may clean up the metadata bag
            return stat

        def finalize_version(self):
            self.bagger.done()
            
            # create a metadata bagger that only looks at the review dir;
            # in other words, data files must appear in the review directory to be
            # considered part of this version of the dataset.  
            usebagger = MIDASMetadataBagger(self.bagger.midasid, self.bagger.bagparent,
                                            self.bagger.sip.revdatadir, config=self.bagger.cfg)
            return usebagger.finalize_version()



class CustomizationStateException(StateException):
    """
    an exception indicating an attempt to call a function that is incompatible with the 
    state of the service with respect to customization control.  This would include, for 
    example, attempting to provide an updated POD record when a dataset is under customization 
    control.  
    """

    def __init__(self, id, message):
        """
        create the exception
        :param str id:  the identifier for the dataset that is in the incorrect state 
        :param str message:  an explanation of the incompatibility of the state and the 
                             requested operation
        """
        super(CustomizationStateException, self).__init__(id+": "+message)
        self.id = id

class InvalidRequest(PDRServiceException):
    """
    An invalid request was made of the metadata service.  
    """

    def __init__(self, message, reasons=[]):
        """
        create the exception

        :param str message:  the message summarizing what makes the request invalid
        :param reasons:  a list of the specific reasons why the request is invalid
        :type reasons: array of str
        """
        super(InvalidRequest, self).__init__("Publishing Service", http_code=400,
                                             message=message, sys=PublishSystem)
        self.reasons = reasons

