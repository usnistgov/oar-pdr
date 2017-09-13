"""
The uWSGI script for launching the preservation service
"""
import os, sys
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
if not confsrc:
    raise ConfigurationException("preserver: nist-oar configuration not provided")

cfg = config.resolve_configuration(confsrc)
logcfg = cfg.get('sip_type',{}).get('midas',{}).get('preserv',{})
if 'logfile' not in logcfg:
    logcfg['logfile'] = 'preservation.log'
config.configure_log(config=logcfg, addstderr=True)
application = wsgi.app(cfg)
