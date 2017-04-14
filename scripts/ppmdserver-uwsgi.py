"""
The uWSGI script for launching the metadata server.
"""
import uwsgi.opt
from nistoar.pdr.exceptions import ConfigurationError
from nistoar.pdr.publish.mdserv import wsgi, config

# determine where the configuration is coming from
confsrc = uwsgi.opt.get("nistoar_config_file")
if not confsrc:
    raise ConfigurationError("ppmdserver: nist-oar configuration not provided")

cfg = config.resolve_configuration(confsrc)
application = wsgi.app(cfg)


