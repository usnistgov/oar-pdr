"""
This module implements a validator for the base BagIt standard
"""
import os, re
from collections import OrderedDict
from urlparse import urlparse

from .base import Validator, ValidatorBase
from ..bag import NISTBag
from ..builder import checksum_of

csfunctions = {
    "sha256":  checksum_of
}

class BagItValidator(ValidatorBase):
    """
    A validator that runs tests for compliance to the base BagIt standard
    """
    profile = "BagIt v0.97"

    def __init__(self, config=None):
        super(BagItValidator, self).__init__(config)

    def test_bagit_txt(self, bag):
        """
        test that the bagit.txt file exists and has the required contents
        """
        out = []
        bagitf = os.path.join(bag.dir, "bagit.txt")
        if os.path.exists(bagitf):
            baginfo = bag.get_baginfo(bagitf)
            try:
                if baginfo['BagIt-Version'] != ["0.97"]:
                    out.append( self._err("2.1.1-3",
                                     "bagit.txt: BagIt-Version not set to 0.97"))
            except KeyError:
                out.append( self._err("2.1.1-2",
                                   "bagit.txt: missing element: BagIt-Version") )
            try:
                if baginfo['Tag-File-Character-Encoding'] != ["UTF-8"]:
                    out.append( self._err("2.1.1-5",
                                     "bagit.txt: Tag-File-Character-Encoding "+
                                     "not set to UTF-8"))
            except KeyError:
                out.append( self._err("2.1.1-4",
                                      "bagit.txt: missing element: " +
                                      "Tag-File-Character-Encoding") )

            if len(out) == 0 and \
               baginfo.keys() != ["BagIt-Version","Tag-File-Character-Encoding"]:
                out.append( self._rec("2.1.1-6",
                                      "bagit.txt: recommend using this " +
                                      "element order: BagIt-Version " +
                                      "Tag-File-Character-Encoding") )

        else:
            out.append(self._err("2.1.1-1", "bag-info.txt file is missing"))

        return out

    def test_data_dir(self, bag):
        """
        test that the data directory exists
        """
        out = []
        if not os.path.exists(os.path.join(bag.dir, "data")):
            out += [ self._err("2.1.2", "Missing payload directory, data/") ]
        return out

    def test_manifest(self, bag):
        tcfg = self.cfg.get("test_manifest", {})
        check = tcfg.get('check_checksums', True)
        return self._test_manifest(bag, "manifest", check)

    def test_tagmanifest(self, bag):
        tcfg = self.cfg.get("test_manifest", {})
        check = tcfg.get('check_checksums', True)
        return self._test_manifest(bag, "tagmanifest", check)

    def _test_manifest(self, bag, basename, check):
        out = []
        manire = re.compile(r'^{0}-(\w+).txt$'.format(basename))
        manifests = [f for f in os.listdir(bag.dir) if manire.match(f)]
        if len(manifests) > 0:
            for mfile in manifests:
                alg = manire.match(mfile).group(1)
                csfunc = None
                if alg in csfunctions:
                    csfunc = csfunctions[alg]

                badlines = []
                notdata = []
                paths = OrderedDict()
                with open(os.path.join(bag.dir, mfile)) as fd:
                    i = 0
                    for line in fd:
                        i += 1
                        parts = line.split()
                        if len(parts) != 2:
                            badlines.append(i)
                            continue
                        if parts[1].startswith('*'):
                            parts[1] = parts[1][1:]
                            parts.append('*')

                        if basename == "manifest" and \
                           not parts[1].startswith('data/'):
                            notdata.append(parts[1])
                        else:
                            paths[parts[1]] = parts[0]

                if badlines:
                    if len(badlines) > 4:
                        badlines[3] = "..."
                        badlines = badlines[:4]
                    out += [self._err("2.1.3-2",
                                      "{0} format issues found (lines {1})"
                                      .format(mfile, ", ".join([str(b)
                                                        for b in badlines])))]

                if notdata:
                    s = (len(notdata) > 1 and "s") or ""
                    out += [self._err("2.1.3-3",
                        "{0} lists {1} non-payload (i.e. under data/) file{2}"
                                      .format(mfile, len(notdata), s))]

                # make sure all paths exist
                badpaths = []
                for datap in paths:
                    fp = os.path.join(bag.dir, datap)
                    if not os.path.exists(fp):
                        badpaths.append(datap)
                    elif not os.path.isfile(fp):
                        out += [self._err("2.1.3-7",
                                          "Manifest entry is not a file: "+
                                          datap)]

                if badpaths:
                    for datap in badpaths[:4]:
                        out += [self._err("3-1-2",
                                          "Path in manifest missing in bag: "+
                                          datap)]
                    if len(badpaths) > 4:
                        addl = len(badpaths) - 3
                        out[-1] = self._err("3-1-2",
                   "{0} additional files missing from payload (data/) directory"
                                            .format(addl))

                # check that all files in the payload are listed in the manifest
                notfound = []
                failed = []
                if basename == "manifest":
                  for root, subdirs, files in os.walk(bag.data_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        assert fp.startswith(bag.dir+'/')
                        datap = fp[len(bag.dir)+1:]

                        if datap not in paths:
                            notfound.append(datap)
                        elif check and csfunc and csfunc(fp) != paths[datap]:
                            failed.append(datap)

                if notfound:
                    for datap in notfound[:4]:
                        out += [self._rec("2.1.3-4",
                                          "Payload file not listed in {0}: {1}"
                                          .format(mfile, datap))]
                    if len(notfound) > 4:
                        addl = len(notfound) - 3
                        out[-1] = self._rec("2.1.3-4",
                          "{0} additional payload (data/) files missing from {1}"
                                            .format(addl, mfile))
                if failed:
                    for datap in failed[:4]:
                        out += [self._err("2.1.3-5",
                        "{0}: Recorded checksum does not match payload file: {1}"
                                     .format(mfile, datap))]
                    if len(notfound) > 4:
                        addl = len(notfound) - 3
                        out[-1] = self._err("2.1.3-5",
            "{0}: Checksums don't match for {1} additional payload (data/) files"
                                       .format(mfile, addl))

        elif basename == "manifest":
            out += [self._err("2.1.3-1", "No manifest-<alg>.txt files found")]

        return out
            
    def test_baginfo(self, bag):
        out = []
        baginfof = os.path.join(bag.dir, "bag-info.txt")

        if os.path.exists(baginfof):
            out += self.check_baginfo_format(baginfof)
            baginfo = bag.get_baginfo()

            data = bag.get_baginfo()
            for fld in _fmt_tests:
                if fld in data:
                    for val in data[fld]:
                        if not _fmt_tests[fld](val):
                            if fld == "Bag-Size":
                                out += [self._warn("2.2.2-"+fld,
                  "Not recommended value format for {0}: {1}".format(fld, val))]
                            else:
                                out += [self._err("2.2.2-"+fld,
                        "Incorrect value format for {0}: {1}".format(fld, val))]

        else:
            out += [self._rec("2.2.2-1", "Recommend adding a bag-info.txt file")]

        return out

    def check_baginfo_format(self, baginfof):
        out = []

        badlines = []
        fmtre = re.compile("^[\w\-]+\s*:\s*\S.*$")
        cntre = re.compile("^\s+")
        i = 0
        with open(baginfof) as fd:
            for line in fd:
                i += 1
                if not fmtre.match(line) and (i == 1 or not cntre.match(line)):
                    badlines.append(i)

        if badlines:
            if len(badlines) > 4:
                badlines[3] = '...'
                badlines = badlines[:4]

            out += [self._err("2.2.2-2",
                              "bag-info.txt format issues found (lines {0})"
                              .format(", ".join([str(b) for b in badlines])))]

        return out

    def test_fetch_txt(self, bag):
        
        ff = os.path.join(bag.dir, "fetch.txt")
        if not os.path.exists(ff):
            return []

        FMT = "2.2.3-1"
        ICL = "2.2.3-2"
        URL = "2.2.3-3"
        errs = { FMT: [], ICL: [], URL: [] }
        i = 0
        with open(ff) as fd:
            for line in fd:
                i += 1
                parts = line.split()
                if len(parts) < 3:
                  errs[FMT].append(i)
                  continue
              
                try:
                    int(parts[1])
                except ValueError as ex:
                    errs[ICL].append(i)
                    continue

                url = urlparse(parts[0])
                if not url.scheme or not url.netloc:
                    errs[URL].append(i)

        out = []
        for err in (FMT, ICL, URL):
            if len(errs[err]) > 0:
                if len(errs[err]) > 4:
                    errs[err][3] = "..."
                s = (len(errs[err]) > 1 and "s") or ""
                errs[err] = "(line{0} {1})" \
                    .format(s, ", ".join([str(e) for e in errs[err]]))
                
        if errs[FMT]:
            out.append(self._err(FMT,  "Missing length and/or filename "+
                                 "fields " + errs[FMT]))
        if errs[ICL]:
            out.append(self._err(ICL,  "Content length (field 2) not an "+
                                 "integer " + errs[ICL]))
        if errs[URL]:
            out.append(self._err(URL,  "Missing length and/or filename "+
                                 "fields " + errs[URL]))
        return out

_emailre = re.compile("^\w[\w\.]*@(\w+\.)+\w+$")
def _fmt_email(value):
    return _emailre.match(value) is not None

_datere = re.compile("^\d\d\d\d-[01]\d-(([012]\d)|(3[01]))$")
def _fmt_date(value):
    return _datere.match(value) is not None

_bagszre = re.compile("^\s*((\d+\.?)|(\d*\.\d+)) [kMGTZ]?[bB]\s*$")
def _fmt_bagsz(value):
    return _bagszre.match(value) is not None

_bagcntre = re.compile("^[123456789]\d* of (([123456789]\d*)|\?)$")
def _fmt_bagcnt(value):
    return _bagcntre.match(value) is not None

_oxumre = re.compile("^\d+\.\d+$")
def _fmt_oxum(value):
    return _oxumre.match(value) is not None

_fmt_tests = {
    "Bag-Size": _fmt_bagsz,
    "Payload-Oxum": _fmt_oxum,
    "Bag-Count": _fmt_bagcnt,
    "Contact-Email": _fmt_email,
    "Bagging-Date": _fmt_date
}

