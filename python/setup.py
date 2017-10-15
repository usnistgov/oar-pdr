import os, sys, subprocess, pdb, unittest
from distutils.core import setup
from distutils.command.build import build as _build

def find_oar_metadata(submoddir='oar-metadata'):
    out = submoddir
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(
                           os.path.dirname( os.path.abspath(__file__) )), out)
    outpy = os.path.join(out, "python", "nistoar")
    if not os.path.exists(out):
        msg = "oar-metadata submodule not found in {0} subdirectory" 
        raise RuntimeError(msg.format(dirname))
    if not os.path.exists(outpy):
        msg = "{0} subdirectory does apparently does not contain oar-metadata " \
              "submodule"
        raise RuntimeError(msg.format(dirname))
    return out

def build_oar_metadata(pkgdir, buildlib, buildscrp):
    pydir = os.path.join(pkgdir, "python")
    cmd = "python setup.py build --build-lib={0} --build-scripts={1}" \
        .format(os.path.abspath(buildlib), os.path.abspath(buildscrp)).split()
    if sys.executable:
        cmd[0] = sys.executable
    ex = subprocess.call(cmd, cwd=pydir)
    if ex != 0:
        raise RuntimeError("oar-metadata submodule build failed; exit="+str(ex)+
                           ";\ndir="+pydir+";\ncmd="+" ".join(cmd))

class build(_build):

    def run(self):
        oarmdpkg = find_oar_metadata()
        build_oar_metadata(oarmdpkg, self.build_lib, self.build_scripts)
        _build.run(self)

setup(name='nistoar',
      version='0.1',
      description="nistoar/pdr: support for the NIST Public Data Repository",
      author="Ray Plante",
      author_email="raymond.plante@nist.gov",
      url='https://github.com/usnistgov/oar-pdr',
      scripts=[ '../scripts/ppmdserver.py', '../scripts/ppmdserver-uwsgi.py',
                '../scripts/preserver-uwsgi.py' ],
      packages=['nistoar.pdr', 'nistoar.pdr.publish', 'nistoar.pdr.ingest', 
                'nistoar.pdr.publish.mdserv',
                'nistoar.pdr.preserv', 'nistoar.pdr.preserv.bagger',
                'nistoar.pdr.preserv.bagit', 'nistoar.pdr.preserv.service',
                'nistoar.testing'
            ],
      package_data={'nistoar.pdr': [ 'data/*' ]},
      cmdclass={'build': build}
)

