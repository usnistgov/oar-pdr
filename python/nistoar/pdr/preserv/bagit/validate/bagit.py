"""
This module implements a validator for the base BagIt standard
"""
import os, re
from collections import OrderedDict
from urlparse import urlparse

from .base import (Validator, ValidatorBase, ALL, ValidationResults,
                   ERROR, WARN, REC, ALL, PROB)
from ..bag import NISTBag
from ....utils import checksum_of

csfunctions = {
    "sha256":  checksum_of
}

class BagItValidator(ValidatorBase):
    """
    A validator that runs tests for compliance to the base BagIt standard
    """
    profile = ("BagIt", "v0.97")

    def __init__(self, config=None):
        super(BagItValidator, self).__init__(config)

    def test_bagit_txt(self, bag, want=ALL, results=None):
        """
        test that the bagit.txt file exists and has the required contents
        """
        out = results
        if not out:
            out = ValidationResults(bag.name, want)
        bagitf = os.path.join(bag.dir, "bagit.txt")

        t = self._issue("2.1.1-1", "Bag must contain a bag-info.txt file")
        out._err(t, os.path.exists(bagitf))
        if t.failed():
            return out
        
        baginfo = bag.get_baginfo(bagitf)
        t = self._issue("2.1.1-2",
                        "bagit.txt must contain element: BagIt-Version")
        out._err(t, 'BagIt-Version' in baginfo)

        if t.passed():
            t = self._issue("2.1.1-3",
                            "bagit.txt: BagIt-Version must be set to {0}"
                            .format(self.profile[1]))
            out._err(t, baginfo['BagIt-Version'] == ["0.97"])

        t = self._issue("2.1.1-4",
                  "bagit.txt must contain element: Tag-File-Character-Encoding")
        out._err(t, 'Tag-File-Character-Encoding' in baginfo)

        if t.passed():
            t = self._issue("2.1.1-5",
                "bagit.txt: Tag-File-Character-Encoding must be set to 'UTF-8'")
            out._err(t, baginfo['Tag-File-Character-Encoding'] == ["UTF-8"])

        t = self._issue("2.1.1-6", "bagit.txt: recommend using this " +
                                   "element order: BagIt-Version, " +
                                   "Tag-File-Character-Encoding")
        out._rec(t, baginfo.keys() == ["BagIt-Version",
                                        "Tag-File-Character-Encoding"])
        return out

    def test_data_dir(self, bag, want=ALL, results=None):
        """
        test that the data directory exists
        """
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        t = self._issue("2.1.2", "Bag must contain payload directory, data/")
        out._err(t, os.path.exists(os.path.join(bag.dir, "data")))

        return out

    def test_manifest(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        tcfg = self.cfg.get("test_manifest", {})
        check = tcfg.get('check_checksums', True)
        return self._test_manifest(bag, "manifest", check, out, want)

    def test_tagmanifest(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)

        tcfg = self.cfg.get("test_manifest", {})
        check = tcfg.get('check_checksums', True)
        return self._test_manifest(bag, "tagmanifest", check, out, want)

    def _test_manifest(self, bag, basename, check, out, want=ALL):
        manire = re.compile(r'^{0}-(\w+).txt$'.format(basename))
        manifests = [f for f in os.listdir(bag.dir) if manire.match(f)]

        if basename == "manifest":
            t = self._issue("2.1.3-1", "Bag requires at least one "+
                            "manifest-<alg>.txt file")
            out._err(t, len(manifests) > 0)
            if t.failed():
                return out

        delimre = re.compile(r'[ \t]+')
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
                    parts = delimre.split(line.rstrip('\n'), 1)
                    if len(parts) != 2:
                        badlines.append(i)
                        continue
                    if parts[1].startswith('*'):
                        parts[1] = parts[1][1:]
                        parts.append('*')

                    if basename == "manifest" and \
                       not parts[1].startswith('data/'):
                        notdata.append((i, parts[1]))
                    else:
                        paths[parts[1]] = parts[0]

            t = self._issue("2.1.3-2",
                            "Manifest file lines must match format "+
                            "CHECKSUM FILENAME")
            comms = None
            if badlines:
                if len(badlines) > 4:
                    badlines[3] = "..."
                    badlines = badlines[:4]
                s = (len(badlines) > 1 and "s") or ""
                comms = "{0}: line{1} {2}" \
                        .format(mfile, s, ", ".join([str(b) for b in badlines]))
            out._err(t, len(badlines) == 0, comms)

            t = self._issue("2.1.3-3",
                            "manifest-<alg>.txt file lists only payload files")
            comms = None
            if notdata:
                s = (len(notdata) > 1 and "s") or ""
                if len(notdata) > 4:
                    notdata[3] = ("...", notdata[3][1])
                comms = ["{0}: line{1} {2}" 
                  .format(mfile, s, ", ".join([str(n[0]) for n in notdata[:4]]))]
                comms.extend( [n[1] for n in notdata] )
            out._err(t, len(notdata) == 0, comms)

            # make sure all paths exist
            missing = []
            notafile = []
            for datap in paths:
                fp = os.path.join(bag.dir, datap)
                if not os.path.exists(fp):
                    missing.append(datap)
                elif not os.path.isfile(fp):
                    notafile.append(datap)

            t = self._issue("2.1.3-7", "Manifest must list only files")
            comm = None
            if len(notafile) > 0:
                s = (len(notafile) > 1 and "s") or ""
                comm = ["{0} non-file{1} listed in {2}"
                        .format(len(notafile), s, mfile)]
                comm += notafile
            out._err(t, len(notafile) == 0, comm)

            t = self._issue("3-1-2",
                            "Bag must contain all files listed in manifest")
            comm = None
            if len(missing) > 0:
                s = (len(missing) > 1 and "s") or ""
                comm = ["{0} missing file{1} from {2}"
                        .format(len(missing), s, mfile)]
                comm += missing
            out._err(t, len(missing) == 0, comm)

            # check that all files in the payload are listed in the manifest
            notfound = []
            failed = []
            if check or basename == "manifest":
              top = (basename == "manifest" and bag.data_dir) or bag.dir
              for root, subdirs, files in os.walk(top):
                for f in files:
                    fp = os.path.join(root, f)
                    assert fp.startswith(bag.dir+'/')
                    datap = fp[len(bag.dir)+1:]

                    if datap not in paths:
                        if basename == "manifest":
                            notfound.append(datap)
                    elif check and csfunc and csfunc(fp) != paths[datap]:
                        failed.append(datap)

            t = self._issue("2.1.3-4",
                     "All payload files must be listed in at least one manifest")
            comm = None
            if len(notfound) > 0:
                s = (len(notfound) > 1 and "s") or ""
                comm = ["{0} payload file{1} not listed in {2}"
                        .format(len(notfound), s, mfile)]
                comm += notfound
            out._rec(t, len(notfound) == 0, comm)

            t = self._issue("3-2-2", "Every checksum must be verifiable")
            if len(failed) > 0:
                s = (len(failed) > 1 and "s") or ""
                es = (len(failed) == 1 and "es") or ""
                comm = ["{0} recorded checksum{1} in {2} do{3} not verify against file"
                       .format(len(failed), s, mfile, es)]
                comm += failed
            out._err(t, len(failed) == 0, comm)

        return out
            
    def test_baginfo(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)
        baginfof = os.path.join(bag.dir, "bag-info.txt")

        t = self._issue("2.2.2-1", "A bag should include a bag-info.txt file")
        out._rec(t, os.path.exists(baginfof))
        if t.failed():
            return out
        
        self.check_baginfo_format(baginfof, out)
        data = bag.get_baginfo()
        for fld in _fmt_tests:
            if fld in data:
                badvals = []
                t = self._issue("2.2.2-"+fld,
                                "{0} value should match format, {1}"
                                .format(fld, _fmt_tests[fld][0]))
                for val in data[fld]:
                    if not _fmt_tests[fld][1](val):
                        badvals.append(val)

                comm = None
                if len(badvals) > 0:
                    comm = list(badvals)
                if fld == "Bag-Size":
                    out._rec(t, len(badvals) == 0, comm)
                else:
                    out._err(t, len(badvals) == 0, comm)

        return out

    def check_baginfo_format(self, baginfof, results):
        out = results

        badlines = []
        fmtre = re.compile("^[\w\-]+\s*:(\s*\S.*)?$")
        cntre = re.compile("^\s+")
        i = 0
        with open(baginfof) as fd:
            for line in fd:
                i += 1
                if not fmtre.match(line) and (i == 1 or not cntre.match(line)):
                    badlines.append(i)

        t = self._issue("2.2.2-2","bag-info.txt lines must match "+
                        "label-colon-value format")
        comm = None
        if badlines:
            s = (len(badlines) > 1 and "s") or ""
            if len(badlines) > 4:
                badlines[3] = '...'
                badlines = badlines[:4]
            comm = "line{0} {1}".format(s, ", ".join([str(b) for b in badlines]))
        out._err(t, len(badlines) == 0, comm)

        return out

    def test_fetch_txt(self, bag, want=ALL, results=None):
        out = results
        if not out:
            out = ValidationResults(bag.name, want)
        
        ff = os.path.join(bag.dir, "fetch.txt")
        if not os.path.exists(ff):
            return out

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

        for err in (FMT, ICL, URL):
            if len(errs[err]) > 0:
                if len(errs[err]) > 4:
                    errs[err][3] = "..."
                s = (len(errs[err]) > 1 and "s") or ""
                errs[err] = "Malformed: line{0} {1})" \
                    .format(s, ", ".join([str(e) for e in errs[err]]))

        t = self._issue(FMT,
                        "fetch.txt lines must match format URL LENGTH FILENAME")
        out._err(t, not bool(errs[FMT]), errs[FMT])

        t = self._issue(ICL,  "Content length (field 2) must be an integer")
        out._err(t, not bool(errs[ICL]), errs[ICL])

        t = self._issue(URL,  "First field must be a URL")
        out._err(t, not bool(errs[URL]), errs[URL])

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
    "Bag-Size": ("D.D Xb", _fmt_bagsz),
    "Payload-Oxum": ("NNN.NNN", _fmt_oxum),
    "Bag-Count": ("N of N", _fmt_bagcnt),
    "Contact-Email": ("NAME@NETADDR", _fmt_email),
    "Bagging-Date": ("YYYY-MM-DD", _fmt_date)
}

