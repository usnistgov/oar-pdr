#! /usr/bin/python
#
import os, sys, subprocess
import unittest as test

scriptdir = os.path.dirname(__file__)
pkgdir = os.path.dirname(scriptdir)
pydir = os.path.join(pkgdir, "python")

def build_py(pydir, builddir):
    cmd = "python setup.py build --build-base={0}" \
        .format(os.path.abspath(builddir)).split()
    if sys.executable:
        cmd[0] = sys.executable
    ex = subprocess.call(cmd, cwd=pydir)
    if ex != 0:
        raise RuntimeError("oar-pdr build failed; exit="+str(ex)+
                           ";\ndir="+pydir+";\ncmd="+" ".join(cmd))

def the_test_suite(pydir):
    test_loader = test.TestLoader()
    test_suite = test_loader.discover(pydir, 'test_*.py')
    return test_suite

def testall(pydir):
    bdir = os.path.join(pydir, "build")
    build_py(pydir, bdir)
    result = test.TextTestRunner().run(the_test_suite(pydir))
    return result.wasSuccessful()

if __name__ == '__main__':
    if not testall(pydir):
        sys.exit(1)
