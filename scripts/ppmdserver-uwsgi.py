"""
The uWSGI script for launching the metadata server.
"""
import uwsgi
from nistoar.pdr.exceptions import ConfigurationException
from nistoar.pdr.publish.mdserv import wsgi, config

# determine where the configuration is coming from
confsrc = uwsgi.opt.get("nistoar_config_file")
if not confsrc:
    raise ConfigurationException("ppmdserver: nist-oar configuration not provided")

cfg = config.resolve_configuration(confsrc)
config.configure_log(config=cfg)
application = wsgi.app(cfg)


