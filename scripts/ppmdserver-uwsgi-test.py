"""
The uWSGI script for launching the metadata server.
"""
import sys, os, traceback as tb
import uwsgi
from nistoar.pdr.exceptions import ConfigurationException
from nistoar.pdr.publish.mdserv import wsgi, config

bagparent = "_ppmdserver_test"+str(os.getpid())
datadir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "python",
                       "nistoar", "pdr", "preserv", "tests", "data")
midasdir = os.path.join(datadir, "midassip")
revdir = os.path.join(midasdir,"review")
upldir = os.path.join(midasdir,"upload")
midasid = '3A1EE2F169DD3B8CE0531A570681DB5D1491'

def default_config():
    if not os.path.exists(bagparent):
        os.mkdir(bagparent)
    return {
        'working_dir':     bagparent,
        'review_dir':      revdir,
        'upload_dir':      upldir,
        'id_registry_dir': bagparent
    }

cfg = default_config()
config.configure_log(config=cfg)
application = wsgi.app(cfg)


