"""
Utility functions useful across the pdr package
"""
from collections import OrderedDict, Mapping
import hashlib, json, re, shutil, os, time, subprocess, logging, threading
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

class LockedFile(object):
    """
    An object representing a file in a locked state.  The file is locked against
    simultaneous accesses across both threads and processes.  

    The easiest way to use this class is via the with statement.  For example,
    to read a file with a shared lock (many reads, no writes):
    .. code-block:: python

       with LockedFile(filename) as fd:
           data = json.load(fd)

    And to write a file with an exclusive write (no other simultaneous reads 
    or writes):
    .. code-block:: python

       with LockedFile(filename, 'w') as fd:
           json.dump(data, fd)

    An example of its use without the with statement might be:
    .. code-block:: python

       lkdfile = LockedFile(filename)
       fd = lkdfile.open()
       data = json.load(fd)
       lkdfile.close()    #  do not call fd.close() !!!

       lkdfile.mode = 'w'
       with lkdfile as fd:
          json.dump(data, fd)

    """
    _thread_locks = {}
    _class_lock = threading.RLock()

    class _ThreadLock(object):
        _reader_count = 0
        def __init__(self):
            self.ex_lock = threading.Lock()
            self.sh_lock = threading.Lock()
        def acquire_shared(self):
            with self.ex_lock:
                if not self._reader_count:
                    self.sh_lock.acquire()
                self._reader_count += 1
        def release_shared(self):
            with self.ex_lock:
                if self._reader_count > 0:
                    self._reader_count -= 1
                if self._reader_count <= 0:
                    self.sh_lock.release()
        def acquire_exclusive(self):
            with self.sh_lock:
                self.ex_lock.acquire()
        def release_exclusive(self):
            self.ex_lock.release()
            
    @classmethod
    def _get_thread_lock_for(cls, filepath):
        filepath = os.path.abspath(filepath)
        with cls._class_lock:
            if filepath not in cls._thread_locks:
                cls._thread_locks[filepath] = cls._ThreadLock()
            return cls._thread_locks[filepath]

    def __init__(self, filename, mode='r'):
        self.mode = mode
        self._fo = None
        self._fname = filename
        self._thread_lock = self._get_thread_lock_for(filename)
        self._writing = None

    @property
    def fo(self):
        """
        the open file object or None if the file is not currently open
        """
        return self._fo

    def _acquire_thread_lock(self):
        if self._writing:
            self._thread_lock.acquire_exclusive()
        else:
            self._thread_lock.acquire_shared()
    def _release_thread_lock(self):
        if self._writing:
            self._thread_lock.release_exclusive()
        else:
            self._thread_lock.release_shared()

    def open(self, mode=None):
        """
        Open the file so that it is appropriate locked.  If mode is not 
        provided, the mode will be the value set when this object was 
        created.  
        """
        if self._fo:
            raise StateException(self._fname+": file is already open")
        if mode:
            self.mode = mode
            
        self._writing = 'a' in self.mode or 'w' in self.mode or '+' in self.mode
        self._acquire_thread_lock()
        try:
            self._fo = open(self._fname, self.mode)
        except:
            self._release_thread_lock()
            if self._fo:
                try:
                    self._fo.close()
                except:
                    pass
            self._fo = None
            self._writing = None
            raise

        if fcntl:
            lock_type = (self._writing and fcntl.LOCK_EX) or fcntl.LOCK_SH
            fcntl.lockf(self.fo, lock_type)
        return self.fo

    def close(self):
        if not self._fo:
            return
        try:
            self._fo.close()
        finally:
            self._fo = None
            self._release_thread_lock()
            self._writing = None

    def __enter__(self):
        return self.open()

    def __exit__(self, e1, e2, e3):
        self.close()
        return False

    def __del__(self):
        if self._fo:
            self.close()

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
    with LockedFile(jsonfile) as fd:
        blab(log, "Acquired shared lock for reading: "+jsonfile)
        out = json.load(fd, object_pairs_hook=OrderedDict)
    blab(log, "released SH")
    return out

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
        with LockedFile(destfile, 'a') as fd:
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
