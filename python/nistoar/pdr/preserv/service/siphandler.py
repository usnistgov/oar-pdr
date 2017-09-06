"""
This module provides an abstract interface turning a Submission Information 
Package (SIP) into an Archive Information Package (BagIt bags).  It also 
includes implementations for different known SIPs
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict
from copy import deepcopy

from ..bagit.serialize import DefaultSerializer
from ..bagger.base import checksum_of, PreservationException
from ..bagger.midas import PreservationBagger
from .. import sys as _sys

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

        # set up the Status manager
        stcfg = self.cfg.get('status_manager', {})
        if 'cachedir' not in stcfg:
            stcfg['cachedir'] = os.path.join(self.workdir, "preserv_status")

        # The initial state will be FORGOTTEN unless another handler has
        # already started.
        self._status = status.SIPStatus(self._sipid, stcfg)

    @abstractmethod
    def isready(self):
        """
        do a quick check of the input SIP to determine if it can be 
        processed into an AIP.  If it is not ready, return False.

        Implementations should first call this inherited version which ensures 
        that the current status is either FORGOTTEN, PENDING, or READY.  False
        is returned if this is not true, and the child implementation should not 
        proceed.  The child implementation should then do a quick check that the
        input data exists and appears to be in a state ready for preservation.  
        """
        return self._status.state in (status.FORGOTTEN, status.PENDING,
                                      status.READY)

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
        return self._status.data

    @property
    def state(self):
        """
        the label indicating the current state ofthe SIP's preservation.  This
        is equivalent to self.status['state'].  
        """
        return self._status.state

    def set_state(self, state, message=None):
        """
        update the status of the preservation to that of the given label.
        A message intended for the external user can optionally be provided.
        This status will get cached to disk so that it is accessible by other
        processes.
        """
        self._status.update(state, message)

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
        
        file1 = self._ser.serialize(bagdir, destdir, format)
        for file in [file1]:
            csumfile = os.path.splitext(file)[0] + ".sha256"
            csum = checksum_of(file)
            with open(csumfile, 'w') as fd:
                fd.write(csum)
                fd.write('\n')

        return [file1, csumfile]
    
class MIDASSIPHandler(object):
    """
    The interface for processing an Submission Information Package 
    (SIP) from the MIDAS system.

    This handler takes a configuration dictionary on construction. The 
    following properties are supported:

    :prop working_dir str #req:  a directory where this handler can store its
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

        self.workdir = self.cfg.get('working_dir')
        if not self.workdir:
            raise ConfigurationException("Missing required config property: "+
                                         "working_dir")
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        
        self.stagedir = self.cfg.get('staging_dir')
        if not self.stagedir:
            self.stagedir = os.path.join(self.workdir, "_stage")
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
            raise ConfigurationException("Missing required config property: "+
                                         "mdbag_dir")
        if not os.path.exists(self.mdbagdir):
            os.mkdir(self.mdbagdir)
        
        self.bagger = PreservationBagger(sipid, self.workdir, self.sipparent,
                                         self.mdbagdir, config.get('bagger'),
                                         self.minter)

    def isready(self):
        """
        do a quick check of the input SIP to determine if it can be 
        processed into an AIP.  If it is not ready, return False.

        Implementations should first call this inherited version which ensures 
        that the current status is either FORGOTTEN, PENDING, or READY.  False
        is returned if this is not true, and the child implementation should not 
        proceed.  The child implementation should then do a quick check that the
        input data exists and appears to be in a state ready for preservation.  
        It should finally set the current state to READY.

        :return bool:  True if the requested SIP appears to be ready for 
                       preservation; False, otherwise.
        """
        if not super(MIDASSIPHandler, self).isready():
            return False

        if self.state != status.READY:
            # check for the existence of the input data
            if not os.path.exists(self.bagger.indir):
                self.status.update(status.NOT_FOUND)

            # make sure the input SIP includes a POD file
            try:
                self.bagger.find_pod_file()
            except PODError, e:
                self.status.update(status.NOT_FOUND, "missing POD record")
                return False

            self.status.update(status.READY)
            
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
        if not self.isready():
            raise StateException("{0}: SIP is not ready: {1}".
                                 format(self._sipid, self.status.message),
                                 sys=_sys)

        bagdir = self.bagger.make_bag()
        savefiles = self._serialize(bagdir, stagedir, serialtype)
        errors = []
        for f in savefiles:
            try:
                os.rename(f, self.storedir)
            except OSError, ex:
                msg = "{0}: {1}".format(f, ex.message)
                logger.error(msg)
                errors.append(msg)

        if errors:
            msg = "Failed to copy all preservation files to long-term " \
                  "storage dir ({0})"
            msg = msg.format(self.storedir)
            self.status.update(status.FAILED, msg)
            raise PreservationError(msg, errors)

