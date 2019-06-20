"""
Utility functions useful across the pdr package
"""
from collections import OrderedDict, Mapping
import hashlib, json, re, shutil, os, time, subprocess, logging
try:
    import fcntl
except ImportError:
    fcntl = None

from .exceptions import (NERDError, PODError, StateException)

log = logging.getLogger("pdr.utils")
BLAB = logging.DEBUG - 1

def blab(log, msg, *args, **kwargs):
    """
    log a verbose message. This uses a log level, BLAB, that is lower than 
    DEBUG; in other words when a log's level is set to DEBUG, this message 
    will not be displayed.  This is intended for messages that would appear 
    voluminously if the level were set to BLAB. 

    :param Logger log:  the Logger object to record to
    :param str    msg:  the message to write
    :param args:        treat msg as a template and insert these values
    :param kwargs:      other arbitrary keywords to pass to log.log()
    """
    log.log(BLAB, msg, *args, **kwargs)

def read_nerd(nerdfile):
    """
    read the JSON-formatted NERDm metadata in the given file

    :return OrderedDict:  the dictionary containing the data
    """
    try:
        return read_json(nerdfile)
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
        return read_json(podfile)
    except ValueError, ex:
        raise PODError("Unable to parse POD file, " + podfile + ": "+str(ex),
                       cause=ex, src=podfile)
    except IOError, ex:
        raise PODError("Unable to read POD file, " + podfile + ": "+str(ex),
                       cause=ex, src=podfile)

def read_json(jsonfile, nolock=False):
    """
    read the JSON data from the specified file

    :param str   jsonfile:  the path to the JSON file to read.  
    :param bool  nolock:    if False (default), a shared lock will be aquired
                            before reading the file.  A True value reads the 
                            file without a lock
    :raise IOError:  if there is an error while acquiring the lock or reading 
                     the file contents
    :raise ValueError:  if JSON format errors are detected.
    """
    with open(jsonfile) as fd:
        if fcntl and not nolock:
            fcntl.lockf(fd, fcntl.LOCK_SH)
            blab(log, "Acquired shared lock for reading: "+jsonfile)
        data = fd.read()
    blab(log, "released SH")
    if not data:
        # this is an unfortunate hack multithreaded reading/writing
        time.sleep(0.02)
        with open(jsonfile) as fd:
            if fcntl and not nolock:
                fcntl.lockf(fd, fcntl.LOCK_SH)
                blab(log, "(Re)Acquired shared lock for reading: "+jsonfile)
            data = fd.read()
        blab(log, "released SH")
    return json.loads(data, object_pairs_hook=OrderedDict)

def write_json(jsdata, destfile, indent=4, nolock=False):
    """
    write out the given JSON data into a file with pretty print formatting

    :param dict jsdata:    the JSON data to write 
    :param str  destfile:  the path to the file to write the data to
    :param int  indent:    the number of characters to use for indentation
                           (default: 4).
    :param bool  nolock:   if False (default), an exclusive lock will be acquired
                           before writing to the file.  A True value writes the 
                           data without a lock
    """
    try:
        with open(destfile, 'a') as fd:
            if fcntl and not nolock:
                fcntl.lockf(fd, fcntl.LOCK_EX)
                blab(log, "Acquired exclusive lock for writing: "+destfile)
            fd.truncate(0)
            json.dump(jsdata, fd, indent=indent, separators=(',', ': '))
        blab(log, "released EX")
            
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

def measure_dir_size(dirpath):
    """
    return a pair of numbers representing, in order, the totaled size (in bytes)
    of all files below the directory and the total number of files.  

    Note that the byte count does not include the capacity taken up by directory
    entries and thus is not an accurate measure of the space the directory takes
    up on disk.

    :param str dirpath:  the path to the directory of interest
    :rtype:  list containing 2 ints
    """
    size = 0
    count = 0
    for root, subdirs, files in os.walk(dirpath):
        count += len(files)
        for f in files:
            size += os.stat(os.path.join(root,f)).st_size
    return [size, count]

def rmtree_sys(rootdir):
    """
    an implementation of rmtree that is intended to work on NSF-mounted 
    directories where shutil.rmtree can often fail.
    """
    if '*' in rootdir or '?' in rootdir:
        raise ValueError("No wildcards allowed in rootdir")
    if not os.path.exists(rootdir):
        return
    cmd = "rm -r ".split() + [rootdir]
    subprocess.check_call(cmd)

def rmtree_retry(rootdir, retries=1):
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
    
rmtree = rmtree_retry
