"""
This module provides functions and classes that encapsulate policies and 
conventions for preservation bags and the bagging process which can span 
across multiple bagger and SIP types.  In particular, it provides functions
that understand the NIST conventions for naming preservation bags.  

Note that this modules captures much of the same knowledge and functionality
implemented in the BagUtils Java class (from the 
gov.nist.oar.bags.preservation.bags package provided by the oar-dist-service
repository).  
"""
import os, re
from collections import Sequence, Mapping
from urlparse import urlparse
from copy import deepcopy

from ..bagit.builder import (NERDM_SCH_ID_BASE, NERDM_SCH_VER, NERDMPUB_SCH_VER,
                             NERDMBIB_SCH_ID_BASE, NERDMBIB_SCH_VER)

DEF_MBAG_VERSION = "0.4"
DEF_NIST_PROF_VERSION = "0.4"

def form_bag_name(aipid, bagseq=0, dsver="1.0", mbver=DEF_MBAG_VERSION,
                  namefmt=None):
    """
    return name for a bag directory that reflects the convention of the NIST
    BagIt Profile.  According to the Profile, preservation bag names follow 
    the format, AIPID.AIPVER.mbagMBVER-SEQ.  

    :param str   aipid:  the AIP identifier for the dataset
    :param int  bagseq:  the multibag sequence number to assign (default: 0)
    :param str   dsver:  the dataset's release version string.  (default: 1.0)
    :param str   mbver:  the version of the multibag profile the bag 
                           (purportedly) complies to (default:  the value
                           of DEF_MBAG_VERSION, 0.4)
    :param str namefmt:  an arbitrary formatting string for forming the string.
                           Note that by providing this parameter, the caller
                           overrides the NIST convention.  This formatting 
                           string should follow the format used by the 
                           str.format() function, using the the parameter 
                           names from this method as placeholders (e.g. 
                           "{aipid}"
    """
    if not namefmt:
        namefmt = "{aipid}.{dsver}.mbag{mbver}-{bagseq}"

    if not mbver:
        mbver = DEF_MBAG_VERSION
    mbver = re.sub(r'\.', '_', mbver)
    dsver = re.sub(r'\.', '_', dsver)
    
    return namefmt.format(aipid=aipid, dsver=dsver, mbver=mbver,
                          bagseq=str(bagseq))

def form_bag_name03(aipid, bagseq=0, mbver="0.3"):
    """
    return name for a bag directory that reflects the convention of the NIST
    BagIt Profile, versions 0.3 and earlier.  According to these deprecated 
    versions, preservation bag names follow the format, 
    AIPID.mbagMBVER-SEQ.  

    :param str   aipid:  the AIP identifier for the dataset
    :param int  bagseq:  the multibag sequence number to assign (default: 0)
    :param str   mbver:  the version of the multibag profile the bag 
                           (purportedly) complies to (default:  the value
                           of DEF_MBAG_VERSION, 0.4)
    """
    return form_bag_name(aipid, bagseq, "", mbver,
                         "{aipid}.mbag{mbver}-{bagseq}")

BAGNAME04_RE = re.compile(r"^(\w[\w\-]*)\.(\d+(_\d+)*)\.mbag(\d+_\d+)-(\d+)(\..*)?$")
BAGNAME02_RE = re.compile(r"^(\w[\w\-]*)\.mbag(\d+_\d+)-(\d+)(\..*)?$")
BAGNAME_RE = BAGNAME04_RE

def parse_bag_name(bagname, nistprof=None):
    """
    parse a bag name into its meaningful components: 
    id, version, multibag profile version, multibag sequence number, and 
    serialization extension (if present).  The version fields will be exactly 
    as they appear in the name (i.e. with underscore, _, as the delimiter).  
    :param str bagname:  the name to parse.  
    :param str nistprof: the version of the NIST BagIt profile that the name
                         must comply with; if None, it will be compared against
                         all recognized conventions.  
    :return list of str:  a list containing the components in order of id, 
                       version, multibag profile version, multibag sequence 
                       number, and serialization extension.  If the name does 
                       not contain a version or serialization extension, the 
                       second or fourth element, respectively, will be an 
                       empty string.  The extension field will not include a 
                       leading dot.  
    :raises ValueError:  if the input name does not follow a recognized 
                       naming convention or nistprof is not recognized as a 
                       profile version.
    """
    if nistprof:
        if not Version.is_proper_version(nistprof):
            raise ValueError("parseBagName(): nistprof: not a version: " +
                             nistprof)
        pver = Version(nistprof)
        if pver <= "0.3":
            return parse_bag_name_02(bagname, nistprof)

        return parse_bag_name_04(bagname, nistprof)

    try:
        return parse_bag_name_04(bagname)
    except ValueError as ex:
        pass

    try:
        return parse_bag_name_02(bagname)
    except ValueError as ex:
        raise ValueError("Not recognized as a NIST bag bagname: "+bagname)

def parse_bag_name_02(name, nistprof="0.2"):
    """
    parse a bag name into its parts according to convention specified in the 
    NIST BagIt Profile, versions 0.2-0.3.
    """
    m = BAGNAME02_RE.match(name)
    if m is None:
        if nistprof is None:  nistprof = "0.2"
        raise ValueError("Not recognized as a bag name according to profile "+
                         "version "+nistprof+": "+name)
    out = list(m.group(1, 2, 3, 4))
    out.insert(1, "")
    if not out[4]:
        out[4] = ''
    if out[4]:
        out[4] = out[4].lstrip(".")
    return out

def parse_bag_name_04(name, nistprof="0.4"):
    m = BAGNAME04_RE.match(name)
    if m is None:
        if nistprof is None:  nistprof = "0.4"
        raise ValueError("Not recognized as a bag name according to profile "+
                         "version "+nistprof+": "+name)
    out = list(m.group(1, 2, 4, 5, 6))
    if not out[4]:
        out[4] = ''
    if out[4]:
        out[4] = out[4].lstrip(".")
    return out
    
def is_legal_bag_name(name):
    """
    return True if the given name is recognized as a legal bag name according
    to the NIST Preservation profile.
    """
    for pat in (BAGNAME04_RE, BAGNAME02_RE):
        if pat.match(name):
            return True
    return False

def multibag_version_of(name):
    """
    return the version of the Multibag BagIt Profile that the bag with the 
    given name claims to be compliant with.  Return an empty string if the 
    name appears not to contain profile version string.
    """
    try:
        return re.sub(r'_', ".", parse_bag_name(name)[2])
    except ValueError as ex:
        return ''

_ver_delim = re.compile(r"[\._]")
_proper_ver = re.compile(r"^\d+([\._]\d+)*$")

class Version(object):
    """
    a version class that can facilitate comparisons
    """

    def _toint(self, field):
        try:
            return int(field)
        except ValueError:
            return field

    def __init__(self, vers):
        """
        convert a version string to a Version instance
        """
        self._vs = vers
        self.fields = [self._toint(n) for n in _ver_delim.split(self._vs)]

    def __str__(self):
        return self._vs

    def __eq__(self, other):
        if not isinstance(other, Version):
            other = Version(other)
        return self.fields == other.fields

    def __lt__(self, other):
        if not isinstance(other, Version):
            other = Version(other)
        return self.fields < other.fields

    def __le__(self, other):
        if not isinstance(other, Version):
            other = Version(other)
        return self < other or self == other

    def __ge__(self, other):
        return not (self < other)
    def __gt__(self, other):
        return not self.__le__(other)
    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def is_proper_version(cls, vers):
        """
        return true if the given version string is of the form M.M.M... where
        each M is any non-negative number.   
        """
        return _proper_ver.match(vers) is not None

def cmp_versions(ver1, ver2):
    """
    compare two version strings for their order.
    :return int:  -1 if v1 < v2, 0 if v1 = v2, and +1 if v1 > v2
    """
    a = Version(ver1)
    b = Version(ver2)
    if a < b:
        return -1
    elif a == b:
        return 0
    return +1

class BagName(object):
    """
    a wrapper class around a legal bag name that allows it to be sorted as part of 
    a list of bag names.  In particular, the constructor can be used as a key function
    passed to the sort function.  
    """
    def __init__(self, bagname):
        """
        wrap a bag name
        :raises ValueError:  if bagname is not recognized as a legal bag name
        """
        self._nm = bagname
        self.fields = parse_bag_name(bagname)

    def __str__(self):
        return self._nm

    @property
    def aipid(self):
        """
        return the AIP identifier for this preservation bag
        """
        return self.fields[0]

    @property
    def version(self):
        """
        return the version of the AIP that this bag is (originally) part of.  (It may
        also be part of later versions of the AIP.)  If the version is an empty string,
        it can be taken as version 0 or version 1.
        """
        return self.fields[1]

    @property
    def multibag_profile(self):
        """
        return the version of the Multibag BagIt Profile that this bag claims to be 
        compliant with.
        """
        return self.fields[2]

    @property
    def sequence(self):
        """
        return the sequence number for the bag
        """
        return self.fields[3]

    @property
    def serialization(self):
        """
        return the label for the serialization format used for the bag.  If an empty
        string, the name refers to the bag in its unserialized state. 
        """
        return self.fields[4]

    def __eq__(self, other):
        if not isinstance(other, BagName):
            other = BagName(other)
        return self.fields == other.fields

    def __lt__(self, other):
        if not isinstance(other, BagName):
            other = BagName(other)

        # We sort the names base on the ordering of individual fields with
        # following precendence:
        #  1. the AIP identifier (lexically)
        #  2. the bag sequence number
        #  3. the publication version
        #  4. the multibag profile version
        #  5. the serialization extension (lexically)
        # versions are sorted via the Version class

        # 1. compare AIP id
        if self.aipid < other.aipid:
            return True
        elif self.aipid != other.aipid:
            return False

        # 2. compare the multibag sequence number
        try:
            s0 = int(self.sequence)
        except ValueError as ex:
            s0 = 0
        try:
            s1 = int(other.sequence)
        except ValueError as ex:
            s1 = 0
        if s0 < s1:
            return True
        if s0 != s1:
            return False

        # 3. compare the publication version.  
        v0, v1 = [((v == "" and "0") or Version(v)) for v in (self.version, other.version)]
        if v0 < v1:
            return True
        if v0 != v1:
            return False

        # 4. compare the multibag profile version
        v0, v1 = Version(self.multibag_profile), Version(other.multibag_profile)
        if v0 < v1:
            return True
        if v0 != v1:
            return False

        # 5. finally, compare the extensions, lexically
        return self.serialization < other.serialization

    def __le__(self, other):
        if not isinstance(other, BagName):
            other = BagName(other)

        return self == other or self < other

    def __ge__(self, other):
        return not (self < other)
    def __gt__(self, other):
        return not self.__le__(other)
    def __ne__(self, other):
        return not (self == other)

def find_latest_head_bag(bagnames):
    """
    return the name of the latest head bag from a given list of bag names.  Each 
    item in the list must be a legal bag name (see is_legal_bag_name()) and have the 
    same AIP identifier.  If the former requirement is not satisfied, a ValueError
    exception is raised; if the second is not, the result is undefined. 
    :param bagnames:  the list of bag names
    :type  bagnames:  list of str
    """
    if not isinstance(bagnames, Sequence):
        raise TypeError("findLatestHeadBag(): input not a list: "+str(bagnames))
    s = sorted(bagnames, key=BagName)
    if len(s) < 1:
        raise ValueError("findLatestHeadBag(): bagnames list is empty")
    return s[-1]

def select_version(bagnames, version):
    """
    select the bags from a list of bagnames that match a desired version.  Under 
    certain circumstances, this will look for certain varients.  If none of the 
    names match the version, an empty list is returned.
    :param bagnames:  the list of bag names to select from 
    :type  bagnames:  list of str
    :param str version:  the desired version in dot-delimited form
    """
    version = re.sub(r'\.', "_", version)

    # Most likely given current NIST practice, if version is simply "0" or "1",
    # we're refering to bags following the 0.2 naming convention.
    if version == "0" or version == "1":
        out = select_version(bagnames, "")
        if len(out) > 0:
            return out

    if version == "":
        vernamere = re.compile(r"^(\w[\w\-]+)\.mbag")
        return [b for b in bagnames if vernamere.match(b)]

    out = []
    vernamere = re.compile(r"^(\w[\w\-]+)\."+version+r"\.")
    while len(version) > 0:
        for name in bagnames:
            if vernamere.match(name):
                out.append(name)
        if len(out) > 0 or not version.endswith("_0"):
            break

        # try lopping off trailing zeros
        version = version[:len(version)-2]

    return out

_nrdpat = re.compile(r"^("+NERDM_SCH_ID_BASE+"\S+/)v\d[\w\.]*((#.*)?)$")
def _schuripatfor(uribase):
    return re.compile(r"^("+uribase+")v\d[\w\.]*((#.*)?)$")

def update_nerdm_schema(nerdmd, version=None, byext={}):
    """
    update the given NERDm record to the latest (or specified) version
    of the NERDm schemas.  This will update the "_schema" property of the 
    given JSON record to reflect the requested schema.  In addition, all 
    "_extensionSchemas" properties will found and references to any version
    of a NERDm schema will be updated to requested version.  

    :param dict  nerdmd:  the NERDm record
    :param str  version:  the default version to update to.  This value typically
                          starts with the character, "v".  All schemas not 
                          referenced by the byext parameter will be set to this
                          version.  If not provided, the version will be the 
                          latest supported version as specified by 
                          nistoar.pdr.preserv.bagit.builder.NERDM_SCH_VER.
    :param dict   byext:  a dictionary in which provides versions on a per-
                          extension schema basis.  The keys represent extension 
                          schemas given either by the extension field in the 
                          standard NERDm schema URI or the entire base URL
                          for the extension schema up to the verison field.  
                          Each value gives the version of the extension schema
                          that that schema should be updated to.  An empty string
                          for the key represents the core schema, and an empty
                          string for the value means that the version for that
                          extension should not be changed.
    """
    # detect the metatag character and do an initial sanity check on the input
    # metadata record
    if "_schema" in nerdmd:
        mtc = "_"
    elif "$schema" in nerdmd:
        mtc = "$"
    else:
        raise ValueError("No _schema metatag found (is this a NERDm record?)")
        
    defver = version
    if not version:
        defver = NERDM_SCH_VER

    # prep the byext map
    if not byext:
        byext = {}
    else:
        byext = dict(byext)
    if not version and "pub" not in byext:
        byext["pub"] = NERDMPUB_SCH_VER
    if not version and "bib" not in byext:
        byext["bib"] = NERDMBIB_SCH_VER
    if "" not in byext:
        byext[""] = defver

    matchrs = {}
    for ext in byext:
        uribase = ext
        parsed = urlparse(ext)
        if not parsed.scheme:
            uribase = NERDM_SCH_ID_BASE+ext
            if ext:
                uribase += "/"
        matchrs[ _schuripatfor(uribase) ] = byext[ext]

    # update the core schema
    updated = _upd_schema_ver(nerdmd[mtc+"schema"], matchrs, defver)
    if updated:
        nerdmd[mtc+"schema"] = updated
    _upd_schema_ver_on_node(nerdmd, mtc+"extensionSchemas", matchrs, defver)

    # from v0.3: correct to use bib extension if needed
    if any(mtc+"extensionSchemas" in r for r in nerdmd.get('references',[])):
        for ref in nerdmd['references']:
            for i, ext in enumerate(ref.get(mtc+"extensionSchemas", [])):
                if ext.startswith(NERDM_SCH_ID_BASE+"v") and '#/definitions/DCite' in ext:
                    ref[mtc+"extensionSchemas"][i] = NERDMBIB_SCH_ID_BASE + byext['bib'] + \
                                                     ext[ext.index('#'):]

    # ensure the PDR-ID is the form that refers to the latest version
    nerdmd["@id"] = re.sub(r'\.v\d+(_\d+)*$','', nerdmd["@id"])

    # from v0.4: convert versionHistory to releaseHistory
    if 'versionHistory' in nerdmd:
        if 'releaseHistory' not in nerdmd:
            # update the location URLs
            for v in nerdmd['versionHistory']:
                if location in v:
                    vtag = ".v" + re.sub(r'\.','_', v['version'])
                    if not v['location'].endswith(vtag):
                        v['location'] += vtag

            nerdm['releaseHistory'] = OrderedDict([
                ("@id", nerdm["@id"]+".rel"),
                ("@type", ["nrdr:ReleaseHistory"]),
                ("hasRelease", nerdm['versionHistory'])
            ])
        del nerdmd['versionHistory']

    return nerdmd

def _upd_schema_ver_on_node(node, schprop, byext, defver):
    # node - a JSON node to examine
    # schprop - the property, e.g. "_extensionSchemas" or "_schema" to examime
    # byext - uri-re to new version map
    # defurire - defurire to check in lieu of a match in byext
    # defver - default version to update URIs matching defurire
    if schprop in node:
        if isinstance(node[schprop], (list, tuple)):
            for i in range(len(node[schprop])):
                updated = _upd_schema_ver(node[schprop][i], byext, defver)
                if updated:
                    node[schprop][i] = updated
        else:
            updated = _upd_schema_ver(node[schprop], byext, defver)
            if updated:
                node[schprop] = updated

    for prop in node:
        if isinstance(node[prop], Mapping):
            _upd_schema_ver_on_node(node[prop], schprop, byext, defver)
        elif isinstance(node[prop], (list, tuple)):
            _upd_schema_ver_on_array(node[prop], schprop, byext, defver)

def _upd_schema_ver_on_array(array, schprop, byext, defver):
    for el in array:
        if isinstance(el, Mapping):
            _upd_schema_ver_on_node(el, schprop, byext, defver)
        elif isinstance(el, (list, tuple)):
            _upd_schema_ver_on_array(el, schprop, byext, defver)

def _upd_schema_ver(schuri, byext, defver):
    for r in byext:
        match = r.search(schuri)
        if match:
            if byext[r]:
                return match.group(1)+byext[r]+match.group(2)
            else:
                return None
    match = _nrdpat.match(schuri)
    if match and defver:
        return match.group(1)+defver+match.group(2)
    return None
