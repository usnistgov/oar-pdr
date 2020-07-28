"""
This module provides an abstract interface, SIPHandler, for  turning a 
Submission Information Package (SIP) into an Archive Information Package 
(BagIt bags).  It also includes implementations for different known SIPs.

This module is part of the preservation service module.  A 
PreservationService is capable of launching preservation of many types of 
SIPs, which it does by instantiating an SIPHandler implementation specific
to that SIP type.  An SIPHandler implementation will use an SIPBagger
instance that is also specific to the SIP type to do much of its work.
An SIPBagger class focuses on constructing the preservation bag, while 
the SIPHandler understands what to do with the bag once it's constructed
as well as how to orchestrate the preservation with the context of a 
controlling process (e.g. a web service).  
"""
from __future__ import print_function
import os, sys, re, shutil, logging, errno
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict
from copy import deepcopy

from ..bagit.serialize import DefaultSerializer
from ..bagit.bag import NISTBag
from ..bagit.validate import NISTAIPValidator
from ..bagit.multibag import MultibagSplitter
from ..bagger import utils as bagutils
from ..bagger.base import checksum_of
from ..bagger.midas import PreservationBagger, midasid_to_bagname, _midadid_to_dirname
from ..bagger.midas3 import PreservationBagger as PreservationM3Bagger 
from .. import (ConfigurationException, StateException, PODError, PreservationException, 
                PreservationStateError, SIPDirectoryError)
from .. import sys as _sys
from . import status
from ...ingest.rmm import IngestClient
from ...doimint import DOIMintingClient
from ...utils import write_json

log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)

class SIPHandler(object):
    """
    The abstract interface for processing an Submission Information Package 
    (SIP).  To launch the preservation of an SIP, one instantiates an 
    implementation of this handler class that is knowledgable of the type
    of SIP being processed, assigning to it the specific SIP to process. 
    Then, the bagit() function is called to assemble and write the serialized 
    bag to a particular destination directory.  (See the module documentation
    for a summary of its place within the preservation processing model.)

    This class takes a configuration dictionary on construction; the supported
    properties will depend on the specific SIPHandler implementation; however,
    this base class support the following properties:
    :prop working_dir str #req:  a directory where this handler can store its
                                 working data.
    :prop status_manager dict ({'cachedir': ...}): configuration properties for 
                                 for the SIPStatus object used to track the 
                                 status of SIP preservation.  If not set, 
                                 the sub-property 'cachedir' will be set to
                                 a directory call 'preserv_status' just below
                                 the working directory ('working_dir').  
    """
    __metaclass__ = ABCMeta

    def __init__(self, sipid, config, minter=None, serializer=None,
                 notifier=None, asupdate=None):
        """
        Configure the handler to process a specific SIP with a given 
        identifier.  The SIP identifier (together with the type of the 
        handler) implies a location for SIP content.  

        :param sipid   str:  an identifer for the SIP that implies its 
                             location.
        :param config dict:  a configuration dictionary specific to the 
                             intended type of SIPHandler.
        :param minter IDMinter:  the IDMinter to use to minter new AIP IDs, 
                             overriding what might be provided by the 
                             configuration or the default for the type of 
                             SIPHandler
        :param serializer Serializer:  a Serializer instance to use to 
                             serialize bags.  If not provided the
                             DefaultSerializer from the .serialize module
                             will be used.
        :param notifier NotificationService: the service for pushing alerts
                             to real people.
        :param asupdate bool:  Create this handler assuming this preservation 
                             request is an update to an existing AIP.
        """
        self._sipid = sipid
        self.cfg = deepcopy(config)
        self._minter = minter
        if not serializer:
            serializer = DefaultSerializer()
        self._ser = serializer
        self._asupdate = asupdate

        self.workdir = self.cfg['working_dir']
        assert self.workdir
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)

        self.storedir = self.cfg['store_dir']
        assert self.storedir
        if not os.path.isdir(self.storedir):
            raise StateException("LT-storage directory does not exist as a "+
                                 "directory: " + self.storedir)

        # set up the Status manager
        stcfg = self.cfg.get('status_manager', {})
        if 'cachedir' not in stcfg:
            stcfg['cachedir'] = os.path.join(self.workdir, "preserv_status")
        if not os.path.exists(stcfg['cachedir']):
            os.mkdir(stcfg['cachedir'])

        # If this is a first time preservation request, the initial state
        # will be FORGOTTEN unless another handler has already started.
        # If this is an update, the state should be SUCCESSFUL.
        self._status = status.SIPStatus(self._sipid, stcfg)

        # set the notification service we can send alerts to
        self.notifier = notifier

    @abstractmethod
    def isready(self, _inprogress=False):
        """
        do a quick check of the input SIP to determine if it can be 
        processed into an AIP.  If it is not ready, return False.

        Implementations should first call this inherited version which ensures 
        that the current status is either FORGOTTEN, PENDING, or READY.  False
        is returned if this is not true, and the child implementation should not 
        proceed.  The child implementation should then do a quick check that the
        input data exists and appears to be in a state ready for preservation.  
        """
        ok = [status.FORGOTTEN, status.PENDING, status.READY, status.NOT_READY]
        if _inprogress:
            ok.append(status.IN_PROGRESS)
        if self._asupdate:
            ok.append(status.SUCCESSFUL)
        return self._status.state in ok

    @abstractmethod
    def bagit(self, serialtype=None, destdir=None, params=None):
        """
        create an AIP in the form of serialized BagIt bags from the 
        identified SIP.  The name of the serialized bag files are 
        controlled by the implementation.

        Errors that prevent successful creation of the bags will raise 
        exceptions.  This implementation ensures that the status property
        is updated to reflect the failure.  

        :param serialtype str:  the type of serialization to apply; this 
                                must be a name recognized by the system.  
                                If not provided a default serialization 
                                will be applied (as given in the configuration).
        :param destdir str:     the path to a directory where the serialized
                                bag(s) will be written.  If not provided the
                                configured directory will be used.  
        :param params dict:     SIP-specific parameters to apply to the 
                                creation of the AIP.  These can over-ride 
                                SIP-default behavior as set by the 
                                configuration.
        :return dict:  a summary of the preservation process, including bag
                       files' checksum hashes.  This is 
        """
        raise NotImplementedError()

    @property
    def sipid(self):
        """
        the identifier for the SIP being handled by this handler
        """
        return self._sipid

    @property
    def status(self):
        """
        a dictionary describing the current status of the SIP's preservation.
        """
        self._status.refresh()
        return self._status.user_export()

    @property
    def state(self):
        """
        the label indicating the current state ofthe SIP's preservation.  This
        is equivalent to self.status['state'].  
        """
        return self._status.state

    def refresh_state(self):
        """
        refresh the status from presistent storage so that the state is up to date
        """
        self._status.refresh()

    def set_state(self, state, message=None, cache=True):
        """
        update the status of the preservation to that of the given label.
        A message intended for the external user can optionally be provided.
        This status will get cached to disk so that it is accessible by other
        processes.
        """
        self._status.update(state, message, cache)

    def _serialize(self, bagdir, destdir, format=None):
        """
        serialize a given bag into a given destination directory.

        :param bagdir   str:   path to the bag's root directory.
        :param destdir str:     the path to a directory where the serialized
                                bag(s) will be written.  If not provided the
                                configured directory will be used.  
        :param format str:  the type of serialization to apply; this 
                                must be a name recognized by the system.  
                                If not provided a default serialization 
                                will be applied (as given in the configuration).
        """
        srcbags = [ bagdir ]

        # split the bag if it exceed size limits
        mbcfg = self.cfg.get('multibag', {})
        maxhbsz = mbcfg.get('max_headbag_size', mbcfg.get('max_bag_size'))
        if maxhbsz:
            log.info("Considering multibagging (max size: %d)", maxhbsz)
            mbspltr = MultibagSplitter(bagdir, mbcfg)

            # check the size of the source bag and split it if it exceeds
            # limits.  
            srcbags = mbspltr.check_and_split(os.path.dirname(bagdir), log)

            # TODO: Run NIST validator on output files
        elif not mbcfg:
            log.warning("multibag splitting not configured")
            

        self._status.data['user']['bagfiles'] = []
        outfiles = []
        for bagd in srcbags:
            bagfile = self._ser.serialize(bagd, destdir, format)
            outfiles.append(bagfile)

            csumfile = bagfile + ".sha256"
            csum = checksum_of(bagfile)
            with open(csumfile, 'w') as fd:
                fd.write(csum)
                fd.write('\n')
            outfiles.append(csumfile)

            # write the checksum to our status object
            self._status.data['user']['bagfiles'].append({
                'name': os.path.basename(bagfile),
                'sha256': csum
            })

        self._status.cache()

        # remove the source bags
        if self.cfg.get("cleanup_unserialized_bags", True):
            for bagd in srcbags:
                try:
                    shutil.rmtree(bagd)
                except Exception as ex:
                    log.warn("Trouble removing unserialized bag: "+bagd)
        
        return outfiles

    def _is_ingested(self):
        """
        return True if some version of this SIP has been ingested into the PDR already.
        """
        #FUTURE: this should query a PDR service to determine if the it exists
        raise NotImplemented()

    @abstractmethod
    def _is_preserved(self):
        """
        return True if some version of this SIP has been preserved (i.e. sent successfully through
        the Preservation Service).  This look for as definitive evidence of success (i.e. existence
        in long-term storage) as possible.
        """
        raise NotImplemented()
    
class MIDASSIPHandler(SIPHandler):
    """
    The interface for processing an Submission Information Package 
    (SIP) from the MIDAS system.

    This handler defines its SIP to be a (1) data directory containing (a)
    user-uploaded data files and (b) a POD file (called _pod.json), and (2)
    (optionally) a metadata bag created on-the-fly from the POD file when
    the user requests the landing page.  If the metadata bag does not exist
    when this handler starts its work, it will be created automatically (via
    MIDASMetadataBagger).

    This handler takes a configuration dictionary on construction. The 
    following properties are supported:

    :prop bagparent_dir str #req:  a directory to write output bag to (before
                                 serialization).
    :prop working_dir str None:  a directory where this handler can store its
                                 working data.
    :prop status_manager dict ({'cachedir': ...}): configuration properties for 
                                 for the SIPStatus object used to track the 
                                 status of SIP preservation.  If not set, 
                                 the sub-property 'cachedir' will be set to
                                 a directory call 'preserv_status' just below
                                 the working directory ('working_dir').  
    :prop bagger dict ({}):  the configuration dictionary for the MIDAS 
                                 PreservationBagger instance used to create the
                                 output bag.  
    :prop review_dir str #req:  an existing directory containing MIDAS SIPs
    
    """
    name = "MIDAS-SIP"
    key = "midas"

    def __init__(self, sipid, config, minter=None, serializer=None,
                 notifier=None, asupdate=None, sipdirname=None):
        """
        Configure the handler to process a specific SIP with a given 
        identifier.  The SIP identifier (together with the type of the 
        handler) implies a location for SIP content.  

        :param sipid   str:  an identifer for the SIP that implies its 
                             location.
        :param config dict:  a configuration dictionary specific to the 
                             intended type of SIPHandler.
        :param minter IDMinter:  the IDMinter to use to minter new AIP IDs, 
                             overriding what might be provided by the 
                             configuration or the default for the type of 
                             SIPHandler
        :param serializer Serializer:  a Serializer instance to use to 
                             serialize bags.  If not provided the
                             DefaultSerializer from the .serialize module
                             will be used.
        :param notifier NotificationService: the service for pushing alerts
                             to real people.
        :param asupdate bool:  Create this handler assuming this preservation 
                             request is an update to an existing AIP.
        :param sipdirname str: a relative directory name to look for that 
                               represents the SIP's directory.  If not provided,
                               the directory is determined based on the provided
                               MIDAS ID.  
        """
        super(MIDASSIPHandler, self).__init__(sipid, config, minter, serializer,
                                              notifier, asupdate)

        workdir = self.cfg.get('working_dir')
        if workdir and not os.path.exists(workdir):
            os.mkdir(workdir)

        self.cleanparent = False
        isrel = self.cfg.get('bagger',{}).get('relative_to_indir')
        bagparent = self.cfg.get('bagparent_dir')
        if not bagparent:
            self.cleanparent = True  # we will feel free to delete stuff from
                                     #   the bagparent
            bagparent = "_preserv"
            if not isrel:
                bagparent = sipid + bagparent
        if not os.path.isabs(bagparent):
            if not isrel:
                if not workdir:
                    raise ConfigurationException("Missing needed config "+
                                                 "property: workdir_dir")
                bagparent = os.path.join(workdir, bagparent)

        self.stagedir = self.cfg.get('staging_dir')
        if not self.stagedir:
            self.stagedir = "stage"
        if not os.path.isabs(self.stagedir):
            if not workdir:
              raise ConfigurationException("Missing needed config property: "+
                                           "working_dir")
            self.stagedir = os.path.join(workdir, self.stagedir)
        if not os.path.exists(self.stagedir):
            os.mkdir(self.stagedir)
        
        self.sipparent = self.cfg.get('review_dir')
        if not self.sipparent:
            raise ConfigurationException("Missing required config property: "+
                                         "review_dir")
        if not os.path.exists(self.sipparent):
            raise ConfigurationException("'review_dir' does not exist: "+
                                         self.sipparent)

        self.mdbagdir = self.cfg.get('metadata_bags_dir')
        if not self.mdbagdir:
            self.mdbagdir = "mdserv"
        if not os.path.isabs(self.mdbagdir):
            if not workdir:
              raise ConfigurationException("Missing needed config property: "+
                                           "working_dir")
            self.mdbagdir = os.path.join(workdir, self.mdbagdir)
            if not os.path.exists(self.mdbagdir):
                os.mkdir(self.mdbagdir)
        if not os.path.exists(self.mdbagdir):
            raise StateException("Metadata directory does not exist as a " +
                                 "directory: " + self.mdbagdir)

        bgrcfg = config.get('bagger', {})
        if 'store_dir' not in bgrcfg and 'store_dir' in config:
            bgrcfg['store_dir'] = config['store_dir']
        if 'repo_access' not in bgrcfg and 'repo_access' in config:
            bgrcfg['repo_access'] = config['repo_access']
            if 'store_dir' not in bgrcfg['repo_access'] and 'store_dir' in bgrcfg:
                bgrcfg['repo_access']['store_dir'] = bgrcfg['store_dir']
            
        self.bagger = PreservationBagger(sipid, bagparent, self.sipparent,
                                         self.mdbagdir, bgrcfg, self._minter, 
                                         self._asupdate, sipdirname)

        if self.state == status.FORGOTTEN and self._is_preserved():
            log.debug("Detected successful preservation that was forgotten, SIP=%s", self._sipid)
            self.set_state(status.SUCCESSFUL, 
                      "SIP with forgotten state is apparently already preserved")

        self._ingester = None
        ingcfg = self.cfg.get('ingester')
        if ingcfg:
            self._ingester = IngestClient(ingcfg, log.getChild("ingester"))

    def isready(self, _inprogress=False):
        """
        do a quick check of the input SIP to determine if it can be 
        processed into an AIP.  If it is not ready, return False.

        :return bool:  True if the requested SIP appears to be ready for 
                       preservation; False, otherwise.
        """
        if not super(MIDASSIPHandler, self).isready(_inprogress):
            return False

        if self.state != status.READY:
            # check for the existence of the input data
            if not os.path.exists(self.bagger.indir):
                self.set_state(status.NOT_FOUND, cache=False)
                return False

            # make sure the input SIP includes a POD file
            try:
                self.bagger.find_pod_file()
            except PODError, e:
                self.set_state(status.NOT_READY, "missing POD record", False)
                return False

            if self.state == status.FORGOTTEN or self.state == status.NOT_READY:
                self.set_state(status.READY,
                               cache=(self.state == status.NOT_READY))
            
        return True
                
        
    def bagit(self, serialtype=None, destdir=None, params=None):
        """
        create an AIP in the form of serialized BagIt bags from the 
        identified SIP.  The name of the serialized bag files are 
        controlled by the implementation.

        :param serialtype str:  the type of serialization to apply; this 
                                must be a name recognized by the system.  
                                If not provided a default serialization 
                                will be applied (as given in the configuration).
        :param destdir str:     the path to a directory where the serialized
                                bag(s) will be written.  If not provided the
                                configured directory will be used.  
        :param params dict:     SIP-specific parameters to apply to the 
                                creation of the AIP.  These can over-ride 
                                SIP-default behavior as set by the 
                                configuration.
        """
        self._status.start()
        if not serialtype:
            serialtype = 'zip'
        if not destdir:
            destdir = self.storedir

        if not self.isready(_inprogress=True):
            raise StateException("{0}: SIP is not ready: {1}".
                                 format(self._sipid, self._status.message),
                                 sys=_sys)

        # If a previous attempt to preserve went wrong, it's possible it's
        # remnants remain on disk.  If so, we should clean out the directory
        # before trying again.
        if self.cleanparent and os.path.isdir(self.bagger.bagparent):
            log.warning("Cleaning out previous bagging artifacts (%s)",
                        self.bagger.bagparent)
            shutil.rmtree(self.bagger.bagparent)

        # Create the bag.  Note: make_bag() can raise exceptions
        self._status.record_progress("Collecting metadata and files")
        try:
            bagdir = self.bagger.make_bag()
        finally:
            if hasattr(self.bagger, 'bagbldr') and self.bagger.bagbldr:
                self.bagger.bagbldr._unset_logfile() # disengage the internal log

        # Stage the full NERDm record for ingest into the RMM
        bag = NISTBag(self.bagger.bagdir)
        nerdm = bag.nerdm_record()
        if self._ingester:
            try:
                self._ingester.stage(nerdm, self.bagger.name)
            except Exception as ex:
                msg = "Failure staging NERDm record for " + self.bagger.name + \
                      " for ingest: " + str(ex)
                log.exception(msg)
                # send an alert email to interested subscribers
                if self.notifier:
                    self.notifier.alert("preserve.failure", origin=self.name,
                                  summary="Ingest failed for "+self.bagger.name,
                                        desc=msg, id=self.bagger.name,
                                        version=nerdm.get('version', 'unknown'))

        # zip it up; this may split the bag into multibags
        self._status.record_progress("Serializing")
        savefiles = self._serialize(bagdir, self.stagedir, serialtype)

        # copy the zipped files to long-term storage ("public" directory)
        self._status.record_progress("Delivering preservation artifacts")
        log.debug("writing files to %s", destdir)
        errors = []
        saved = []
        try:
            for f in savefiles:
                destfile = os.path.join(destdir, os.path.basename(f))
                if os.path.exists(destfile) and \
                   not self.cfg.get('allow_bag_overwrite', False):
                    raise OSError(errno.EEXIST, os.strerror(errno.EEXIST),
                                  destfile)
                shutil.copy(f, destdir)
                saved.append(f)
        except OSError, ex:
            log.error("Failed to copy preservation file: %s\n" +
                      "  to long-term storage: %s", f, destdir)
            log.exception("Reason: %s", str(ex))
            log.error("Rolling back successfully copied files")
            msg = "Failed to copy preservation files to long-term storage"
            self.set_state(status.FAILED, msg)

            for f in saved:
                fp = os.path.join(destdir, os.path.basename(f))
                if os.path.exists(fp):
                    log.warn("Removing %s from long-term storage", f)
                    os.remove(fp)

            raise PreservationException(msg, [str(ex)])

        # Now write copies of the checksum files to the review SIP dir.
        # MIDAS will scoop these up and save them in its database.
        # The file with sequence number 0 must be written last; this is a
        # signal that preservation is complete.
        try:
            sigbase = self._sipid+"_"
            ckspat = re.compile(self._sipid+r'.*-(\d+).\w+.sha256$')
            cksfiles = [f for f in savefiles if ckspat.search(f)]
            cksfiles.sort(key=lambda f: int(ckspat.search(f).group(1)),
                          reverse=True)
            log.debug("copying %s checksum files to %s",
                      str(len(cksfiles)), self.bagger.indir)
            cpfailures = []
            for f in cksfiles:
                try:
                    sigfile = sigbase+ckspat.search(f).group(1)+'.sha256'
                    sigfile = os.path.join(self.bagger.bagparent,sigfile)
                    log.debug("copying checksum file to %s", sigfile)
                    shutil.copyfile(f, sigfile)
                except Exception, ex:
                    msg = "Failed to copy checksum file to review dir:" + \
                          "\n %s to\n %s\nReason: %s" % \
                          (f, sigfile, str(ex))
                    log.exception(msg)
                    cpfailures.append(msg)

            if cpfailures and self.notifier:
                # alert subscribers of these failures with an email
                self.notifier.alert("preserve.failure", origin=self.name,
                                    summary="checksum file copy failure", desc=msg, 
                                    version=nerdm.get('version', 'unknown'))
                                    
                    
        except Exception, ex:
            msg = "%s: Failure while writing checksum file(s) to " + \
                  "review dir: %s" % (self._sipid, str(ex))
            log.exception(msg)
            if self.notifier:
                self.notifier.alert("preserve.failure", origin=self.name,
                                    summary="checksum file write failure",
                                    desc=msg, id=self._sipid,
                                    version=nerdm.get('version', 'unknown'))
                
        # remove the metadata bag directory so that that an attempt to update
        # will force a rebuild based on the published version
        mdbag = os.path.join(self.mdbagdir, self.bagger.name)
        log.debug("ensuring the removal metadata bag directory: %s", mdbag)
        if os.path.isdir(mdbag):
            log.debug("removing metadata bag directory...")
            try:
                shutil.rmtree(mdbag)
            except Exception as ex:
                log.error("Failed to clean up the metadata bag directory: "+
                          mdbag + ": "+str(ex))
            if os.path.isfile(mdbag+".lock"):
                try:
                    os.remove(mdbag+".lock")
                except Exception as ex:
                    log.warn("Failed to clean up the metadata bag lock file: "+
                             mdbag + ".lock: "+str(ex))

        # cache the latest nerdm record under the staging directory
        try:
            mdcache = os.path.join(self.stagedir, '_nerd')
            staged = os.path.join(mdcache, self.bagger.name+".json")
            if os.path.isdir(mdcache):
                write_json(nerdm, staged)
        except Exception as ex:
            log.error("Failed to cache the new NERDm record: "+str(ex))
            if os.path.exists(staged):
                # remove the old record as it is now out of date
                os.remove(staged)

        self.set_state(status.SUCCESSFUL)

        # submit NERDm record to ingest service
        if self._ingester and self._ingester.is_staged(self.bagger.name):
            try:
                self._ingester.submit(self.bagger.name)
                log.info("Submitted NERDm record to RMM")
            except Exception as ex:
                msg = "Failed to ingest record with name=" + \
                      self.bagger.name + " into RMM: " + str(ex)
                log.exception(msg)
                log.info("Ingest service endpoint: "+self._ingester.endpoint)

                if self.notifier:
                    self.notifier.alert("ingest.failure", origin=self.name,
                          summary="NERDm ingest failure: " + self.bagger.name,
                                        desc=msg, id=self.bagger.name,
                                        version=nerdm.get('version', 'unknown'))

        # tell a human that things are great!
        if self.notifier:
            self.notifier.alert("preserve.success", origin=self.name,
                           summary="New MIDAS SIP preserved: "+self.bagger.name,
                                id=self.bagger.name,
                                version=nerdm.get('version', 'unknown'))

        # clean up staging area
        if self.cfg.get('clean_bag_staging', True):
            headbag = None
            if not self.cfg.get('clean_headbag_staging', False):
                bags = [b for b in [os.path.basename(f) for f in savefiles]
                          if bagutils.is_legal_bag_name(b) and
                             not b.endswith('sha256')]
                if len(bags):
                    headbag = '/' + bagutils.find_latest_head_bag(bags)
            for f in savefiles:
                if f.endswith(headbag):
                    continue
                try:
                    os.remove(f)
                except Exception, ex:
                    log.error("Trouble cleaning up serialized bag in staging "+
                          "dir:\n  %s\nReason: %s", f, str(ex))

        log.info("Completed preservation of SIP %s", self.bagger.name)

    def _is_preserved(self):
        """
        return True if some version of this SIP has been preserved (i.e. sent 
        successfully through the Preservation Service).  This look for as 
        definitive evidence of success (i.e. existence in long-term storage) 
        as possible.
        """
        # look for files in the serialized bag store with names that start
        # with the SIP identifier
        return len([f for f in os.listdir(self.storedir)
                      if f.startswith(self.bagger.name+'.')]) > 0
    
class MIDAS3SIPHandler(SIPHandler):
    """
    The interface for processing an Submission Information Package 
    (SIP) from the MIDAS system (Mark III conventions)

    This handler considers an SIP to be (1) a metadata bag that was created 
    through the user-driven interaction between MIDAS and the PDR's pubserver, 
    and (2) a data directory that contains user-uploaded data.  Unlike with
    the assumptions built into MIDASSIPHandler (the Mark I conventions), it 
    is not possible to preserve a MIDAS submission via this handler without 
    the metadata bag being created first.  Note that this implementation 
    assumes that the metadata bag (1) is writable, having been safely copied 
    there by another controller.  

    This handler takes a configuration dictionary on construction. The 
    following properties are supported:

    :prop bagparent_dir str #req:  a directory to write output bag to (before
                                 serialization).
    :prop working_dir str None:  a directory where this handler can store its
                                 working data.
    :prop status_manager dict ({'cachedir': ...}): configuration properties for 
                                 for the SIPStatus object used to track the 
                                 status of SIP preservation.  If not set, 
                                 the sub-property 'cachedir' will be set to
                                 a directory call 'preserv_status' just below
                                 the working directory ('working_dir').  
    :prop bagger dict ({}):  the configuration dictionary for the MIDAS 
                                 PreservationBagger instance used to create the
                                 output bag.  
    :prop review_dir str #req:  an existing directory containing MIDAS SIPs
    
    """
    name = "MIDAS3-SIP"
    key = "midas3"

    def __init__(self, sipid, config, minter=None, serializer=None,
                 notifier=None, asupdate=None, sipdatadir=None):
        """
        Configure the handler to process a specific SIP with a given 
        identifier.  The SIP identifier (together with the type of the 
        handler) implies a location for SIP content.  

        :param sipid   str:  an identifer for the SIP that implies its 
                             location.
        :param config dict:  a configuration dictionary specific to the 
                             intended type of SIPHandler.
        :param serializer Serializer:  a Serializer instance to use to 
                             serialize bags.  If not provided the
                             DefaultSerializer from the .serialize module
                             will be used.
        :param notifier NotificationService: the service for pushing alerts
                             to real people.
        :param asupdate bool:  Create this handler assuming this preservation 
                             request is an update to an existing AIP.
        :param sipdatadir str: a relative directory name to look for that 
                               represents the SIP's directory.  If not provided,
                               the directory is determined based on the provided
                               MIDAS ID.  
        """
        SIPHandler.__init__(self, sipid, config, None, serializer, notifier, asupdate)
        self.bagname = self._midasid_to_bagname(self._sipid)
                                               
        workdir = self.cfg.get('working_dir')
        if workdir and not os.path.exists(workdir):
            os.mkdir(workdir)

        self.stagedir = self.cfg.get('staging_dir')
        if not self.stagedir:
            self.stagedir = "stage"
        if not os.path.isabs(self.stagedir):
            if not workdir:
              raise ConfigurationException("Missing needed config property: "+
                                           "working_dir")
            self.stagedir = os.path.join(workdir, self.stagedir)
        if not os.path.exists(self.stagedir):
            os.mkdir(self.stagedir)
        
        datadir = self.cfg.get('review_dir')
        if not datadir:
            raise ConfigurationException("Missing required config property: review_dir")
        if not os.path.exists(datadir):
            raise ConfigurationException("'review_dir' does not exist: "+datadir)
        if not sipdatadir:
            sipdatadir = self._midasid_to_recnum(self._sipid)
        datadir = os.path.join(datadir, sipdatadir)

        bgrcfg = config.get('bagger', {})
        if 'store_dir' not in bgrcfg and 'store_dir' in config:
            bgrcfg['store_dir'] = config['store_dir']
        if 'repo_access' not in bgrcfg and 'repo_access' in config:
            bgrcfg['repo_access'] = config['repo_access']
            if 'store_dir' not in bgrcfg['repo_access'] and 'store_dir' in bgrcfg:
                bgrcfg['repo_access']['store_dir'] = bgrcfg['store_dir']

        isrel = bgrcfg.get('relative_to_indir')
        bagparent = self.cfg.get('bagparent_dir')
        if not bagparent:
            bagparent = "_preserv"
        if not os.path.isabs(bagparent):
            if isrel:
                bagparent = os.path.join(datadir, bagparent)
            else:
                if not workdir:
                    raise ConfigurationException("Missing needed config "+
                                                 "property: workdir_dir")
                bagparent = os.path.join(workdir, bagparent)
                if not os.path.exists(bagparent):
                    os.mkdir(bagparent)

        self.mdbagdir = self.cfg.get('mdbags_dir')
        if not self.mdbagdir:
            self.mdbagdir = "mdbags"
        if not os.path.isabs(self.mdbagdir):
            if not workdir:
                raise ConfigurationException("Missing needed config property: working_dir")
            self.mdbagdir = os.path.join(workdir, self.mdbagdir)
            if not os.path.exists(self.mdbagdir):
                os.mkdir(self.mdbagdir)
        if not os.path.exists(self.mdbagdir):
            raise StateException("Metadata bags directory does not exist as a " +
                                 "directory: " + self.mdbagdir)

        bagname = self._midasid_to_bagname(self._sipid)
        self.sipdir = os.path.join(bagparent, bagname)
        if self.cfg.get('force_copy_mdbag') or not os.path.isdir(self.sipdir):
            self.sipdir = os.path.join(self.mdbagdir, bagname)

        try:
            self.bagger = PreservationM3Bagger(self.sipdir, bagparent, datadir, bgrcfg, self._asupdate)
        except (SIPDirectoryError, PreservationStateError) as ex:
            log.debug("Unable to create PreservationBagger: %s", str(ex))
            self.bagger = None
            self.sipdir = None

        if self.state == status.FORGOTTEN:
            if self._is_preserved():
                log.debug("Detected successful preservation that was forgotten, SIP=%s", self._sipid)
                self.set_state(status.SUCCESSFUL, 
                               "SIP with forgotten state is apparently already preserved")

        self._ingester = None
        ingcfg = self.cfg.get('ingester')
        if ingcfg and ingcfg.get('service_endpoint'):
            self._ingester = IngestClient(ingcfg, log.getChild("ingester"))
        else:
            log.warn("Ingester client not configured: archived records will not get loaded to repo")

        self._doiminter = None
        dmcfg = self.cfg.get('doi_minter')
        if dmcfg and dmcfg.get('datacite_api'):
            self._doiminter = DOIMintingClient(dmcfg, log.getChild("doimint"))
        else:
            log.warn("DOI minting client not configured: archived records will not get submitted to DataCite")

    def isready(self, _inprogress=False):
        """
        do a quick check of the input SIP to determine if it can be 
        processed into an AIP.  If it is not ready, return False.

        :return bool:  True if the requested SIP appears to be ready for 
                       preservation; False, otherwise.
        """
        if not super(MIDAS3SIPHandler, self).isready(_inprogress):
            return False

        if not self.bagger:
            if not self.sipdir:
                self.set_state(status.NOT_FOUND, cache=False)
            return False

        if self.state != status.READY:
            # check for the existence of the input data
            if not os.path.exists(self.bagger.sipdir) or \
               not os.path.exists(self.bagger.datadir):
                if log.isEnabledFor(logging.DEBUG):
                    if not os.path.exists(self.bagger.sipdir):
                        log.debug("SIP metadata bag directory missing: %s", self.bagger.sipdir)
                    if not os.path.exists(self.bagger.datadir):
                        log.debug("SIP data directory missing: %s", self.bagger.datadir)
                self.set_state(status.NOT_FOUND, cache=False)
                return False

            if self.state == status.FORGOTTEN or self.state == status.NOT_READY:
                self.set_state(status.READY,
                               cache=(self.state == status.NOT_READY))
            
        return True
                
    def bagit(self, serialtype=None, destdir=None, params=None):
        """
        create an AIP in the form of serialized BagIt bags from the 
        identified SIP.  The name of the serialized bag files are 
        controlled by the implementation.

        :param serialtype str:  the type of serialization to apply; this 
                                must be a name recognized by the system.  
                                If not provided a default serialization 
                                will be applied (as given in the configuration).
        :param destdir str:     the path to a directory where the serialized
                                bag(s) will be written.  If not provided the
                                configured directory will be used.  
        :param params dict:     SIP-specific parameters to apply to the 
                                creation of the AIP.  These can over-ride 
                                SIP-default behavior as set by the 
                                configuration.
        """
        self._status.start()
        if not serialtype:
            serialtype = 'zip'
        if not destdir:
            destdir = self.storedir

        if not self.isready(_inprogress=True):
            if not os.path.exists(self.datadir):
                log.warn("bagit request for id=%s has missing data dir: "+self.datadir)
            raise StateException("{0}: SIP is not ready: {1}".
                                 format(self._sipid, self._status.message),
                                 sys=_sys)

        # Create the bag.  Note: make_bag() can raise exceptions
        self._status.record_progress("Collecting metadata and files from MIDAS session")
        try:
            bagdir = self.bagger.make_bag()
            self.bagger.bagbldr.record("Preservation bag is built and ready to be serialized.")
        finally:
            if hasattr(self.bagger, 'bagbldr') and self.bagger.bagbldr:
                self.bagger.bagbldr._unset_logfile() # disengage the internal log

        # Stage the full NERDm record for ingest into the RMM
        bag = NISTBag(self.bagger.bagdir)
        nerdm = bag.nerdm_record()
        if self._ingester:
            try:
                self._ingester.stage(nerdm, self.bagger.name)
            except Exception as ex:
                msg = "Failure staging NERDm record for " + self.bagger.name + \
                      " for ingest: " + str(ex)
                log.exception(msg)
                # send an alert email to interested subscribers
                if self.notifier:
                    self.notifier.alert("ingest.failure", origin=self.name,
                                  summary="Ingest failed for "+self.bagger.name,
                                        desc=msg, id=self.bagger.name,
                                        version=nerdm.get('version', 'unknown'))

        # Stage the DataCite DOI record for submission to DataCite
        if self._doiminter and 'doi' in nerdm:
            try:
                self._doiminter.stage(nerdm, name=self.bagger.name)
            except Exception as ex:
                msg = "Failure staging DataCite record for " + self.bagger.name + \
                      " for DOI minting/updating: " + str(ex)
                log.exception(msg)
                if self.notifier:
                    self.notifier.alert("doi.failure", origin=self.name,
                                  summary="DOI minting failed for "+self.bagger.name,
                                        desc=msg, id=self.bagger.name,
                                        version=nerdm.get('version', 'unknown'))

        # zip it up; this may split the bag into multibags
        self._status.record_progress("Serializing")
        savefiles = self._serialize(bagdir, self.stagedir, serialtype)

        # copy the zipped files to long-term storage ("public" directory)
        self._status.record_progress("Delivering preservation artifacts")
        log.debug("writing files to %s", destdir)
        errors = []
        saved = []
        try:
            for f in savefiles:
                destfile = os.path.join(destdir, os.path.basename(f))
                if os.path.exists(destfile) and \
                   not self.cfg.get('allow_bag_overwrite', False):
                    raise OSError(errno.EEXIST, os.strerror(errno.EEXIST),
                                  destfile)
                shutil.copy(f, destdir)
                saved.append(f)
        except OSError, ex:
            log.error("Failed to copy preservation file: %s\n" +
                      "  to long-term storage: %s", f, destdir)
            log.exception("Reason: %s", str(ex))
            log.error("Rolling back successfully copied files")
            msg = "Failed to copy preservation files to long-term storage"
            self.set_state(status.FAILED, msg)

            for f in saved:
                fp = os.path.join(destdir, os.path.basename(f))
                if os.path.exists(fp):
                    log.warn("Removing %s from long-term storage", f)
                    os.remove(fp)

            raise PreservationException(msg, [str(ex)])

        # Now write copies of the checksum files to the review SIP dir.
        # MIDAS will scoop these up and save them in its database.
        # The file with sequence number 0 must be written last; this is a
        # signal that preservation is complete.
        try:
            sigbase = self.bagname+"_"
            ckspat = re.compile(self.bagname+r'.*-(\d+).\w+.sha256$')
            cksfiles = [f for f in savefiles if ckspat.search(f)]
            cksfiles.sort(key=lambda f: int(ckspat.search(f).group(1)),
                          reverse=True)
            log.debug("copying %s checksum files to %s",
                      str(len(cksfiles)), self.bagger.bagparent)
            cpfailures = []
            for f in cksfiles:
                try:
                    sigfile = sigbase+ckspat.search(f).group(1)+'.sha256'
                    sigfile = os.path.join(self.bagger.bagparent,sigfile)
                    log.debug("copying checksum file to %s", sigfile)
                    shutil.copyfile(f, sigfile)
                except Exception, ex:
                    msg = "Failed to copy checksum file to review dir:" + \
                          "\n %s to\n %s\nReason: %s" % \
                          (f, sigfile, str(ex))
                    log.exception(msg)
                    cpfailures.append(msg)

            if cpfailures and self.notifier:
                # alert subscribers of these failures with an email
                self.notifier.alert("preserve.failure", origin=self.name,
                                    summary="checksum file copy failure", desc=msg,
                                    version=nerdm.get('version', 'unknown'))
                    
        except Exception, ex:
            msg = "%s: Failure while writing checksum file(s) to review dir: %s" \
                  % (self._sipid, str(ex))
            log.exception(msg)
            if self.notifier:
                self.notifier.alert("preserve.failure", origin=self.name,
                                    summary="checksum file write failure",
                                    desc=msg, id=self._sipid,
                                    version=nerdm.get('version', 'unknown'))
                
        # cache the latest nerdm record under the staging directory
        try:
            mdcache = os.path.join(self.stagedir, '_nerd')
            staged = os.path.join(mdcache, self.bagger.name+".json")
            if os.path.isdir(mdcache):
                write_json(nerdm, staged)
        except Exception as ex:
            log.error("Failed to cache the new NERDm record: "+str(ex))
            if os.path.exists(staged):
                # remove the old record as it is now out of date
                os.remove(staged)

        self.set_state(status.SUCCESSFUL)

        # submit NERDm record to ingest service
        if self._ingester and self._ingester.is_staged(self.bagger.name):
            try:
                self._ingester.submit(self.bagger.name)
                log.info("Submitted NERDm record to RMM")
            except Exception as ex:
                msg = "Failed to ingest record with name=" + \
                      self.bagger.name + " into RMM: " + str(ex)
                log.exception(msg)
                log.info("Ingest service endpoint: %s", self._ingester.endpoint)

                if self.notifier:
                    self.notifier.alert("ingest.failure", origin=self.name,
                          summary="NERDm ingest failure: " + self.bagger.name,
                                        desc=msg, id=self.bagger.name,
                                        version=nerdm.get('version', 'unknown'))

        # submit NERDm record to ingest service
        if self._doiminter and self._doiminter.is_staged(self.bagger.name):
            try:
                self._doiminter.submit(self.bagger.name)
                log.info("Submitted DOI record to DataCite")
            except Exception as ex:
                msg = "Failed to submit DOI record with name=" + \
                      self.bagger.name + " to DataCite: " + str(ex)
                log.exception(msg)
                log.info("DOI minter service endpoint: %s", self._doiminter.dccli._ep)

                if self.notifier:
                    self.notifier.alert("doi.failure", origin=self.name,
                          summary="NERDm ingest failure: " + self.bagger.name,
                                        desc=msg, id=self.bagger.name,
                                        version=nerdm.get('version', 'unknown'))

        # tell a human that things are great!
        if self.notifier:
            self.notifier.alert("preserve.success", origin=self.name,
                           summary="New MIDAS SIP preserved: "+self.bagger.name,
                                id=self.bagger.name,
                                version=nerdm.get('version', 'unknown'))

        # clean up staging area
        if self.cfg.get('clean_bag_staging', True):
            headbag = None
            if not self.cfg.get('clean_headbag_staging', False):
                bags = [b for b in [os.path.basename(f) for f in savefiles]
                          if bagutils.is_legal_bag_name(b) and
                             not b.endswith('sha256')]
                if len(bags):
                    headbag = '/' + bagutils.find_latest_head_bag(bags)
            for f in savefiles:
                if f.endswith(headbag):
                    continue
                try:
                    os.remove(f)
                except Exception, ex:
                    log.error("Trouble cleaning up serialized bag in staging "+
                          "dir:\n  %s\nReason: %s", f, str(ex))

        if self.cfg.get('signal_done'):
            requests.get(self.cfg.get('signal_done'),
                         headers={'Authorization': "Bearer "+self.cfg.get('auth_key')})

        log.info("Completed preservation of SIP %s", self.bagger.name)
        
    def _is_preserved(self):
        """
        return True if some version of this SIP has been preserved (i.e. sent 
        successfully through the Preservation Service).  This look for as 
        definitive evidence of success (i.e. existence in long-term storage) 
        as possible.
        """
        bagname = (self.bagger and self.bagger.name) or self.bagname

        # look for files in the serialized bag store with names that start
        # with the SIP identifier
        return len([f for f in os.listdir(self.storedir) if f.startswith(bagname+'.')]) > 0
    
    def _midasid_to_bagname(self, id):
        return midasid_to_bagname(id)

    def _midasid_to_recnum(self, id):
        return _midadid_to_dirname(id)


    
