"""
Module for converting a NERDm record to the latest schema versions.  
"""
import re
from collections import OrderedDict
from collections import Mapping
from copy import deepcopy
from urlparse import urlparse

from . import constants as NERDM_CONST
from nistoar.nerdm import utils

_nrdpat = re.compile(r"^("+NERDM_CONST.core_schema_base+"\S+/)v\d[\w\.]*((#.*)?)$")
_oldnrdpat = re.compile(r"^https?://www.nist.gov/od/dm/nerdm-schema/")
def _schuripatfor(uribase):
    return re.compile(r"^("+uribase+")v\d[\w\.]*((#.*)?)$")

_ineditpat = re.compile(r"\+(\s+\(\w+\))?$")

__all__ = [ 'RELHIST_EXTENSION', 'VERSION_EXTENSION_RE', 'to_version_ext', 'NERDm2Latest',
            'update_to_latest_schema' ]

RELHIST_EXTENSION = "/pdr:v"
VERSION_EXTENSION_RE = re.compile(RELHIST_EXTENSION+r"/\d+(\.\d+)*$")

def to_version_ext(version):
    return RELHIST_EXTENSION + '/' + version

class NERDm2Latest(object):
    """
    a transformation engine for converting NERDm records to conform to the latest schema versions.

    The engine can be configured with additional named record "massagers" which will make additional
    changes to a record according to a named convention.  Multiple conventions can be applied; these 
    convetions massagers are applied after migrating a record to the latest schemas
    """
    _verextre = VERSION_EXTENSION_RE 

    def __init__(self, logger=None, resolver=None, massagers=None, defconv=[], defver=None, byext={}):
        """
        initialize the updater with a set of available massagers provided as a dictionary: the keys
        are names of conventions for how information should be captured in a NERDm record, and the 
        values are functions that take a NERDm record as input 
        :param Logger  logger:  the log to write messages to; if None, no messages will be written
        :param str   resolver:  the base URL for the ID resolver service.  This is used to set
                                location of versioned releases.
        :param dict massagers:  a dictionary mapping convention names to functions to be applied to
                                a NERDm record.
        :param str|list defconv: the default convention or conventions to apply.  These will be 
                                applied in the order that they are listed.  
        :param str     defver:  the default version to update to.  This value typically
                                starts with the character, "v".  All schemas not 
                                referenced by the byext parameter will be set to this
                                version.  If not provided, the version will be the 
                                latest supported version as specified by 
                                nistoar.nerdm.constants.
        :param dict     byext:  a dictionary in which provides versions on a per-
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
        self.log = logger
        if not defver:
            defver = NERDM_CONST.core_ver
        self.defver = defver
        self.byext = byext
        self._massagers = massagers
        self.resolver_baseurl = resolver
        if self.resolver_baseurl:
            self.resolver_baseurl = self.resolver_baseurl.rstrip('/') + '/'
        if defconv is None:
            defconv = []
        elif isinstance(defconv, str):
            defconv = [defconv]
        unkn = [c for c in defconv if c not in self._massagers]
        if unkn:
            raise ValueError("Undefined convention massagers: "+str(unkn))
        self._defconv = defconv

    def convert(self, nerdmd, conv=[], version=None, byext=None, inplace=False):
        """
        convert the nerdm record to conform to the latest schemas
        :param dict nerdmd:   the NERDm record to upgrade
        :param str|list conv: the names of conventions to apply to the input record, where the names
                              correspond to the names set as massagers.  If None, the default set are 
                              applied; if an empty list (default), none are applied
        :param str version:   the version to update to; this overrides the value set at construction time.  
        :param dict  byext:   a dictionary of extension versions by label; this overrides the set
                              set at construction time.
        """
        if conv is None:
            conv = self._defconv

        if not inplace:
            nerdmd = deepcopy(nerdmd)

        # update the schema references
        self.update_nerdm_schema(nerdmd, version, byext, inplace=True)

        # handle version-specific changes
        schver = utils.get_nerdm_schema_version(nerdmd)
        if utils.cmp_versions(schver, "0.5") >= 0 and \
           'versionHistory' in nerdmd and 'releaseHistory' not in nerdmd:
            # change from versionHistory to releaseHistory
            nerdmd['releaseHistory'] = self.create_release_history(nerdmd)
            del nerdmd['versionHistory']

        if utils.cmp_versions(schver, "0.1") >= 0:
            if 'references' in nerdmd:
                for i, ref in enumerate(nerdmd['references']):
                    if 'refid' in ref:
                        if '@id' not in ref:
                            ref['@id'] = ref['refid']
                        del ref['refid']
                    if not ref.get('@id'):
                        ref['@id'] = "#ref-%d" % i

        if utils.cmp_versions(schver, "0.6") >= 0:
            if 'isPartOf' in nerdmd and not isinstance(nerdmd['isPartOf'], list):
                nerdmd['isPartOf'] = [ nerdmd['isPartOf'] ]

        # now apply any massagers
        for convention in conv:
            nerdmd = messagers[convention](nerdmd)

        return nerdmd

    def create_release_history(self, nerdmd, id=None, idext=RELHIST_EXTENSION):
        """
        return a NERDm ReleaseHistory object from version history information in the given NERDm
        Resource object
        """
        if not id:
            id = nerdmd.get('@id')
        if not id:
            raise ValueError("create_release_history: id needed") 
        out = OrderedDict([("@id", id + idext), ("@type", ["nrdr:ReleaseHistory"])])
        out['hasRelease'] = nerdmd.get("versionHistory", [])

        if len(out['hasRelease']) == 0:
            out['hasRelease'].append(self.create_release_ref(nerdmd))

        return out

    def create_release_ref_for(self, version, baseid=None):
        """
        create a bare-bones release reference object for a given base ID and version.  This 
        implementation reflects PDR-specific conventions for IDs and ID resolution.
        :param str version:  the version to create the reference object for
        :param str  baseid:  the base PDR identifier (i.e. not version-specific) 
        """
        out = OrderedDict([ ('version', version) ])
        if baseid:
            verid = baseid.rstrip('/')
            if not self._verextre.search(verid):
                verid += to_version_ext(version)
            out['@id'] = verid
        
            if self.resolver_baseurl:
                out['location'] = self.resolver_baseurl + verid

        v = version.split('.')
        for i in range(len(v), 3):
            v.append('0')
        if len(v) == 3:
            if v[2] != '0':
                out['description'] = "metadata update"
            elif v[1] != '0':
                out['description'] = "data update"
            elif v[0] == '1':
                out['description'] = "initial release"
        
        return out

    def create_release_ref(self, nerdm, defver="1.0.0"):
        """
        create a NERDm Release object (a reference to a versioned release of a reousrce) for the 
        given NERDm Resource.
        :param dict nerdm:   the NERDm Resource record to create a Release for
        :param str devver:   the default version to assume if the given Resource does not have a 
                               version property set
        :rtype: OrderedDict
        :return: the Release object refering to the nerdm input
        """
        version = _ineditpat.sub('', nerdm.get('version', defver))
        out = self.create_release_ref_for(version, nerdm.get('@id'))
        
        issued = None
        for prop in "annotated revised issued modified".split(): 
            issued = nerdm.get(prop)
            if issued:
                break

        if issued:
            out['issued'] = issued
        if not out.get('location') and nerdm.get('landingPage'):
            out['location'] = nerdm.get('landingPage')

        return out

    def update_nerdm_schema(self, nerdmd, version=None, byext=None, inplace=False):
        """
        return a converted version of the input record that is updated to the latest (or specified)
        versions of the NERDm schema.  The "_schema" property of the output record will reflect
        the requested schema, and all "_extensionSchemas" properties will found and updated.  
        :param dict  nerdmd:  the input NERDm record to convert
        :param str  version:  the default version to update to; this overrides the value set at 
                              construction time.  
        :param dict   byext:  a dictionary of extension versions by label; this overrides the set
                              set at construction time.
        :param inplace bool:  if True, the input record will be edited directly; otherwise, the 
                              input record will not be changed.
        :return:  the converted record
        """
        # detect the metatag character and do an initial sanity check on the input
        # metadata record
        mtc = utils.meta_prop_ch(nerdmd)

        defver = version
        if not version:
            defver = self.defver

        # prep the byext map
        if byext is None:
            byext = self.byext
        byext = dict(byext)
        if "pub" not in byext:
            byext["pub"] = version or NERDM_CONST.pub_ver
        if "bib" not in byext:
            byext["bib"] = version or NERDM_CONST.bib_ver
        if "rls" not in byext:
            byext["rls"] = version or NERDM_CONST.rls_ver
        if "exp" not in byext:
            byext["exp"] = version or NERDM_CONST.exp_ver
        if "sip" not in byext:
            byext["sip"] = version or NERDM_CONST.sip_ver
        if "agg" not in byext:
            byext["agg"] = version or NERDM_CONST.agg_ver
        if "" not in byext:
            byext[""] = defver

        matchrs = {}
        for ext in byext:
            uribase = ext
            parsed = urlparse(ext)
            if not parsed.scheme:
                uribase = NERDM_CONST.core_schema_base+ext
                if ext:
                    uribase += "/"
            matchrs[ _schuripatfor(uribase) ] = byext[ext]

        if not inplace:
            nerdmd = deepcopy(nerdmd)

        # update the core schema
        updated = self._upd_schema_ver(nerdmd[mtc+"schema"], matchrs, defver)
        if updated:
            nerdmd[mtc+"schema"] = updated
        self._upd_schema_ver_on_node(nerdmd, mtc+"extensionSchemas", matchrs, defver)

        # correct to start using bib extension if needed
        _dcreftype_re = re.compile("#/definitions/DCiteDocumentRef")
        if any(mtc+"extensionSchemas" in r for r in nerdmd.get('references',[])):
            for ref in nerdmd['references']:
                for i, ext in enumerate(ref.get(mtc+"extensionSchemas", [])):
                    if ext.startswith(NERDM_CONST.core_schema_base+"v") and '#/definitions/DCite' in ext:
                        ref[mtc+"extensionSchemas"][i] = _dcreftype_re.sub("#/definitions/DCiteRef",
                                                                           ref[mtc+"extensionSchemas"][i])
                        ext = ref[mtc+"extensionSchemas"][i]
                        ref[mtc+"extensionSchemas"][i] = NERDM_CONST.core_schema_base+"bib/" + byext['bib'] + \
                                                         ext[ext.index('#'):]

        return nerdmd

    def _upd_schema_ver_on_node(self, node, schprop, byext, defver):
        # node - a JSON node to examine
        # schprop - the property, e.g. "_extensionSchemas" or "_schema" to examime
        # byext - uri-re to new version map
        # defurire - defurire to check in lieu of a match in byext
        # defver - default version to update URIs matching defurire
        if schprop in node:
            if isinstance(node[schprop], (list, tuple)):
                for i in range(len(node[schprop])):
                    updated = self._upd_schema_ver(node[schprop][i], byext, defver)
                    if updated:
                        node[schprop][i] = updated
            else:
                updated = self._upd_schema_ver(node[schprop], byext, defver)
                if updated:
                    node[schprop] = updated

        for prop in node:
            if isinstance(node[prop], Mapping):
                self._upd_schema_ver_on_node(node[prop], schprop, byext, defver)
            elif isinstance(node[prop], (list, tuple)):
                self._upd_schema_ver_on_array(node[prop], schprop, byext, defver)

    def _upd_schema_ver_on_array(self, array, schprop, byext, defver):
        for el in array:
            if isinstance(el, Mapping):
                self._upd_schema_ver_on_node(el, schprop, byext, defver)
            elif isinstance(el, (list, tuple)):
                self._upd_schema_ver_on_array(el, schprop, byext, defver)

    def _upd_schema_ver(self, schuri, byext, defver):
        schuri = _oldnrdpat.sub(NERDM_CONST.core_schema_base, schuri)
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
        

def update_nerdm_schema(nerdmd, version=None, byext={}):
    """
    update the given NERDm record to the latest (or specified) version
    of the NERDm schemas.  This will update the "_schema" property of the 
    given JSON record to reflect the requested schema.  In addition, all 
    "_extensionSchemas" properties will found and references to any version
    of a NERDm schema will be updated to requested version.  Note that the 
    input record will be changed in-place.

    :param dict  nerdmd:  the NERDm record
    :param str  version:  the default version to update to.  This value typically
                          starts with the character, "v".  All schemas not 
                          referenced by the byext parameter will be set to this
                          version.  If not provided, the version will be the 
                          latest supported version as specified by 
                          nistoar.nerdm.const.core_ver.
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
    return NERDm2Latest().update_nerdm_schema(nerdmd, version=version, byext=byext, inplace=True)

def update_to_latest_schema(nerdmd, inplace=True):
    """
    update the given NERDm record to the latest versions of the NERDm schemas, transforming the 
    data for compliance.
    """
    return NERDm2Latest().convert(nerdmd, inplace=inplace)

