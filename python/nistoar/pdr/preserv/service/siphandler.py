"""
This module provides an abstract interface turning a Submission Information 
Package (SIP) into an Archive Information Package (BagIt bags).  It also 
includes implementations for different known SIPs
"""
import os, re, shutil, logging
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict
from copy import deepcopy

from ..bagit.serialize import DefaultSerializer
from ..bagger.base import checksum_of
from ..bagger.midas import PreservationBagger
from .. import (ConfigurationException, StateException, PODError)
from .. import PreservationException, sys as _sys
from . import status
from ...ingest.rmm import IngestClient

log = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)

class SIPHandler(object):
    """
    The abstract interface for processing an Submission Information Package 
    (SIP).  To launch the preservation of an SIP, one instantiates an 
    implementation of this handler class that is knowledgable of the type
    of SIP being processed, assigning to it the specific SIP to process. 
    Then, the bagit() function is called to assemble and write the serialized 
    bag to a particular destination directory.

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

    def __init__(self, sipid, config, minter=None, serializer=None):
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
        """
        self._sipid = sipid
        self.cfg = deepcopy(config)
        self._minter = minter
        if not serializer:
            serializer = DefaultSerializer()
        self._ser = serializer

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

        # The initial state will be FORGOTTEN unless another handler has
        # already started.
        self._status = status.SIPStatus(self._sipid, stcfg)

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
    def status(self):
        """
        a dictionary describing the current status of the SIP's preservation.
        """
        return self._status.user_export()

    @property
    def state(self):
        """
        the label indicating the current state ofthe SIP's preservation.  This
        is equivalent to self.status['state'].  
        """
        return self._status.state

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
        #TODO:  splitting large submissions

        self._status.data['user']['bagfiles'] = []
        file1 = self._ser.serialize(bagdir, destdir, format)
        for file in [file1]:
            csumfile = file + ".sha256"
            csum = checksum_of(file)
            with open(csumfile, 'w') as fd:
                fd.write(csum)
                fd.write('\n')

            # write the checksum to our status object
            self._status.data['user']['bagfiles'].append({
                'name': os.path.basename(file),
                'sha256': csum
            })

        self._status.cache()
        return [file1, csumfile]

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

    def __init__(self, sipid, config, minter=None, serializer=None):
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
        """
        super(MIDASSIPHandler, self).__init__(sipid, config, minter, serializer)

        workdir = self.cfg.get('working_dir')
        if workdir and not os.path.exists(workdir):
            os.mkdir(workdir)

        isrel = self.cfg.get('bagger',{}).get('relative_to_indir')
        bagparent = self.cfg.get('bagparent_dir')
        if not bagparent:
            bagparent = "_preserv"
        if not os.path.isabs(bagparent):
            if not isrel:
                if not workdir:
                    raise ConfigurationException("Missing needed config "+
                                                 "property: workdir_dir")
                bagparent = os.path.join(workdir, bagparent)
                if not os.path.exists(bagparent):
                    os.mkdir(bagparent)

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

        self.mdbagdir = self.cfg.get('mdbag_dir')
        if not self.mdbagdir:
            self.mdbagdir = "mdserv"
        if not os.path.isabs(self.mdbagdir):
            if not workdir:
              raise ConfigurationException("Missing needed config property: "+
                                           "working_dir")
            self.stagedir = os.path.join(workdir, self.mdbagdir)
            if not os.path.exists(self.mdbagdir):
                os.mkdir(self.mdbagdir)
        if not os.path.exists(self.mdbagdir):
            raise StateException("Metadata directory does not exist as a " +
                                 "directory: " + self.mdbagdir)
        
        self.bagger = PreservationBagger(sipid, bagparent, self.sipparent,
                                         self.mdbagdir, config.get('bagger'),
                                         self._minter)

        if self.state == status.FORGOTTEN and self._is_preserved():
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

        Implementations should first call this inherited version which ensures 
        that the current status is either FORGOTTEN, PENDING, or READY.  False
        is returned if this is not true, and the child implementation should not 
        proceed.  The child implementation should then do a quick check that the
        input data exists and appears to be in a state ready for preservation.  
        It should finally set the _ready field to True.

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

        # Create the bag
        self._status.record_progress("Collecting metadata and files")
        bagdir = self.bagger.make_bag()

        # zip it up 
        self._status.record_progress("Serializing")
        savefiles = self._serialize(bagdir, self.stagedir, serialtype)

        # copy the zipped files to long-term storage ("public" directory)
        self._status.record_progress("Delivering preservation artifacts")
        log.debug("writing files to %s", destdir)
        errors = []
        try:
            for f in savefiles:
                shutil.copy(f, destdir)
        except OSError, ex:
            log.error("Failed to copy preservation file: %s\n" +
                      "  to long-term storage: %s", f, destdir)
            log.exception("Reason: %s", str(ex))
            log.error("Rolling back successfully copied files")
            msg = "Failed to copy preservation files to long-term storage"
            self.set_state(status.FAILED, msg)

            for f in savefiles:
                f = os.path.join(destdir, os.path.basename(f))
                if os.path.exists(f):
                    os.remove(f)

            raise PreservationException(msg, [str(ex)])

        # Stage the full NERDm record for ingest into the RMM
        if self._ingester:
            try:
                bag = NISTBag(self.bagger.bagdir)
                self._ingester.stage(bag.nerdm_record(), self.bagger.name)
            except Exception as ex:
                log.exception("Failure staging NERM record for " +
                              self.bagger.name + ": " + str(ex))

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
            for f in cksfiles:
                try:
                    sigfile = sigbase+ckspat.search(f).group(1)+'.sha256'
                    sigfile = os.path.join(self.bagger.bagparent,sigfile)
                    log.debug("copying checksum file to %s", sigfile)
                    shutil.copyfile(f, sigfile)
                except Exception, ex:
                    log.exception("Failed to copy checksum file to review dir:"+
                                  "\n %s to\n %s\nReason: %s", f,
                                  open.path.join(self.bagger.indir), str(ex))
                    
        except Exception, ex:
            log.exception("%s: Failure while writing checksum file(s) to "+
                          "review dir: %s", self._sipid, str(ex))
                
        self.set_state(status.SUCCESSFUL)

        # submit NERDm record to ingest service
        if self._ingester and self._ingester.is_staged(self.bagger.name):
            try:
                self._ingester.submit(self.bagger.name)
            except Exception as ex:
                self.log.exception("Failed to ingest record with name=" +
                                   self.bagger.name + "into RMM: " + str(ex))

        # clean up staging area
        for f in savefiles:
            try:
                os.remove(f)
            except Exception, ex:
                log.error("Trouble cleaning up serialized bag in staging dir: "+
                          "\n  %s\nReason: %s", f, str(ex))

    def _is_preserved(self):
        """
        return True if some version of this SIP has been preserved (i.e. sent successfully through
        the Preservation Service).  This look for as definitive evidence of success (i.e. existence
        in long-term storage) as possible.
        """
        bagname = self.bagger.form_bag_name(self.bagger.name)
        return len([f for f in os.listdir(self.storedir) if f.startswith(bagname)]) > 0
    
