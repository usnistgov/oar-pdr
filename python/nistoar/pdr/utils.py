"""
Utility functions useful across the pdr package
"""
from collections import OrderedDict, Mapping
import hashlib, json, re, shutil, os, time

from .exceptions import (NERDError, PODError, StateException)

def read_nerd(nerdfile):
    """
    read the JSON-formatted NERDm metadata in the given file

    :return OrderedDict:  the dictionary containing the data
    """
    try:
        with open(nerdfile) as fd:
            return json.load(fd, object_pairs_hook=OrderedDict)
    except ValueError, ex:
        raise NERDError("Unable to parse NERD file, " + nerdfile + ": "+str(ex),
                       cause=ex, src=nerdfile)
    except IOError, ex:
        raise NERDError("Unable to read NERD file, " + nerdfile + ": "+str(ex),
                        cause=ex, src=nerdfile)

def read_pod(podfile):
    """
    read the JSON-formatted POD metadata in the given file

    :return OrderedDict:  the dictionary containing the data
    """
    try:
        with open(podfile) as fd:
            return json.load(fd, object_pairs_hook=OrderedDict)
    except ValueError, ex:
        raise PODError("Unable to parse POD file, " + podfile + ": "+str(ex),
                       cause=ex, src=podfile)
    except IOError, ex:
        raise PODError("Unable to read POD file, " + podfile + ": "+str(ex),
                       cause=ex, src=podfile)

def write_json(jsdata, destfile, indent=4):
    """
    write out the given JSON data into a file with pretty print formatting
    """
    try:
        with open(destfile, 'w') as fd:
            json.dump(jsdata, fd, indent=indent, separators=(',', ': '))
    except Exception, ex:
        raise StateException("{0}: Failed to write JSON data to file: {1}"
                             .format(destfile, str(ex)), cause=ex)

def_ext2mime = {
    "html": "text/html",
    "txt":  "text/plain",
    "xml":  "text/xml",
    "json": "application/json"
}

def update_mimetypes_from_file(map, filepath):
    """
    load the MIME-type mappings from the given file into the given dictionary 
    mapping extensions to MIME-type values.  The file can have either an nginx
    configuration format or the common format (i.e. used by Apache).  
    """
    if map is None:
        map = {}
    if not isinstance(map, Mapping):
        raise ValueError("map argument is not dictionary-like: "+ str(type(map)))

    commline = re.compile(r'^\s*#')
    nginx_fmt_start = re.compile(r'^\s*types\s+{')
    nginx_fmt_end = re.compile(r'^\s*}')
    with open(filepath) as fd:
        line = '#'
        while line and (line.strip() == '' or commline.search(line)):
            line = fd.readline()

        if line:
            line = line.strip()
            if nginx_fmt_start.search(line):
                # nginx format
                line = fd.readline()
                while line:
                    if nginx_fmt_end.search(line):
                        break
                    line = line.strip()
                    if line and not commline.search(line):
                        words = line.rstrip(';').split()
                        if len(words) > 1:
                            for ext in words[1:]:
                                map[ext] = words[0]
                    line = fd.readline()

            else:
                # common server format
                while line:
                    if commline.search(line):
                        continue
                    words = line.strip().split()
                    if len(words) > 1:
                        for ext in words[1:]:
                            map[ext] = words[0]
                    line = fd.readline()

    return map

def build_mime_type_map(filelist):
    """
    return a dictionary mapping filename extensions to MIME-types, given an 
    ordered list of files defining mappings.  Entries in files appearing later 
    in the list can override those in the earlier ones.  Files can be in either 
    the nginx configuration format or the common format (i.e. used by Apache).  

    :param filelist array:  a list of filepaths defining the MIME-types to
                            extensions mappings.
    """
    out = def_ext2mime.copy()
    for file in filelist:
        update_mimetypes_from_file(out, file)
    return out


def checksum_of(filepath):
    """
    return the checksum for the given file
    """
    bfsz = 10240000   # 10 MB buffer
    sum = hashlib.sha256()
    with open(filepath) as fd:
        while True:
            buf = fd.read(bfsz)
            if not buf: break
            sum.update(buf)
    return sum.hexdigest()

def rmtree(rootdir, retries=1):
    """
    an implementation of rmtree that is intended to work on NSF-mounted 
    directories where shutil.rmtree can often fail.
    """
    if not os.path.exists(rootdir):
        return
    if not os.path.isdir(rootdir):
        os.remove(rootdir)
        return
    
    for root,subdirs,files in os.walk(rootdir, topdown=False):
        try:
            shutil.rmtree(root)
        except OSError as ex:
            if retries <= 0:
                raise
            # wait a little for NFS to catch up
            time.sleep(0.25)
            rmtree(root, retries=retries-1)
    
