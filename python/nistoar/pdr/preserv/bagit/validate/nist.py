"""
This module implements a validator for the NIST-generated bags
"""
import os, re
from collections import OrderedDict
from urlparse import urlparse

from .base import (Validator, ValidatorBase, ALL, ValidationResults,
                   ERROR, WARN, REC, ALL, PROB, AggregatedValidator)
from .bagit import BagItValidator
from .multibag import MultibagValidator
from ..bag import NISTBag

class NISTBagValidator(ValidatorBase):
    """
    A validator that runs tests for compliance for the NIST Preservation Bag
    Profile.  Specifically, this validator only covers the NIST Profile-specific
    parts (excluding Multibag and basic BagIt compliance; see 
    PreservationBagValidator)
    """
    profile = ("NIST", "0.2")
    namere = re.compile("^(\w+).mbag(\d+)_(\d+)-(\d+)$")
    
    def __init__(self, config=None):
        super(NISTBagValidator, self).__init__(config)

    def test_name(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        t = self._issue("2-0", "Bag names should match format DSID.mbagMM_NN-SS")
        nm = self.namere.match(bag.name)
        out._warn(t, nm)

        if nm:
            t = self._issue("2-2", "Bag name should include version 'mbag{0}'")
            vers = self.profile[1].split('.')
            out._warn(t, nm.group(2) == vers[0] and nm.group(3) == vers[1])

        return out
        

class NISTAIPValidator(AggregatedValidator):
    """
    An AggregatedValidator that validates the complete profile for bags 
    created by the NIST preservation service.  
    """
    def __init__(self, config=None):
        if not config:
            config = {}
        bagit = BagitValidator(config=config.get("bagit", {}))
        multibag = MultibagValidator(config=config.get("multibag", {}))
        nist = NISTBagValidator(config=config.get("nist", {}))

        super(PreservationBagValidator, self).__init__(
            bagit,
            multibag,
            nist
        )

