"""
The uWSGI script for launching the preservation service (for testing)
"""
import os, sys, logging, copy, shutil, traceback as tb
import uwsgi
try:
    import nistoar
except ImportError:
    oarpath = os.environ.get('OAR_PYTHONPATH')
    if not oarpath and 'OAR_HOME' in os.environ:
        oarpath = os.path.join(os.environ['OAR_HOME'], "lib", "python")
    if oarpath:
        sys.path.insert(0, oarpath)
    import nistoar

from nistoar.pdr.exceptions import ConfigurationException
from nistoar.pdr.preserv.service import wsgi
from nistoar.pdr.publish.mdserv import config

# determine where the configuration is coming from
confsrc = uwsgi.opt.get("oar_config_file")

# For this testing version of the ppmdserver, these uwsgi parameters will
# override the corresponding values in the configuration file
#
if uwsgi.opt.get('oar_working_dir'):
    bagparent = uwsgi.opt.get('oar_working_dir')
else:
    bagparent = "_preserver_test"+str(os.getpid())

if uwsgi.opt.get('oar_midas_dir'):
    datadir = uwsgi.opt.get('oar_midas_dir')
else:
    datadir = os.path.join(os.path.dirname(os.path.dirname(
                           os.path.abspath(__file__))), "python", "tests", 
                           "nistoar", "pdr", "preserv", "data")

midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

def adjust_config(config):
    doclean = uwsgi.opt.get('oar_clean_workdir', None)
    datadir = uwsgi.opt.get('oar_midas_parent','SRCTESTDATA')
    workdir = uwsgi.opt.get('oar_preserver_workdir')
    storedir = uwsgi.opt.get('oar_preserver_storedir')
    if not workdir:
        workdir = os.path.join(os.getcwd(), "_preserver-"+str(os.getpid()))
        if doclean is None:
            doclean = True
    if not storedir:
        storedir = os.path.join(workdir, 'store')       
    if datadir == 'SRCTESTDATA':
        datadir = os.path.join(os.path.dirname(os.path.dirname(
                               os.path.abspath(__file__))), "python", "tests", 
                               "nistoar", "pdr", "preserv", "data", "midassip")
        revdir = os.path.join(workdir, "review")
        print >> sys.stderr, "copying review data"
        shutil.copytree(os.path.join(datadir,'review'), revdir)
        assert os.path.exists(revdir)
    else:
        revdir = os.path.join(datadir, 'review')

    out = copy.deepcopy(config)
    out.update( {
        'working_dir':       workdir,
        'id_registry_dir':   workdir,
        'store_dir':         os.path.join(workdir, 'store'),
        'sip_type': {
            'midas': {
                'common': {
                    'review_dir': revdir,
                    "id_minter": { "shoulder_for_edi": "edi0" },
                },
                "mdserv": {
                    "working_dir": os.path.join(workdir, 'mdserv')
                },
                "preserv": {
                    "bagparent_dir": "_preserv",
                    "staging_dir": os.path.join(workdir, 'stage'),
                    "bagger": { 'relative_to_indir': True },
                    "status_manager": {
                        "cachedir": os.path.join(workdir, 'status')
                    }
                }
            }
        },
        'clean_working_dir': doclean,
        'logfile':           'preserve-test.log'
    } )

    return out

cfg = {}
if confsrc:
    cfg = config.resolve_configuration(confsrc)
cfg = adjust_config(cfg)

workdir = os.path.abspath(cfg['working_dir'])
storedir = os.path.abspath(cfg['store_dir'])
mdservdir = os.path.join(workdir, 'mdserv')
doclean = cfg['clean_working_dir']

config.configure_log(config=cfg, addstderr=True)
logging.getLogger().setLevel(logging.DEBUG)
logging.info("Starting server with working_dir=%s, midas_dir=%s, store=%s",
             bagparent, datadir, storedir)

if not os.path.exists(workdir):
    os.mkdir(workdir)

if doclean:
    for item in os.listdir(workdir):
        if item == 'review':
            continue
        ipath = os.path.join(workdir, item)
        try:
            if os.path.isfile(ipath) or os.path.islink(ipath):
                os.remove(ipath)
            elif os.path.isdir(ipath):
                shutil.rmtree(ipath)
        except OSError, e:
            log.warn("Failed to clean item from working directory: %s",ipath)

if not os.path.exists(storedir):
    os.mkdir(storedir)
if not os.path.exists(mdservdir):
    os.mkdir(mdservdir)

application = wsgi.app(cfg)
