"""
The uWSGI script for launching the metadata server.
"""
import sys, os, logging, copy, shutil, traceback as tb
import uwsgi
from nistoar.pdr.exceptions import ConfigurationException
from nistoar.pdr.publish.mdserv import wsgi, config

confsrc = uwsgi.opt.get("oar_config_file")

# For this testing version of the ppmdserver, these uwsgi parameters will
# override the corresponding values in the configuration file
#
if uwsgi.opt.get('oar_working_dir'):
    bagparent = uwsgi.opt.get('oar_working_dir')
else:
    bagparent = "_ppmdserver_test"+str(os.getpid())

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
    workdir = uwsgi.opt.get('oar_mdserv_workdir')
    if not workdir:
        workdir = "_ppmdserver-"+str(os.getpid())
        if doclean is None:
            doclean = True 
    if datadir == 'SRCTESTDATA':
        datadir = os.path.join(os.path.dirname(os.path.dirname(
                               os.path.abspath(__file__))), "python", "tests", 
                               "nistoar", "pdr", "preserv", "data", "midassip")

    out = copy.deepcopy(config)
    out.update( {
        'working_dir':       workdir,
        'review_dir':        os.path.join(datadir, "review"),
        'upload_dir':        os.path.join(datadir, "upload"),
        'id_registry_dir':   workdir,
        'clean_working_dir': doclean,
        'logfile':           'ppmdserver-test.log',
    } )

    return out

cfg = {}
if confsrc:
    cfg = config.resolve_configuration(confsrc)
cfg = adjust_config(cfg)

workdir = cfg['working_dir']
doclean = cfg['clean_working_dir']
if not os.path.exists(workdir):
    os.mkdir(workdir)

config.configure_log(config=cfg, addstderr=True)
logging.getLogger().setLevel(logging.DEBUG)
logging.info("Starting server with working_dir=%s, midas_dir=%s",
             bagparent, datadir)

if doclean:
    for item in os.listdir(workdir):
        ipath = os.path.join(workdir, item)
        try:
            if os.path.isfile(ipath) or os.path.islink(ipath):
                os.remove(ipath)
            elif os.path.isdir(ipath):
                shutil.rmtree(ipath)
        except OSError, e:
            log.warn("Failed to clean item from working directory: %s",ipath)

application = wsgi.app(cfg)


