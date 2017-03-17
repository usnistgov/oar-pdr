"""
This module manages the preparation of the metadata needed by pre-publication
landing page service.  It uses an SIPBagger to create the NERDm metadata from 
POD metadata provided by MIDAS and assembles it into an exportable form.  
"""
import os, logging, re, json

from collections import Mapping
from .. import PublishSystem
from ..exceptions import *
from ...preserv.bagger import MIDASMetadataBagger
from ...preserv.bagit import NISTBag
from ....id import PDRMinter

log = logging.getLogger(PublishSystem().subsystem_abbrev)

class PrePubMetadataService(PublishSystem):
    """
    The class providing the implementation for the pre-publication metadata
    service.
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
            raise ValueError("PrePubMetadataService: config argument not a " +
                             "dictionary: " + str(config))
        self.cfg = config

        self.log = log.getChild("mdserv")
        
        if not workdir:
            workdir = self.cfg.get('working_dir')
        if not workdir:
            raise ConfigurationException("Missing required config parameters: "
                                         "working_dir")
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir)
        self.workdir = workdir

        if not reviewdir:
            reviewdir = self.cfg.get('review_dir')
        if not reviewdir:
            raise ConfigurationException("Missing required config parameters: "
                                         "review_dir")
        if not os.path.isdir(reviewdir):
            raise StateException("MIDAS review directory does not exist as a " +
                                 "directory: " + reviewdir)
        self.reviewdir = reviewdir

        if not uploaddir:
            uploaddir = self.cfg.get('upload_dir')
        if not uploaddir:
            raise ConfigurationException("Missing required config parameters: "
                                         "upload_dir")
        if not os.path.isdir(uploaddir):
            raise StateException("MIDAS Upload directory does not exist as a " +
                                 "directory: " + uploaddir)
        self.uploaddir = uploaddir

        if not idregdir:
            idregdir = self.cfg.get('id_registry_dir', self.workdir)
        if not os.path.isdir(idregdir):
            raise StateException("ID Registry directory does not exist as a " +
                                 "directory: " + idregdir)

        self._minter = self._create_minter(idregdir)

    def _create_minter(self, parentdir):
        cfg = self.cfg.get('id_minter', {})
        out = PDRMinter(parentdir, cfg)
        if not os.path.exists(out.registry.store):
            self.log.warn("Creating new ID minter")
        return out

    def prepare_metadata_bag(self, id):
        """
        Bag up the metadata from data provided by MIDAS for a given MIDAS ID.  
        """
        cfg = self.cfg.get('bagger', {})
        bagger = MIDASMetadataBagger(id, self.workdir, self.reviewdir,
                                     self.uploaddir, cfg, self._minter)
        bagger.ensure_preparation()
        return bagger.bagdir

    def make_nerdm_record(self, bagdir):
        """
        Given a metadata bag, generate a complete NERDm resource record.
        """
        bag = NISTBag(bagdir)
        return bag.nerdm_record()

    def resolve_id(self, id):
        """
        return a full NERDm resource record corresponding to the given 
        MIDAS ID.  
        """
        return self.make_nerdm_record(self.prepare_metadata_bag(id))
        
        
