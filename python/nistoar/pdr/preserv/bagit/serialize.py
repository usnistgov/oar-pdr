"""
Tools for serializing and running checksums on bags
"""
import subprocess as sp
from cStringIO import StringIO
import logging, os

from .exceptions import BagSerializationError
from .. import sys as _sys

def _exec(cmd, dir, log):
    log.info("serializing bag: %s", ' '.join(cmd))
    log.debug("expecting bag in dir: %s", dir)

    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, cwd=dir)
    out, err = map(lambda s: s.strip(), proc.communicate())

    if out:
        log.debug("%s:\n%s", cmd[0], out)

    if proc.returncode > 0:
        log.error("%s exited with error (%d): %s", cmd[0], proc.returncode, err)
        raise sp.CalledProcessError(proc.returncode, cmd, err)
    else:
        log.debug(err)

zip_error = {
    '12': "zip has nothing to do",
    '13': "missing or empty zip file",
    '14': "error writing to a file",
    '15': "zip was unable to create a file to write to",
    '18': "zip could not open a specified file to read",
    '6': "component file too large"
}

def zip_serialize(bagdir, destdir, log, destfile=None):
    """
    serialize a bag with zip

    :param bagdir   str:  path to the bag root directory to be serialized
    :param destdir  str:  path to the output directory to write serialized 
                             file to.  
    :param log   Logger:  a logger to write messages to
    :param destfile str:  the name to give to the serialized file.  If not 
                             provided, one will be constructed from the 
                             bag directory name (and an appropriate extension)
    """
    parent, name = os.path.split(bagdir)
    if not destfile:
        destfile = name+'.zip'
    destfile = os.path.join(destdir, destfile)

    if not os.path.exists(bagdir):
        raise StateException("Can't serialize missing bag directory: "+bagdir)
    if not os.path.exists(destdir):
        raise StateException("Can't serialize to missing destination directory: "
                             +destdir)
    
    cmd = "zip -r".split() + [ destfile, name ]
    try:
        _exec(cmd, parent, log)
    except sp.CalledProcessError, ex:
        if os.path.exists(destfile):
            try:
                os.remove(destfile)
            except Exception:
                pass
        message = zip_error.get(str(ex.returncode))
        if not message:
            message = "Bag serialization failure using zip (consult log)"
        raise BagSerializationError(message, name, ex, sys=_sys)
    except 

    return destfile

def zip7_serialize(bagdir, destdir, log, destfile=None):
    """
    serialize a bag with 7zip

    :param bagdir   str:  path to the bag root directory to be serialized
    :param destdir  str:  path to the output directory to write serialized 
                             file to.  
    :param log   Logger:  a logger to write messages to
    :param destfile str:  the name to give to the serialized file.  If not 
                             provided, one will be constructed from the 
                             bag directory name (and an appropriate extension)
    """
    parent, name = os.path.split(bagdir)
    if not destfile:
        destfile = name+'.7z'
    destfile = os.path.join(destdir, destfile)
    
    cmd = "7z a -t7z".split() + [ destfile, name ]
    try:
        _exec(cmd, parent, log)
    except sp.CalledProcessError, ex:
        if os.path.exists(destfile):
            try:
                os.remove(destfile)
            except Exception:
                pass
        if ex.returncode == 1:
            msg = "7z could not read one or more files"
        else:
            msg = "Bag serialization failure using 7z (consult log)"
        raise BagSerializationError(msg, name, ex, sys=_sys)

    return destfile

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

    @property
    def formats(self):
        """
        a list of the names of formats supported by this serializer
        """
        return self._map.keys()

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
                                        str(format))
        if not log:
            if self.log:
                log = self.log
            else:
                log = logging.getLogger(_sys.system_abbrev).\
                              getChild(_sys.subsystem_abbrev)
        return self._map[format](bagdir, destdir, log)

class DefaultSerializer(Serializer):
    """
    a Serializer configured for some default serialization formats: zip, 7z.
    """

    def __init__(self, log=None):
        super(DefaultSerializer, self).__init__({
            "zip": zip_serialize,
            "7z": zip7_serialize
        }, log)
