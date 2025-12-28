"""
script to increment a NERDm record's version as well as update and repair the release
history.  
"""
import os, sys, json, re
import traceback as tb
from collections import OrderedDict

from nistoar.pdr.utils import read_nerd, NERDError, write_json
from nistoar.pdr.publish.cmd.setver import increment_version
from nistoar.pdr.preserv.bagit.bag import NISTBag

from . import *
from ..utils import latest
from ..utils.versions import OARVersion

old_relhist_ext = re.compile("\.rel$")
RESOLVER_URL = "https://data.nist.gov/od/id/"

def apply_fix(bagdir):
    """
    fix the release history in the metadata found in a given metadata bag
    """
    bag = NISTBag(bagdir)
    nerd = bag.nerd_metadata_for("")
    id = nerd.get('@id')
    if not id:
        raise FatalError("%s: NERDm metadata missing @id" % os.path.basename(bagdir))
    try:
        annot = bag.annotations_metadata_for("")
    except Exception as ex:
        raise FatalError("Failed to read annot.json: "+str(ex), 3)

    if annot.get('versionHistory') or hist_not_up_to_date(annot.get('releaseHistory')):
        try:
            fix_release_history(annot, id)
        except Exception as ex:
            FatalError("Failed to successfullly revise annot.json: "+str(ex), 2)

        try:
            write_json(annot, bag.annotations_file_for(''))
        except Exception as ex:
            raise FatalError("Failed to write out revised annot.json: "+str(ex), 3)

def hist_not_up_to_date(relhist):
    """
    return True if there is an indication that the releast history needs an update
    """
    if not relhist or not relhist.get('@id').endswith(latest.RELHIST_EXTENSION) or \
       not relhist.get('hasRelease'):
        return True
    return any(latest.RELHIST_EXTENSION not in r.get('@id','') for r in relhist['hasRelease'])

def fix_release_history(nerd, id=None):
    """
    migrate the release history to the latest style
    """
    if not id:
        id = nerd.get('@id')
    if not id:
        raise RuntimeError("fix_release_history: Don't know record's @id")
    
    cvt = latest.NERDm2Latest(resolver=RESOLVER_URL)
    if not nerd.get('releaseHistory'):
        nerd['releaseHistory'] = cvt.create_release_history(nerd, id)
    ensure_relhist_id(nerd['releaseHistory'], id)

    more = []
    if 'versionHistory' in nerd:
        rhvers = [r.get('version') for r in nerd.get('releaseHistory',{}).get('hasRelease',[])]
        for ref in nerd['versionHistory']:
            ver = ref.get('version')
            if ver and ver not in more and ver not in rhvers:
                more.append(ref)
    if more:
        nerd['releaseHistory']['hasRelease'] = more + nerd['releaseHistory']['hasRelease']
        nerd['releaseHistory']['hasRelease'].sort(key=lambda r: OARVersion(r.get('version','0')))
    if 'versionHistory' in nerd:
        del nerd['versionHistory']

    for ref in nerd.get('releaseHistory',{}).get('hasRelease', []):
        fix_release_ref(ref, id)

def ensure_relhist_id(relhist, id):
    """
    make sure the release history object has a proper "@id" property
    """
    if not relhist.get('@id'):
        relhist['@id'] = id + latest.RELHIST_EXTENSION

    elif old_relhist_ext.search(relhist['@id']):
        relhist['@id'] = old_relhist_ext.sub(latest.RELHIST_EXTENSION, relhist['@id'])

def fix_release_ref(relref, id, resolver=RESOLVER_URL):
    """
    update a release reference object to the latest data conventions
    """
    version = relref.get('version')
    if not version:
        raise RuntimeError("Release ref missing version (id: %s)" % relref.get('@id', '?'))
    if not relref.get('@id') or latest.RELHIST_EXTENSION not in relref['@id']:
        relref['@id'] = id + latest.RELHIST_EXTENSION + '/' + version

    if not relref.get('location') or latest.RELHIST_EXTENSION not in relref['location']:
        relref['location'] = resolver + relref['@id']

def usage(prog=None, pkg=None):
    if not prog:
        prog = "fix_history"
    if pkg:
        prog = "python -m %s.%s" % (pkg, prog)
    return "%s BAGDIR" % prog

def main(args):
    if len(args) < 1:
        raise FatalError("Missing BAGDIR argument", USAGE_ERROR)
    try:
        apply_fix(args[0])
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


    
    

    
        
    
    
