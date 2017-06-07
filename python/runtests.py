#!/usr/bin/python
#
# discover and execute all the unit tests in the tests tree or only those
# within specified packages.
#
# Usage:  runtests.py [PACKAGE ...]
#
# PACKAGE is a package to run tests for, either using path or module delimits.
# Nominally, a PACKAGE would start with "tests", but if it starts with 
# "nistoar", "tests" will be automatically prepended to the name.  If arguments
# are not given, all tests will be run.
#
import unittest, os, sys, re
import nistoar.pdr as pdr

def _path2mod(path):
    return re.sub(os.sep, '.', path)
def _mod2path(mod):
    return re.sub(r'\.', os.sep, mod)

def discover(within='tests', testsparent=None):
    """
    return a TestSuite containing all tests under a given package.
    """
    return loadtestfiles(discover_testfiles(within, testsparent))

def discover_testfiles(within='tests', testsparent=None):
    """
    find module files containing tests contained within a given package.  
    Test modules have filenames beginning with "test_".
    :param startfrom path or package:  the package to search for tests within;
            the default is the root 'tests' package
    :param testsparent path:  the directory containing the top; the default 
            is the 'python' directory containing the 'tests' module.
    """
    if not testsparent:
        testsparent = os.path.dirname(os.path.abspath(__file__))
    testsparent = testsparent.rstrip('/')

    if '.' in within:
        within = _mod2path(within)
    start = os.path.join(testsparent, within)
    if not os.path.exists(start):
        raise ValueError("Module directory does not exist: " + start)
    if not os.path.isdir(start):
        raise ValueError("Not a package directory: " + start)

    testfiles = []

    for root, dirs, files in os.walk(start):
        rootmod = root[len(testsparent)+1:]
        if '__init__.py' in files:
            for tf in files:
                if tf.startswith('test_') and tf.endswith('.py'):
                    testfiles.append( os.path.join(rootmod, tf) )
                
        else:
            dirs[:] = []

    return testfiles

def loadtestfiles(testfiles=[]):
    subsuites = []

    for tf in testfiles:
        if tf.endswith(".py"):
            pkg = _path2mod(os.path.dirname(tf))
            modname = os.path.basename(tf)[:-3]
            mod = __import__( pkg, globals(), locals(), [modname], -1)
            mod = getattr(mod, modname)
            subsuites.append( unittest.TestLoader().loadTestsFromModule(mod) )
        
    return unittest.TestSuite(subsuites)

def _setlibs():
    oarmetadata = os.path.join(
                     os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "oar-metadata" )

    if not pdr.def_jq_libdir or not os.path.exists(pdr.def_jq_libdir):
        libdir = os.path.join(oarmetadata, 'jq')
        if not os.path.exists(libdir):
            raise RuntimeError("jq library dir ({0}) not found (do you need to run 'git submodule'?)".format(libdir))

        pdr.def_jq_libdir = libdir

    if not pdr.def_merge_etcdir or not os.path.exists(pdr.def_merge_etcdir):
        libdir = os.path.join(oarmetadata, 'jq')
        if not os.path.exists(libdir):
            raise RuntimeError("merge config dir ({0}) not found (do you need to run 'git submodule'?)".format(libdir))

        pdr.def_merge_etcdir = libdir
        

if __name__ == '__main__':
    _setlibs()

    suites = []

    withins = sys.argv[1:]
    if len(withins) < 1:
        withins.append('tests')
        
    for mod in withins:
        if mod.startswith('nistoar'):
            mod = "tests."+mod
        suites.append( discover(mod) )

    result = unittest.TextTestRunner().run(unittest.TestSuite(suites))
    if not result.wasSuccessful():
        sys.exit(1)
    sys.exit(0)
    
