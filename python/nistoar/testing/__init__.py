"""
test infrastructure and utilities usable throughout the nistoar library
"""

# this code was copied from the testing infrastructure for ejsonschema 

import os, shutil

tmpname = "_test"

def ensure_tmpdir(basedir=None, dirname=None):
    """
    ensure the existance of a directory where temporary inputs and outputs 
    can be placed.  This directory is not cleaned up after use.  

    :argument str basedir: the desired path to tmp directory's parent directory.
                           if not provided, the directory will be placed in the 
                           current working directory.
    :return str: the path to the temporary directory
    """
    tdir = tmpdir(basedir, dirname)
    if not os.path.isdir(tdir):
        os.mkdir(tdir)

    return tdir

def tmpdir(basedir=None, dirname=None):
    """
    return the name of a temporary directory where temporary inputs and outputs 
    can be placed.  

    :argument str basedir: the desired path to tmp directory's parent directory.
                           if not provided, the directory will be placed in the 
                           current working directory.
    :argument str dirname: the desired name for the directory
    :return str: the path to the temporary directory
    """
    if not dirname:
        dirname = tmpname + str(os.getpid())
    if not basedir:
        basedir = os.getcwd()
    return os.path.join(basedir, dirname)

def rmdir(dirpath):
    """
    remove the given path and all its contents
    """
    shutil.rmtree(dirpath)

def rmtmpdir(basedir=None, dirname=None):
    """
    remove the default 

    :argument str basedir: the path to tmp directory's parent directory.
                           if not provided, the current working directory will 
                           be assumed.
    :argument str dirname: the name for the directory
    :return str: the path to the removed temporary directory
    """
    tdir = tmpdir(basedir, dirname)
    if os.path.exists(tdir):
        rmdir(tdir)

class Tempfiles(object):
    """
    A class for creating temporary testing space that hides the configured 
    absolute location.  

    It is instantiated with a base directory where temporary directories and 
    files can be created.  Full paths to a temporary file or directory can 
    be gotten, then, by calling the instance as a function:

       ts = Tempfiles(basedir)
       tmpfile = ts("testoutput.txt")

    If you want the file to be automatically cleaned up, use the track() 
    function:

       tmpfile = ts.track("testoutput.txt")

    Temporary directories that should be cleaned up can be created with mkdir():

       tmpdir = ts.mkdir("mytempdir")

    All directories and files created below the configured base can be removed
    by calling clean() explicitly or by using autoclean=True as a constructor
    parameter; the latter will remove the files and directories when the 
    instance is destroyed.  
    """

    def __init__(self, tempdir=None, autoclean=False):
        if not tempdir:
            tempdir = ensure_tmpdir()
        assert os.path.exists(tempdir)
        self._root = tempdir
        self._files = set()
        self._autoclean = autoclean

    @property
    def root(self):
        """
        the base directory below which is where temporary files and directories 
        can be created and tracked
        """
        return self._root

    def __call__(self, child):
        return os.path.join(self.root, child)

    def mkdir(self, dirname):
        """
        create and track a directory given as a relative path
        """
        d = os.path.join(self.root, dirname)
        if not os.path.isdir(d):
            os.mkdir(d)
        self.track(dirname)
        return d

    def track(self, filename):
        """
        keep track of a file or directory that has a relative path given by 
        filename.  It will be removed upon a call to clean()
        """
        self._files.add(filename)
        return self.__call__(filename)

    def clean(self):
        """
        remove all files and directories being tracked by this instance.
        """
        for i in xrange(len(self._files)):
            filen = self._files.pop()
            path = os.path.join(self._root, filen)
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                finally:
                    if os.path.exists(path):
                        self._files.add(filen)

    def __del__(self):
        if self._autoclean:
            self.clean()
