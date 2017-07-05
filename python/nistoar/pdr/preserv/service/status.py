"""
This module provides tools for managing and retrieving the status of a 
preservation efforts across multiple processes.  
"""
import json, os, time, fcntl
from collections import OrderedDict
from copy import deepcopy

from ...exceptions import StateException
from .. import sys as preservsys

NOT_FOUND   = "not found"
READY       = "ready"
PENDING     = "pending"
IN_PROGRESS = "in progress"
SUCCESSFUL  = "successful"
FAILED      = "failed"
FORGOTTEN   = "forgotten"

states = [ NOT_FOUND, READY, PENDING, 
           IN_PROGRESS, SUCCESSFUL, FAILED, FORGOTTEN ]

user_message = {
    NOT_FOUND:   "Data not found for given identifier",
    READY:       "Data is available for preservation",
    PENDING:     "Preservation requested, will start shortly",
    IN_PROGRESS: "Preservation processing in progress",
    SUCCESSFUL:  "Data was successfully preserved",
    FAILED:      "Data preservation failed due to internal errors",
    FORGOTTEN:   "Preservation history is no longer available"
}

LOCK_WRITE = fcntl.LOCK_EX
LOCK_READ  = fcntl.LOCK_SH

class SIPStatusFile(object):
    """
    a class used to manage locked access to the status data file
    """
    LOCK_WRITE = fcntl.LOCK_EX
    LOCK_READ  = fcntl.LOCK_SH
    
    def __init__(self, filepath, locktype=None):
        """
        create the file wrapper
        :param filepath  str: the path to the file
        :param locktype:      the type of lock to acquire.  The value should 
                              be either LOCK_READ or LOCK_WRITE.
                              If None, no lock is acquired.  
        """
        self._file = filepath
        self._fd = None
        self._type = None

        if locktype is not None:
            self.acquire(locktype)

    def __del__(self):
        self.release()

    @property
    def lock_type(self):
        """
        the current type of lock held, or None if no lock is held.
        """
        return self._type

    def acquire(self, locktype):
        """
        set a lock on the file
        """
        if self._fd:
            if self._type == locktype:
                return False
            elif locktype == self.LOCK_WRITE:
                raise RuntimeError("Release the read lock before "+
                                   "requesting write lock")

        if locktype == LOCK_READ:
            self._fd = open(self._file)
            fcntl.flock(self._fd, fcntl.LOCK_SH)
            self._type = LOCK_READ
        elif locktype == LOCK_WRITE:
            self._fd = open(self._file, 'w')
            fcntl.flock(self._fd, fcntl.LOCK_EX)
            self._type = LOCK_WRITE
        else:
            raise ValueError("Not a recognized lock type: "+ str(locktype))
        return True

    def release(self):
        if self._fd:
            self._fd.seek(0, os.SEEK_END)
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None
            self._type = None

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_val, ex_tb):
        self.release()

    def read_data(self):
        """
        read the status data from the configured file.  If a lock is not 
        currently set, one is acquired and immediately released.  
        """
        release = self.acquire(LOCK_READ)
        self._fd.seek(0)
        out = json.load(self._fd, object_pairs_hook=OrderedDict)
        if release:
            self.release()
        return out
        
    def write_data(self, data):
        """
        write the status data to the configured file.  If a lock is not 
        currently set, one is acquired and immediately released.  
        """
        release = self.acquire(LOCK_WRITE)
        self._fd.seek(0)
        json.dump(data, self._fd, indent=2, separators=(',', ': '))
        if release:
            self.release()

    @classmethod
    def read(cls, filepath):
        return cls(filepath).read_data()

    @classmethod
    def write(cls, filepath, data):
        cls(filepath).write_data(data)

def _read_status(filepath):
    try:
        with open(filepath) as fd:
            try:
                fcntl.flock(fd, fcntl.LOCK_SH)
                return json.load(fd, object_pairs_hook=OrderedDict)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError, ex:
        raise StateException("Can't open preservation status file: "
                             +filepath+": "+str(ex), cause=ex,
                             sys=preservsys)


def _write_status(filepath, data):
    try:
        with open(filepath, 'w') as fd:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                json.dump(data, fd, indent=2, separators=(',', ': '))
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError, ex:
        raise StateException("Can't open preservation status file: "
                             +filepath+": "+str(ex), cause=ex,
                             sys=preservsys)

class SIPStatus(object):
    """
    a class that represents the status of an SIP process effort (for 
    preservation).  It encapsulates a dictionary of data that can get updated 
    as the preservation process progresses.  This data is cached to disk so 
    that multiple processes can access it.  
    """

    def __init__(self, id, config=None, _data=None):
        """
        open up the status for the given identifier.  Initial data can be 
        provided or, if no cached data exist, it can be initialized with 
        default data.  In either case, this constructor will not cache the
        data until next call to update() or cache().  

        :param id str:       the identifier for the SIP
        :param config str:   the configuration data to apply.  If not provided
                             defaults will be used; in particular, the status
                             data will be cached to /tmp (intended only for 
                             testing purposes).
        :param _data dict:   initialize the status with this data.  This is 
                             not intended for public use.   
        """
        if not id:
            raise ValueError("SIPStatus(): id needs to be non-empty")
        if not config:
            config = {}
        cachedir = config.get('cachedir', '/tmp/sipstatus')
        self._cachefile = os.path.join(cachedir, id + ".json")

        if _data:
            self._data = deepcopy(_data)
        elif os.path.exists(self._cachefile):
            self._data = SIPStatusFile.read(self._cachefile)
        else:
            self._data = OrderedDict([
                ('sys', {}),
                ('user', OrderedDict([
                    ('state', PENDING),
                    ('message', user_message[PENDING])
                ])),
                ('history', [])
            ])
        self._data['user']['id'] = id

    @property
    def id(self):
        """
        the SIP's identifier
        """
        return self._data['user']['id']

    @property
    def data(self):
        """
        the current status data.  Required fields include:
        :prop id    str:  the SIP's id
        :prop state str:  controlled name for the current state of preservation
                          of the SIP
        :prop message str:  a user-oriented message explaining the state
        """
        return self._data

    def cache(self):
        """
        cache the data to a JSON file on disk
        """
        if not os.path.exists(self._cachefile):
            cachedir = os.path.dirname(self._cachefile)
            if not os.path.exists(cachedir):
                try:
                    os.mkdir(cachedir)
                except Exception, ex:
                    raise StateException("Can't create preservation status dir: "
                                         +cachedir+": "+str(ex), cause=ex,
                                         sys=preservsys)

        self._data['user']['update_time'] = time.time()
        self._data['user']['updated'] = time.asctime()
        SIPStatusFile.write(self._cachefile, self._data)
        
    def update(self, label, message=None):
        """
        change the state of the processing.  In addition to updating the 
        data in-memory, the full, current set of status metadata will be 
        flushed to disk.

        :param label   str:  one of the recognized state labels defined in this
                             class's module (e.g. IN_PROGRESS).  
        :param message str:  an optional message for display to the end user
                             explaining this state.  If not provided, a default
                             explanation is set. 
        """
        if label not in states:
            raise ValueError("Not a recognized state label: "+label)
        if not message:
            message = user_message[label]
        self._data['user']['state'] = label
        self._data['user']['message'] = message
        self.cache()
        

    def start(self, message=None):
        """
        Set the starting time to now and change the state to IN_PROGRESS.

        :param message str:  an optional message for display to the end user
                             explaining this state.  If not provided, a default
                             explanation is set. 
        """
        self._data['user']['start_time'] = time.time()
        self._data['user']['started'] = time.asctime()
        self.update(IN_PROGRESS, message)

    def record_progress(self, message):
        """
        Update the status with a user-oriented message.  The state will be 
        unchanged, but the data will be cached to disk.
        """
        self._data['user']['message'] = message
        self.cache()

    def refresh(self):
        """
        Read the cached status data and replace the data in memory.
        """
        if os.path.exists(self._cachefile):
            self._data = SIPStatusFile.read(self._cachefile)

    def user_export(self):
        """
        return the porion of the status data intended for export through the
        preservation service interface.  
        """
        out = deepcopy(self._data['user'])
        out['history'] = self._data['history']
        return out


    @classmethod
    def for_update(cls, sipid, cfg=None):
        """
        create an SIPStatus to track an update to a previously preserved
        SIP.  
        """
        prev = SIPStatus(sipid, cfg)
        if 'update_time' not in prev.data['user']:
            return prev

        pending = SIPStatus('__noid__', {})
        if 'history' in prev.data and prev.data['history']:
            pending.data['history'] = deepcopy(prev.data['history'])

        del prev.data['user']['id']
        if 'history' in pending.data:
            pending.data['history'].insert(0, prev.data['user'])
        else:
            pending.data['history'] = [ prev.data['user'] ]

        out = SIPStatus(sipid, cfg, _data=pending.data)
        out.cache()
        return out

        
