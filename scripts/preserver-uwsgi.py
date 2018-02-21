"""
The uWSGI script for launching the preservation service
"""
import os, sys, shutil, copy, logging
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

##### These functions used when in test mode

def is_in_test_mode():
    return bool(uwsgi.opt.get('oar_testmode')) or \
           bool([k for k in uwsgi.opt.keys() if k.startswith('oar_testmode_')])

def update_if_test_mode(config):
    # adjust the configuration only if we are running in test mode.  
    if not is_in_test_mode():
        return config
    
    datadir = uwsgi.opt.get('oar_testmode_midas_parent')
    workdir = uwsgi.opt.get('oar_testmode_workdir')
    doclean = uwsgi.opt.get('oar_testmode_clean_workdir', None)
    storedir = uwsgi.opt.get('oar_testmode_storedir')
    if not workdir:
        workdir = os.path.join(os.getcwd(), "_preserver-"+str(os.getpid()))
        if doclean is None:
            doclean = True
    if not storedir:
        storedir = os.path.join(workdir, 'store')       
    if not datadir:
        datadir = os.path.join(os.path.dirname(os.path.dirname(
                               os.path.abspath(__file__))), "python", "tests", 
                               "nistoar", "pdr", "preserv", "data", "midassip")
        revdir = os.path.join(workdir, "review")
        print >> sys.stderr, "copying review data"
        if os.path.isdir(revdir):
            shutil.rmtree(revdir)
        shutil.copytree(os.path.join(datadir,'review'), revdir)
        assert os.path.exists(revdir)
    else:
        revdir = os.path.join(datadir, 'review')
    if not os.path.exists(workdir):
        os.mkdir(workdir)
    if not os.path.exists(storedir):
        os.mkdir(storedir)

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
                    },
                    'logfile':   'preserve-test.log',
                    'logdir':    workdir,
                    'loglevel':  logging.DEBUG,
                }
            }
        },
        'test_mode': True
    } )

    return out

def clean_working_dir(workdir):
    for item in os.listdir(workdir):
        ipath = os.path.join(workdir, item)
        try:
            if os.path.isfile(ipath) or os.path.islink(ipath):
                os.remove(ipath)
            elif os.path.isdir(ipath):
                shutil.rmtree(ipath)
        except OSError, e:
            logging.warn("Failed to clean item from working directory: %s",ipath)

#####

# determine where the configuration is coming from
confsrc = uwsgi.opt.get("oar_config_file")
if confsrc:
    cfg = config.resolve_configuration(confsrc)
elif is_in_test_mode():
    cfg = {}
else:
    raise ConfigurationException("preserver: nist-oar configuration not "+
                                 "provided")

cfg = update_if_test_mode(cfg)
logcfg = cfg.get('sip_type',{}).get('midas',{}).get('preserv',{})
if 'logfile' not in logcfg:
    logcfg['logfile'] = 'preservation.log'
config.configure_log(config=logcfg, addstderr=True)

if cfg.get('test_mode'):
    logging.info("Starting server in test mode with work_dir=%s, midas_dir=%s, "+
                 "store=%s", cfg.get('working_dir'), cfg.get('test_data_dir'),
                 cfg.get('store_dir'))
    mdwd = cfg.get('sip_type',{}).get('midas',{}).get('mdserv',{}) \
              .get('working_dir')
    if mdwd:
        if os.path.exists(mdwd):
            clean_working_dir(mdcfg.get('working_dir'))
        else:
            os.mkdir(mdwd)

application = wsgi.app(cfg)
