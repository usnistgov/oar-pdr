"""
The uWSGI script for launching the metadata server.

This script makes the preservation service deployable as a web service 
via uwsgi.  For example, one can launch the service with the following 
command:

  uwsgi --plugin python --http-socket :9090 --wsgi-file ppmdserver-uwsgi.py \
        --set-ph oar_config_loc=preserver_conf.yml

This script supports a few uwsgi config variables via the --set-ph option; 
the main one, oar_config_loc, identifies the file path or URL to the 
preservation configuration file.  This variable must be provided via the 
uwsgi command-line (as shown above) unless one is launching in test mode.

In test mode, key preservation service configuration parameters will be 
over-ridden to set up and use a test environment, including test data.  This 
mode is turned on by specifying any of the following uwsgi config variables:

   :param oar_testmode bool:  If set, test mode is turned on with a default
                              service configuration.  Use of other 
                              oar_testmode_* variables will override the 
                              defaults.  
   :param oar_testmode_workdir str:  A working directory for all output data
                              and logs as well as some input data.  The 
                              default is ./_preserver-test.$$, where $$ is 
                              uwsgi's proces ID.
   :param oar_testmode_midas_parent str:  The path to a directory that contains
                              stand-ins for the MIDAS data directories.  By 
                              default is set to a directory within the test
                              directory that contains test data.  

This script also pays attention to the following environment variables:

   OAR_HOME          The directory where the OAR PDR system is installed; this 
                        is used to find the OAR PDR python package, nistoar.
   OAR_PYTHONPATH    The directory containing the PDR python module, nistoar.
                        This overrides what is implied by OAR_HOME.
"""
import os, sys, logging, copy
from copy import deepcopy
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
from nistoar.pdr import config
from nistoar.pdr.publish.mdserv import wsgi, extract_mdserv_config

##### These functions used when in test mode

def is_in_test_mode():
    return uwsgi.opt.get('oar_testmode') or \
           uwsgi.opt.get('oar_testmode_workdir') or \
           uwsgi.opt.get('oar_testmode_midas_parent') 

def update_if_test_mode(config):
    # adjust the configuration if we are running in test mode.  

    datadir = uwsgi.opt.get('oar_testmode_midas_parent')
    workdir = uwsgi.opt.get('oar_testmode_workdir')
    testmode = datadir or workdir or uwsgi.opt.get('oar_testmode')
    if not testmode:
        return config
    
    if not workdir:
        workdir = "_ppmdserver-"+str(os.getpid())
    if not datadir:
        datadir = os.path.join(os.path.dirname(os.path.dirname(
                               os.path.abspath(__file__))), "python", "tests", 
                               "nistoar", "pdr", "preserv", "data", "midassip")
    if not os.path.exists(workdir):
        os.mkdir(workdir)

    out = copy.deepcopy(config)
    out.update( {
        'test_mode':         True,
        'test_data_dir':     datadir,
        'working_dir':       workdir,
        'review_dir':        os.path.join(datadir, "review"),
        'upload_dir':        os.path.join(datadir, "upload"),
        'id_registry_dir':   workdir,
        'logfile':           'ppmdserver-test.log',
        'logdir':            workdir,
        'loglevel':          logging.DEBUG
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
confsrc = uwsgi.opt.get("oar_config_loc")
if confsrc:
    cfg = config.resolve_configuration(confsrc)
elif 'oar_config_service' in uwsgi.opt:
    srvc = uwsgi.opt.get('oar_config_service')
    if srvc:
        confsrc = srvc + '/' + uwsgi.opt.get('oar_config_appname', 'pdr-publish')
        if 'oar_config_env' in uwsgi.opt:
            confsrc += '/' + uwsgi.opt.get('oar_config_appname', '')
    
if confsrc:
    cfg = config.resolve_configuration(confsrc)
    cfg = extract_mdserver_config(cfg)
elif is_in_test_mode():
    cfg = {}
else:
    raise ConfigurationException("ppmdserver: nist-oar configuration not "+
                                 "provided")

cfg = update_if_test_mode(cfg)
config.configure_log(config=cfg)

if cfg.get('test_mode'):
    logging.info("Starting server in test mode with work_dir=%s, midas_dir=%s",
                 cfg.get('working_dir'), cfg.get('test_data_dir'))
    clean_working_dir(cfg.get('working_dir'))

application = wsgi.app(cfg)


