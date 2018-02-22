"""
The uWSGI script for launching the metadata server.

This script makes the preservation service deployable as a web service 
via uwsgi.  For example, one can launch the service with the following 
command:

  uwsgi --plugin python --http-socket :9090 --wsgi-file ppmdserver-uwsgi.py \
        --set-ph oar_config_file=preserver_conf.yml

This script supports a few uwsgi config variables via the --set-ph option; 
these are the primary way to inject service configuration into the service.  
These include:

   :param oar_config_service str:  a base URL for the OAR configuration 
                              service.
   :param oar_config_env str:  the environment/profile label to use to 
                              select the version appropriate for the platform.
                              If empty, the default configuration is returned.
   :param oar_config_appname str:  the application/component name for the 
                              configuration. 
   :param oar_config_timeout int:  the number of seconds to wait for the 
                              configuration service to come up.
   :param oar_config_file str:  a local file path or remote URL that holds the 
                              configuration; if given, it will override the 
                              use of the configuration service.  (This should 
                              not be a configuraiton service URL; use 
                              oar_config_service instead.)

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

   OAR_HOME            The directory where the OAR PDR system is installed; this 
                          is used to find the OAR PDR python package, nistoar.
   OAR_PYTHONPATH      The directory containing the PDR python module, nistoar.
                          This overrides what is implied by OAR_HOME.
   OAR_CONFIG_SERVICE  The base URL for the configuration service; this is 
                          overridden by the oar_config_service uwsgi variable. 
   OAR_CONFIG_ENV      The application/component name for the configuration; 
                          this is only used if OAR_CONFIG_SERVICE is used.
   OAR_CONFIG_TIMEOUT  The max number of seconds to wait for the configuration 
                          service to come up (default: 10);
                          this is only used if OAR_CONFIG_SERVICE is used.
   OAR_CONFIG_APP      The name of the component/application to retrieve 
                          configuration data for (default: pdr-publish);
                          this is only used if OAR_CONFIG_SERVICE is used.
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
confsrc = uwsgi.opt.get("oar_config_file")
if confsrc:
    cfg = config.resolve_configuration(confsrc)
elif 'oar_config_service' in uwsgi.opt:
    srvc = config.ConfigService(uwsgi.opt.get('oar_config_service'),
                                uwsgi.opt.get('oar_config_env'))
    srvc.wait_until_up(int(uwsgi.opt.get('oar_config_timeout', 10)),
                       True, sys.stderr)
    cfg = srvc.get(uwsgi.opt.get('oar-config_appname', 'pdr-publish'))
elif config.service:
    config.service.wait_until_up(int(os.environ.get('OAR_CONFIG_TIMEOUT', 10)),
                                 True, sys.stderr)
    cfg = config.service.get(os.environ.get('OAR_CONFIG_APP', 'pdr-publish'))
    cfg = extract_mdserv_config(cfg)
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


