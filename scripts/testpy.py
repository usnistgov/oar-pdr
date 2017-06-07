#! /usr/bin/python
#
# Run the oar-pdr unittests, building the code and setting the python path
# as needed.  This is in implementation a wrapper around runtests.py with this
# script handling the building and path setting.
# 
import os, sys, subprocess, unittest
import unittest as test

scriptdir = os.path.dirname(__file__)
pkgdir = os.path.dirname(scriptdir)
pydir = os.path.join(pkgdir, "python")
builddir = os.path.join(pydir, "build")
runtests = os.path.join(pydir, "runtests.py")

def build_py(pydir, builddir):
    cmd = "python setup.py build --build-base={0}" \
        .format(os.path.abspath(builddir)).split()
    if sys.executable:
        cmd[0] = sys.executable
    ex = subprocess.call(cmd, cwd=pydir)
    if ex != 0:
        raise RuntimeError("oar-pdr build failed; exit="+str(ex)+
                           ";\ndir="+pydir+";\ncmd="+" ".join(cmd))

def run_tests(pydir=pydir, builddir=builddir):
    try:
        import nistoar
    except ImportError:
        libdir = glob.glob(os.path.join(builddir, 'lib.*'))
        if len(libdir) > 0:
            sys.path.insert(0, libdir[0])
        import nistoar

    try:
        import runtests
    except ImportError:
        sys.path.insert(0, pydir)
        import runtests

    result = unittest.TextTestRunner().run(runtests.discover())
    return result.wasSuccessful()

if __name__ == '__main__':
    if not run_tests():
        sys.exit(1)
    sys.exit(0)

