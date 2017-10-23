"""
This module implements a validator for the Multibag Profile
"""
import os, re
from collections import OrderedDict
from urlparse import urlparse

from .base import Validator, ValidatorBase, ValidationIssue, _VIE, _VIW, _VIR
from ..bag import NISTBag

class MultibagValidator(ValidatorBase):
    """
    A validator that runs tests for compliance with the Multibag Bagit Profile.
    In particular, this validator tests whether a given bag can be consider
    part of a multibag aggregation.  
    """
    profile = "Multibag 0.2"

    def __init__(self, config=None):
        super(MultibagValidator, self).__init__(config)

    def test_version(self, bag):
        out = []
        data = bag.get_baginfo()
        if "Multibag-Version" not in data or len(data["Multibag-Version"]) == 0:
            out +=[self._err("1.2-Version",
                        "Missing required bag-info.txt field: Multibag-Version")]
            return out
        
        if len(data["Multibag-Version"]) > 1:
            out +=[self._warn("1.2-Version",
                "bag-info.txt field, Multibag-Version, should only appear once")]
        
        if data["Multibag-Version"][-1] != "0.2":
            out +=[self._err("1.2-Version-val",
                            "Multibag-Version must be set to '0.2'")]
        return out

    def test_reference(self, bag):
        out = []
        data = bag.get_baginfo()
        if "Multibag-Reference" not in data or len(data["Multibag-Version"])==0:
            out +=[self._rec("1.2-Reference",
                        "Should include bag-info.txt field: Multibag-Reference")]
            return out
            
        url = data["Multibag-Reference"][-1]
        if not url:
            out +=[self._err("1.2-Reference-val",
                            "Empty value given for Multibag-Reference")]
            return out

        url = urlparse(url)
        if not url.scheme or not url.netloc:
            out+=[self._err("1.2-Reference-val",
                           "Multibag-Reference value is not an absolute URL")]
        return out

    def test_tag_directory(self, bag):
        out = []
        data = bag.get_baginfo()
        if "Multibag-Tag-Directory" in data:
            mdir = data["Multibag-Tag-Directory"]
            if len(mdir) == 0 or not mdir[-1]:
                out+=[self._err("1.2-Tag-Directory",
                                "Empty value given for Multibag-Tag-Directory")]
                return out
            
            if len(mdir) > 1:
                out+=[self._err("1.2-Tag-Directory",
         "bag-info.txt field, Multibag-Tag-Directory, should only appear once")]
                
            if not os.path.exists(os.path.join(bag.dir,mdir[-1])):
                out+=[self._err("1.2-Tag-Directory",
                                "Multibag-Tag-Directory does not exist")]

        elif not os.path.exists(os.path.join(bag.dir, "multibag")):
            out += [self._err("1.2-Tag-Directory",
                             "Default tag directory, multibag, does not exist")]
        return out

    def test_head_version(self, bag, ishead=False):
        out = []

        data = bag.get_baginfo()
        if "Multibag-Head-Version" in data:
            value = data["Multibag-Head-Version"] 

            if len(value) == 0 or not value[-1]:
                out+=[self._warn("1.2-Head-Version",
          "Empty value provided for bag-info.txt field: Multibag-Head-Version")]
                return out

            if len(value) > 1:
                out +=[self._warn("1.2-Head-Version",
          "bag-info.txt field, Multibag-Head-Version, should only appear once")]

        elif ishead:
            out += [self._err("1.2-Head-Version",
                 "Head Bag: Missing bag-info.txt field: Multibag-Head-Version")]

        return out

    def test_head_deprecates(self, bag, ishead=False):
        out = []

        data = bag.get_baginfo()
        headver = data.get("Multibag-Head-Version", [""])[-1]
        if "Multibag-Head-Deprecates" in data:
            values = data["Multibag-Head-Deprecates"]

            if not ishead:
                out+=[self._warn("1.2-Head-Deprecates",
                                "bag-info.txt field, Multibag-Head-Deprecates, "+
                                "should not appear in non-head bags")]

            if len(values) == 0:
                out+=[self._warn("1.2-Head-Deprecates",
       "Empty value provided for bag-info.txt field: Multibag-Head-Deprecates")]
                return out

            for val in values:
                if not val:
                    out+=[self._warn("1.2-Head-Deprecates",
       "Empty value provided for bag-info.txt field: Multibag-Head-Deprecates")]
                elif val == headver:
                    out+=[self._warn("1.2-Head-Deprecates",
                                     "In bag-info.txt, Multibag-Head-Deprecates"+
                                     " value matches Multibag-Head-Version")]

        return out

    def test_baginfo_recs(self, bag):
        out = []
        data = bag.get_baginfo()

        for el in ["Internal-Sender-Identifier",
                   "Internal-Sender-Description", "Bag-Group-Identifier"]:
            if el not in data or len(data[el]) < 1 or not data[el][-1]:
                out+=[self._rec("1.2-2", "Recommed adding value for "+el+ 
                                " into bag-info.txt file")]
                continue
            for val in data[el]:
                if not val:
                    out+=[self._err("1.2-2", "Empty value provided for " +
                                    "bag-info.txt element: "+el)]
        return out

