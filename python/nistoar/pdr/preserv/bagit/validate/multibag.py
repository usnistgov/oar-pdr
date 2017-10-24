"""
This module implements a validator for the Multibag Profile
"""
import os, re
from collections import OrderedDict
from urlparse import urlparse

from .base import (Validator, ValidatorBase, ALL, ValidationResults,
                   ERROR, WARN, REC, ALL, PROB)
from ..bag import NISTBag

class MultibagValidator(ValidatorBase):
    """
    A validator that runs tests for compliance with the Multibag Bagit Profile.
    In particular, this validator tests whether a given bag can be consider
    part of a multibag aggregation.  
    """
    profile = ("Multibag", "0.2")

    def __init__(self, config=None):
        super(MultibagValidator, self).__init__(config)

    def test_version(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        data = bag.get_baginfo()

        t = self._issue("1.2-Version",
              "bag-info.txt field must have required element: Multibag-Version")
        out._err(t, "Multibag-Version" in data and 
                    len(data["Multibag-Version"]) > 0)
        if t.failed():
            return out

        t = self._issue("1.2-Version",
                "bag-info.txt field, Multibag-Version, should only appear once")
        out._warn(t, len(data["Multibag-Version"]) == 1)

        t = self._issue("1.2-Version-val",
                      "Multibag-Version must be set to '0.2'")
        out._err(t, data["Multibag-Version"][-1] == "0.2")
        
        return out

    def test_reference(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        data = bag.get_baginfo()
        t = self._issue("1.2-Reference",
                        "bag-info.txt should include field: Multibag-Reference")
        out._rec(t, "Multibag-Reference" in data and
                    len(data["Multibag-Version"]) > 0)
        if t.failed():
            return out

        t = self._issue("1.2-Reference-val",
                        "Empty value given for Multibag-Reference")
        url = data["Multibag-Reference"][-1]
        out._err(t, bool(url))

        t = self._issue("1.2-Reference-val",
                        "Multibag-Reference value is not an absolute URL")
        url = urlparse(url)
        out._err(t, url.scheme and url.netloc)

        return out

    def test_tag_directory(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        data = bag.get_baginfo()
        if "Multibag-Tag-Directory" in data:
            mdir = data["Multibag-Tag-Directory"]

            t = self._issue("1.2-Tag-Directory",
            "bag-info.txt: Value for Multibag-Tag-Directory should not be empty")
            out._err(t, len(mdir) > 0 and mdir[-1])
            if t.failed():
                return out

            t = self._issue("1.2-Tag-Directory",
         "bag-info.txt: Multibag-Tag-Directory element should only appear once")
            out._err(t, len(mdir) == 1)

            t = self._issue("1.2-Tag-Directory",
                            "Multibag-Tag-Directory must exist as directory")
            out._err(t, os.path.isdir(os.path.join(bag.dir, mdir[-1])))

        else:
            t = self._issue("1.2-Tag-Directory",
                         "Default Multibag-Tag-Directory, multibag, must exist")
            out._err(t, os.path.exists(os.path.join(bag.dir, "multibag")))

        return out

    def test_head_version(self, bag, want=ALL, results=None, ishead=False):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        data = bag.get_baginfo()
        if "Multibag-Head-Version" in data:
            value = data["Multibag-Head-Version"] 

            t = self._issue("1.2-Head-Version",
            "bag-info.txt: Value for Multibag-Head-Version should not be empty")
            out._warn(t, len(value) > 0 and value[-1])
            if t.failed():
                return out

            t = self._issue("1.2-Head-Version",
         "bag-info.txt: Multibag-Head-Version element should only appear once")
            out._warn(t, len(value) == 1)

        else:
            t = self._issue("1.2-Head-Version",
                "Head bag: bag-info.txt must have Multibag-Head-Version element")
            out._err(t,  ishead)

        return out

    def test_head_deprecates(self, bag, want=ALL, results=None, ishead=False):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        data = bag.get_baginfo()
        headver = data.get("Multibag-Head-Version", [""])[-1]
        if "Multibag-Head-Deprecates" in data:
            values = data["Multibag-Head-Deprecates"]

            t = self._issue("1.2-Head-Deprecates",
                            "bag-info.txt: Multibag-Head-Deprecates "+
                            "element should only appear in non-head bags")
            out._warn(t, not ishead)

            t = self._issue("1.2-Head-Deprecates",
          "bag-info.txt: Value for Multibag-Head-Deprecates should not be empty")
            out._warn(t, len(values) > 0)
            if t.failed():
                return out

            empty = False
            selfdeprecating = False
            for val in values:
                empty = empty or not val
                selfdeprecating = selfdeprecating or val == headver

            t = self._issue("1.2-Head-Deprecates",
                            "bag-info.txt: Value for Multibag-Head-Deprecates "+
                            "should not be empty")
            out._warn(t, not empty)
            t = self._issue("1.2-Head-Deprecates",
                            "bag-info.txt: Multibag-Head-Deprecates should not "+
                            "deprecate itself")
            out._warn(t, not selfdeprecating)

        return out

    def test_baginfo_recs(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        data = bag.get_baginfo()

        for el in ["Internal-Sender-Identifier",
                   "Internal-Sender-Description", "Bag-Group-Identifier"]:
            t = self._issue("1.2-2", "Recommed adding value for "+el+ 
                            " into bag-info.txt file")
            out._rec(t, el in data and len(data[el]) > 0 and data[el][-1])
            if t.failed():
                continue
            t = self._issue("1.2-2", "bag-info.txt: "+el+" element should not "+
                            "have empty values")
            out._err(t, all(data[el]))

        return out

