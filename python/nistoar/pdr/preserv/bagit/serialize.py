"""
Tools for serializing and running checksums on bags
"""
import subprocess as sp
from cStringIO import StringIO

from .exception import BagSerializationError
from . import sys as _sys

def _exec(cmd, dir, log):
    log.info("serializing bag: %s", ' '.join(cmd))

    out = StringIO()
    err = StringIO()
    try:
        sp.check_call(cmd, stdout=out, stderr=err, cwd=dir)
    except sp.CalledProcessError, ex:
        log.error("%s exited with error (%d): %s", cmd[0], proc.returncode, err)
        raise
    finally:
        log.debug("output from %s:\n%s", cmd[0], out)

zip_error = {
    '12': "zip has nothing to do",
    '13': "missing or empty zip file",
    '14': "error writing to a file",
    '15': "zip was unable to create a file to write to",
    '18': "zip could not open a specified file to read",
    '6': "component file too large"
}

def zip_serialize(bagdir, destfile, log):
    """
    serialize a bag with zip
    """
    parent, name = os.path.split(bagdir)
    
    cmd = "zip -r".split() + [ destfile, name ]
    try:
        _exec(cmd, parent, log)
    except sp.CalledProcessError, ex:
        message = zip_error.get(str(ex.returncode))
        if not message:
            message = "Bag serialization failure using zip (consult log)"
        raise BagSerializationError(msg, name, ex, sys=_sys)

def zip7_serialize(bagdir, destfile, log):
    """
    serialize a bag with 7zip
    """
    parent, name = os.path.split(bagdir)
    
    cmd = "7z a -t7z".split() + [ destfile, name ]
    try:
        _exec(cmd, parent, log)
    except sp.CalledProcessError, ex:
        if ex.returncode == 1:
            message = "7z could not read one or more files"
        else:
            message = "Bag serialization failure using 7z (consult log)"
        raise BagSerializationError(msg, name, ex, sys=_sys)

class Serializer(object):
    """
    a class that serialize a bag using the archiving technique identified 
    by a given name.  
    """

    def __init__(self, typefunc=None, log=None):
        """
        """
        self._map = {}
        if typefunc:
            self._map.update(typefunc)
        self.log = log

    def setLog(self, log):
        self.log = log

    def register(self, format, serfunc):
        """
        register a serialization function to make available via this serializer.
        The provided function must take 3 arguments:
          bagdir -- the root directory of the bag to serialize
          destination -- the path to the desired output bagfile.  
          log -- a logger object to send messages to.

        :param format str:   the name users can use to select the serialization
                             format.
        :param serfunc func:  the serializaiton function to associate with this
                           name.  
        """
        if not isinstance(serfunc, func):
            raise TypeError("Serializer.register(): serfunc is not a function: "+
                            str(func))
        self._map[format] = serfunc

    def serialize(self, bagdir, destdir, format, log=None):
        """
        serialize a bag using the named serialization format
        """
        if format not in self._map:
            raise BagSerializationError("Serialization format not supported: "+
                                        format)
        if not log:
            if self.log:
                log = self.log
            else:
                log = logging.getLogger(_sys.system_abbrev).
                              getChild(_sys.subsystem_abbrev)
        self._map[format](bagdir, destdir, log)

class DefaultSerializer(Serializer):
    """
    a Serializer configured for some default serialization formats: zip, 7z.
    """

    def __init__(self, log=None):
        super(DefaultSerializer, self).__init__({
            "zip": zip_serializer,
            "7z": zip7_serializer
        }, log)
