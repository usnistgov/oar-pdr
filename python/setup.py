import os, sys, subprocess, pdb, unittest
from distutils.core import setup
from distutils.command.build import build as _build

def set_version():
    try:
        pkgdir = os.environ.get('PACKAGE_DIR', '..')
        setver = os.path.join(pkgdir,'scripts','setversion.sh')
        if os.path.exists(setver):
            if not os.access(setver, os.X_OK):
                setver = "bash "+setver
            excode = os.system(setver)
            if excode != 0:
                raise RuntimeError("setversion.sh encountered an error")
    except Exception as ex:
        print("Unable to set build version: " + str(ex))

def get_version():
    out = "dev"
    pkgdir = os.environ.get('PACKAGE_DIR', '..')
    versfile = os.path.join(pkgdir, 'VERSION')
    if not os.path.exists(versfile):
        set_version()
    if os.path.exists(versfile):
        with open(versfile) as fd:
            parts = fd.readline().split()
        if len(parts) > 0:
            out = parts[-1]
    else:
        out = "(unknown)"
    return out

def write_version_mod(version):
    nistoardir = 'nistoar'
    print("looking in nistoar")
    for pkg in [f for f in os.listdir(nistoardir) \
                  if not f.startswith('_') and not f.startswith('.')
                     and os.path.isdir(os.path.join(nistoardir, f))]:
        print("setting version for nistoar."+pkg)
        versmodf = os.path.join(nistoardir, pkg, "version.py")
        with open(versmodf, 'w') as fd:
            fd.write('"""')
            fd.write("""
An identification of the subsystem version.  Note that this module file gets 
(over-) written by the build process.  
""")
            fd.write('"""\n\n')
            fd.write('__version__ = "')
            fd.write(version)
            fd.write('"\n')

def find_oar_metadata(submoddir='oar-metadata'):
    out = submoddir
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(
                           os.path.dirname( os.path.abspath(__file__) )), out)
    outpy = os.path.join(out, "python", "nistoar")
    if not os.path.exists(out):
        msg = "oar-metadata submodule not found in {0} subdirectory" 
        raise RuntimeError(msg.format(out))
    if not os.path.exists(outpy):
        msg = "{0} subdirectory does apparently does not contain oar-metadata " \
              "submodule"
        raise RuntimeError(msg.format(out))
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
        write_version_mod(get_version())
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
                '../scripts/preserver-uwsgi.py', '../scripts/pubserver-uwsgi.py',
                '../scripts/ppmdserver3-uwsgi.py', '../scripts/notify.py' ],
      packages=['nistoar.pdr', 'nistoar.pdr.publish', 'nistoar.pdr.ingest', 
                'nistoar.pdr.distrib', 'nistoar.pdr.describe',
                'nistoar.pdr.publish.mdserv', 'nistoar.pdr.publish.midas3', 'nistoar.pdr.publish.cmd',
                'nistoar.pdr.preserv', 'nistoar.pdr.preserv.bagger',
                'nistoar.pdr.preserv.bagit', 'nistoar.pdr.preserv.service',
                'nistoar.pdr.preserv.bagit.validate', 'nistoar.pdr.notify',
                'nistoar.pdr.preserv.bagit.tools', 'nistoar.testing'
            ],
      package_data={'nistoar.pdr': [ 'data/*' ]},
      cmdclass={'build': build}
)

