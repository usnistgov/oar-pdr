"""
script to merge new collection metadata into a member's annot.json file
"""
import os, sys, json, re
import traceback as tb
from collections import OrderedDict

from nistoar.pdr.utils import read_nerd, NERDError, write_json
from nistoar.pdr.preserv.bagger.midas3 import _midadid_to_dirname as midas2recno

from . import *

TAXON_SCHEME = {
    "nist":        "https://data.nist.gov/od/dm/nist-themes/v1.1",
    "additiveman": "https://data.nist.gov/od/dm/nist-themes-additivemanufacturing/v1.0",
    "forensics":   "https://data.nist.gov/od/dm/nist-themes-forensics/v1.0",
    "chipsmetis":  "https://data.nist.gov/od/dm/nist-themes-chipsmetrology/v2.0"
}
_taxon_version_path_re = re.compile(r"/v\d+\.\d+[^/\s]*$")
DEF_METADATABAG_DIR = "/oar/data/pdr/mdbags"

logstrm = sys.stderr

def base_schema(schemauri):
    """
    return the base schema URI for the given schema URI by dropping its version field.
    """
    return _taxon_version_path_re.sub('/', schemauri)

def merge_coll_md(newnerdf, topicscheme, id=None, destf=None, bagparent=None):
    """
    merge the collection-related metadata found in the given NERDm into the publication's 
    annotation data.  Specifically, it will merge the ``isPartOf`` property as well as 
    the topic tag metadata that correspond to the specified schema
    :param str newnerdf:  the path to the new NERDm metadata for the publication that 
                          contains the collection metadata to merge.
    :param str topicscheme:  the URI (or URI label) for the topic schema whose term tags 
                          we need to capture and merge.  
    :param str id:  the AIP ID for the publication being revised; if not given, this is
                    taken from the ``newnerdf`` parameter
    :param str destf:  the path to the file to write the merged data to.  If the file exists,
                    the metadata found there will be the basis for the merge; otherwise,
                    the basis will be taken from the established metadata bag for the 
                    revision.  If not provided, the metadata bag's annot.json file will be 
                    assumed.
    """
    if not os.path.isfile(newnerdf):
        raise FatalError("%s: not a found as a file" % newnerdf)

    if topicscheme in TAXON_SCHEME:
        topicscheme = TAXON_SCHEME[topicscheme]
    basescheme = base_schema(topicscheme)

    nerd = read_nerd(newnerdf)   # may raise NERDError
    if not id:
        id = nerd.get('@id')
    if not id:
        raise FatalError("%s: @id not included; must be provided" % newnerdf)
    aipid = re.sub(r'^ark:/\d+/', '', id)

    if not nerd.get('isPartOf'):
        raise FatalError("%s: Updated NERDm file is missing isPartOf" % aipid)
    if any([not c.get('@id') for c in nerd['isPartOf']]):
        raise FatalError("%s: 'isPartOf' element(s) missing '@id' property" % newnerdf)

#    if not outf:
#        recno = midas2recno(id)
#        outf = "%sannot.json" % recno

    def mdbag_annot_file(bagp, aipid):
        if not bagp:
            bagp = DEF_METADATABAG_DIR
        if not os.path.isdir(bagp):
            raise FatalError("%s: does not exist as a directory")
        bagdir = os.path.join(bagp, aipid)
        if not os.path.isdir(bagdir):
            raise FatalError("%s: metadata bag not established, yet" % aipid)
        annotf = os.path.join(bagdir, 'metadata', 'annot.json')
        if not os.path.isfile(annotf):
            raise FatalError("%s: can't find annot.json" % aipid)
        return annotf

    if not destf:
        destf = mdbag_annot_file(bagparent, aipid)

    inf = destf
    if not os.path.isfile(inf):
        if os.path.exists(inf):
            raise FatalError("%s: exists but it not a file!" % destf)
        inf = mdbag_annot_file(bagparent, aipid)

    annot = read_nerd(inf)   # may raise NERDError

    # copy over the collection membership data
    outcolls = annot.setdefault('isPartOf', [])
    for newcoll in nerd['isPartOf']:
        matched = [ i for i in enumerate(outcolls)
                      if outcolls[i].get('@id') == newcoll.get('@id') ]
        if matched:
            if len(matched) > 0:
                raise FatalError("%s: existing has multiple parent collections with id=%s" %
                                 (inf, str(newcoll.get('@id'))))
            outcolls[matched[0]] = newcoll
        else:
            outcolls.append(newcoll)

    # copy over the related topic terms
    outtops = annot.setdefault('topic', [])
    for newtopic in nerd['topic']:
        if not newtopic.get('scheme').startswith(basescheme):
            continue
        matched = [ i for i in range(len(outtops)) 
                      if outtops[i].get('scheme','').startswith(basescheme) and
                         outtops[i].get('tag','') == newtopic['tag'] ]
        if matched:
            outtops[i] = newtopic
        else:
            outtops.append(newtopic)

    # save the merged annotations
    print >> logstrm, "Saving collection metadata to", destf
    try:
        write_json(annot, destf)
    except Exception as ex:
        raise FatalError("%s: failed to write updated annot data: %s" % (outf, str(ex)))

def usage(prog=None, pkg=None):
    if not prog:
        prog = "merge_coll_md"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s NEWNERD SCHEME [ ID ] [ OUTANNOT ]" % prog

def main(args):
    if len(args) < 2:
        raise FatalError("Missing arguments", USAGE_ERROR)
    try:
        merge_coll_md(args[0], args[1], *args[2:4])
    except FatalError as ex:
        raise
    except Exception as ex:
        tb.print_exc()
        raise FatalError(str(ex))

if __name__ == "__main__":
    prog = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    try:
        main(sys.argv[1:])
    except FatalError as ex:
        carp(prog, str(ex))
        if ex.excode == USAGE_ERROR:
            print >> sys.stderr, "Usage:", usage(prog, __package__)
        sys.exit(ex.excode)

        
                    

    
    
        
    
