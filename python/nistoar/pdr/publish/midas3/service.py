"""
The implementation module for the MIDAS-to-PDR publishing service (pubserver), Mark III version.  
It is designed to operate on SIP work areas created and managed by MIDAS for publishing.
"""
import os, logging, re, json, copy, time, threading
from collections import Mapping, OrderedDict
from copy import deepcopy

from .. import PublishSystem
from ...exceptions import (ConfigurationException, StateException,
                           SIPDirectoryNotFound, IDNotFound, PDRServiceException)
from ...preserv.bagger.midas3 import (MIDASMetadataBagger, UpdatePrepService, PreservationBagger,
                                      midasid_to_bagname, DEF_POD_DATASET_SCHEMA)

from ...preserv.bagit import NISTBag, DEF_MERGE_CONV
from ...preserv.bagger.midas3 import MIDASMetadataBagger, midasid_to_bagname, PreservationBagger
from ...utils import build_mime_type_map, read_nerd, write_json, read_pod
from ....id import PDRMinter, NIST_ARK_NAAN
from ....nerdm.convert import Res2PODds, topics2themes
from ....nerdm.taxonomy import ResearchTopicsTaxonomy
from ....nerdm import validate
from .... import pdr
from .customize import CustomizationServiceClient

log = logging.getLogger(PublishSystem().subsystem_abbrev)

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

        self.log = log.getChild("m3pub")

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

        # used to convert NERDm to POD
        self._nerd2pod = Res2PODds(pdr.def_jq_libdir, logger=self.log)

        # used to interact with the customization service
        if 'customization_service' not in self.cfg:
            raise ConfigurationException("Missing required config parameters: "+
                                         'customization_service', sys=self)
        self._custclient = CustomizationServiceClient(self.cfg.get('customization_service'),
                                                   logger=self.log.getChild("customclient"))

        self.schemadir = self.cfg.get('nerdm_schema_dir', pdr.def_schema_dir)
        self._bagging_workers = {}

    def _set_working_dir(self, workdir):
        if not workdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "working_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir

        self.mddir = self.cfg.get('metadata_bags_dir')
        if not self.mddir:
            self.mddir = os.path.join(workdir,"mdbags")
            if not os.path.exists(self.mddir):  os.mkdir(self.mddir)
        self.nrddir = self.cfg.get('nerdm_serve_dir')
        if not self.nrddir:
            self.nrddir = os.path.join(workdir,"nrdserv")
            if not os.path.exists(self.nrddir):  os.mkdir(self.nrddir)
        self.podq = self.cfg.get('pod_queue_dir')
        if not self.podqdir:
            self.podqdir = os.path.join(workdir,"podq")
            if not os.path.exists(self.podqdir):  os.mkdir(self.podqdir)
        self.storedir = self.cfg.get('store_dir')
        if not self.storedir:
            self.storedir = os.path.join(workdir,"store")
            if not os.path.exists(self.storedir):  os.mkdir(self.storedir)


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
        if self.cfg.get('require_valid_pod'):
            self._validate_pod(pod)

        return self._apply_pod_async(pod, async)

    def _validate_pod(self, pod):
        if self.schemadir:
            valid8r = validate.create_validator(self.schemadir, pod)
            valid8r.validate(pod, schemauri=DEF_POD_DATASET_SCHEMA,
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
            bagger.prepare()
            worker = self.BaggingWorker(self, id, bagger, self.log)
            self._bagging_workers[id] = worker
        return worker

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
            nerdf = nerdm
            nerdm = None

        if not name:
            if not nerdm:
                nerdm = read_nerd(nerdf)
            if 'ediid' not in nerdm:
                raise ValueError("serve_nerdm(): NERDm record is missing req. property, ediid")
            name = re.sub(r'^ark:/\d+/', '', nerdm['ediid'])
                        
        if not nerdf:
            # first stage to a temp file (this helps avoid collisions)
            nerdf = os.path.join(self.nrddir, "_"+name+".json")
            write_json(nerdm, nerdf)

        os.rename(nerdf, os.path.join(self.nrddir, name+".json"))

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

        if self.cfg.get('require_valid_pod'):
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
            msg = "User-generated metadata updates to path='{0}': {1}"
            for destpath in updates:
                if destpath is not None:
                    bagger.bagbldr.update_annotations_for(destpath, updates[destpath],
                                 message=msg.format(destpath, str(updates[destpath].keys())))
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

        # if topic was updated, migrate these to theme
        if ('topic' in fltrd) != ('theme' in fltrd):
            if 'topic' in fltrd:
                fltrd['theme'] = topics2themes(fltrd['topic'], False)
            elif self.schemadir and 'theme' in fltrd:
                taxon = ResearchTopicsTaxonomy.from_schema_dir(self.schemadir)
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

            if not os.path.exists(working_pod_dir):
                os.mkdir(working_pod_dir)
            if not os.path.exists(next_pod_dir):
                os.mkdir(next_pod_dir)

            self.working_pod = os.path.join(working_pod_dir, self.name+".json")
            self.next_pod = os.path.join(next_pod_dir, self.name+".json")
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
            self._thread.start()

        def queue_POD(self, pod):
            self.ensure_qlock()
            with self.qlock:
                write_json(pod, self.next_pod)

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
            self.bagger.enhance_metadata(examine=examine, whendone=whendone)

            # remove this thread from bagger threads
            # del self.service._bagging_workers[self.id]

        def process_queue(self):
            self.ensure_qlock()
            i = 0
            while os.path.exists(self.working_pod) or os.path.exists(self.next_pod):
                with self.qlock:
                    if i > 0:
                        self.log.info("Processing next POD submission for id="+self.id)
                    else:
                        self.log.info("Processing POD submission for id="+self.id)
                    if not os.path.exists(self.working_pod) and os.path.exists(self.next_pod):
                        os.rename(self.next_pod, self.working_pod)

                if os.path.exists(self.working_pod):
                    try:
                        pod = None
                        with self.qlock:
                            pod = read_pod(self.working_pod)
                        self.bagger.apply_pod(pod, False)
                        self.service.serve_nerdm(self.bagger.bagbldr.bag.nerdm_record(True))
                    except Exception as ex:
                        import pdb; pdb.set_trace()
                        self.log.exception("failure while processing POD update: "+str(ex))
                    finally:
                        with self.qlock:
                            os.remove(self.working_pod)

                # let other threads have a chance
                time.sleep(0.1)
                i += 1


    
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

