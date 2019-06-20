"""
Tools for building a NIST Preservation bags
"""
from __future__ import print_function, absolute_import
from __future__ import print_function, absolute_import
import os, errno, logging, re, pkg_resources, textwrap, datetime
import pynoid as noid
from shutil import copy as filecopy, rmtree
from copy import deepcopy
from collections import Mapping, Sequence, OrderedDict
from urllib import quote as urlencode

from .. import PreservationSystem
from .. import ConfigurationException, StateException, PODError
from .exceptions import (BagProfileError, BagWriteError, BadBagRequest,
                         ComponentNotFound)
from ....nerdm.exceptions import (NERDError, NERDTypeError)
from ....nerdm.convert import PODds2Res
from ....id import PDRMinter, NIST_ARK_NAAN
from ...utils import (build_mime_type_map, checksum_of, measure_dir_size,
                      read_nerd, read_pod, write_json)

from ....id import PDRMinter
from ... import def_jq_libdir, def_etc_dir
from ...config import load_from_file, merge_config
from .bag import NISTBag
from .exceptions import BadBagRequest
from .validate.nist import NISTAIPValidator

from multibag import open_headbag

NORM=15  # Log Level for recording normal activity
logging.addLevelName(NORM, "NORMAL")
log = logging.getLogger(__name__)

DEF_BAGLOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"

POD_FILENAME = "pod.json"
NERDMD_FILENAME = "nerdm.json"
FILEMD_FILENAME = NERDMD_FILENAME
RESMD_FILENAME  = NERDMD_FILENAME
COLLMD_FILENAME = NERDMD_FILENAME

ANNOT_FILENAME = "annot.json"
FILEANNOT_FILENAME = ANNOT_FILENAME
RESANNOT_FILENAME  = ANNOT_FILENAME
COLLANNOT_FILENAME = ANNOT_FILENAME

NERD_PRE = "nrd"
NERDPUB_PRE = "nrdp"
NERDM_SCH_ID_BASE = "https://data.nist.gov/od/dm/nerdm-schema/"
NERDMPUB_SCH_ID_BASE = "https://data.nist.gov/od/dm/nerdm-schema/pub/"
NERDM_SCH_VER = "v0.2"
NERDMPUB_SCH_VER = NERDM_SCH_VER
NERDM_SCH_ID = NERDM_SCH_ID_BASE + NERDM_SCH_VER + "#"
NERDMPUB_SCH_ID = NERDMPUB_SCH_ID_BASE + NERDMPUB_SCH_VER + "#"
NERD_DEF = NERDM_SCH_ID + "/definitions/"
NERDPUB_DEF = NERDMPUB_SCH_ID + "/definitions/"
DATAFILE_TYPE = NERDPUB_PRE + ":DataFile"
CHECKSUMFILE_TYPE = NERDPUB_PRE + ":ChecksumFile"
DOWNLOADABLEFILE_TYPE = NERDPUB_PRE + ":DownloadableFile"
SUBCOLL_TYPE = NERDPUB_PRE + ":Subcollection"
NERDM_CONTEXT = "https://data.nist.gov/od/dm/nerdm-pub-context.jsonld"
DISTSERV = "https://data.nist.gov/od/ds/"
DEF_MERGE_CONV = "midas0"

ARK_NAAN = NIST_ARK_NAAN

class BagBuilder(PreservationSystem):
    """
    A class for building up and populating a BagIt bag compliant with the 
    NIST Profile.

    This class can take a configuration dictionary on construction; the 
    following properties are supported:
    :prop log_filename str ("preserv.log"):  the name to give to the logfile 
                              to embed into the output bag
    :prop bag_log_format str:  a format string used to format the embedded
                              log file.
    :prop id_minter dict ({}):  a set of properties to pass to an IDMinter
                              object upon creation (if a minter is not 
                              provided).
    :prop jq_lib       str:  the full path to the JQ transform library 
                              directory; if not set, the directory is 
                              searched for in a few typical places.
    :prop merge_etc    str:  the full path to directory containing the NERDm
                              merger annotated schemas;  if not set, the 
                              directory is searched for in a few typical places.
    :prop merge_convention str ("dev"): the merge convention name to 
                                 use to merge annotation data into the primary
                                 NERDm metadata.
    :prop validate_id bool (True):  If True, an identifier provided to the 
                              constructor will be checked for transcription
                              error.
    :prop copy_on_link_failure bool (True):  If True, then when moving datafiles 
                              to output bag via a hardlink, then the file 
                              will get copied if the linking fails.  
    :prop file_md_extract dict (None):  a set of parameters to pass to the 
                              configured file metadata extractor.
    :prop json_indent int (4):  The amount of indent to use when exporting JSON
                              data
    :prop ensure_nerdm_type_on_add bool (True):  if True, make sure that the 
                         resource metadata has a recognized value for "_schema".
    :prop distrib_service_baseurl str (https://data.nist.gov/od/ds):  the base
                         URL to use for creating downloadURL property values.
    :prop require_ark_id bool (True):  if True, builder will ensure the resource
                         identifier is set with an ARK identifier (in assign_id())
    :prop extra_tag_dirs list of str (None): a list of other bag tag directories 
                         to create (besides "metadata" and "multibag").
    :prop finalize dict:  a set of properties to configure the finalize_bag()
                              function.  See the finalize_bag() documentation 
                              for the specific properties supported.
    :prop bagit_version str ("1.0"): the version of bagit to claim compliance with
    :prop bagit_encoding str ("UTF-8"):  the text encoding to claim was used to
                              write tag metadata.
    :prop init_bag_info dict:  a set of bag-info properties and values that should 
                              always be included in the bag-info.txt file.
    :prop bag-download-url str:  the base URL to use to record the URL for retrieving
                              the bag from the Distribution Service.  
    :prop validator dict:     a set of properties for configuring the bag validation;
                              see nistoar.pdr.preserv.bagit.validate for details.
    """

    nistprofile = "0.4"

    def __init__(self, parentdir, bagname, config=None, id=None, logger=None):
        """
        create the Builder to build a bag with a given name

        :param parentdir str:  the directory that will contain the bag's root 
                                 directory
        :param bagname str:    the name to give to the bag
        :param config dict:    a dictionary of configuration data (see class
                                 documentation for supported parameters). 
        :param id      str:    the ARK identifier to assign to this record.  If 
                                 None, one will be minted automatically when it
                                 is needed.  
        :param logger Logger:  a Logger object to send messages to.  This will 
                                 used to send messages to a preservation log
                                 inside the bag.  
        """
        if not os.path.exists(parentdir):
            raise StateException("Bag Workspace dir does not exist: " +
                                 parentdir, sys=self)
            
        self._name = bagname
        self._pdir = parentdir
        self._bagdir = os.path.join(self._pdir, self._name)
        self._bag = None

        if not logger:
            logger = log
        self.log = logger
        self.log.setLevel(NORM)
        
        if not config:
            config = {}
        self.cfg = self._merge_def_config(config)

        self._id = None   # set below
        self._ediid = None
        self._logname = self.cfg.get('log_filename', 'preserv.log')
        self._log_handlers = {}
        self._mimetypes = None
        self._distbase = self.cfg.get('distrib_service_baseurl', DISTSERV)
        if not self._distbase.endswith('/'):
            self._distbase += '/'

        jqlib = self.cfg.get('jq_lib', def_jq_libdir)
        self.pod2nrd = PODds2Res(jqlib)

        self._create_defmd_fn = {
            "Resource": self._create_def_res_md,
            "Subcollection": self._create_def_subcoll_md,
            "ChecksumFile": self._create_def_chksum_md,
            "DataFile": self._create_def_datafile_md
        }

        # Note: The bag on disk is not changed in any way (including the
        # creation of the bag directory) in this constructor

        if os.path.exists(self._bagdir):
            if not os.path.isdir(self._bagdir):
                raise StateException("BagBuilder: bag root is not a directory "+
                                     self._bagdir)
            self.ensure_bagdir()  # inits self.bag

        if self.bag and os.path.exists(self.bag.nerd_file_for("")):
            resmd = self.bag.nerd_metadata_for("")
            if resmd.get('@id'):
                self._id = resmd['@id']

        if id and id != self._id:
            if self.bag and os.path.exists(self.bag.metadata_dir):
                self.assign_id(id, keep_conv=True)
            else:
                # delay saving id to metadata
                self._id = self._fix_id(id)

    def __del__(self):
        self._unset_logfile()

    def _merge_def_config(self, config):
        if not def_etc_dir:
            self.log.warning("BagBuilder: Can't load default config: " +
                             "can't find etc directory")
            return config
        defconffile = os.path.join(def_etc_dir, "nist_bagger_conf.yml")
        if not os.path.exists(defconffile):
            self.log.warning("BagBuilder: default config file not found: " +
                             defconffile)
            return config

        defconf = load_from_file(defconffile)
        return merge_config(config, defconf)

    def logfile_is_connected(self, logfile=None):
        # return True if the bagdir/preserv.log is currently attached to this
        # builder
        if not logfile:
            logfile = self._logname
        if not os.path.isabs(logfile):
            logfile = os.path.join(self.bagdir, logfile)
        for hdlr in self.log.handlers:
            if self._handles_logfile(hdlr, logfile):
                return True
        return False

    def _handles_logfile(self, handler, logfilepath):
        # return True if the handler is set to write to a file with the given
        # name
        return hasattr(handler,'stream') and hasattr(handler.stream, 'name') \
               and handler.stream.name == logfilepath

    def _get_log_handler(self, logfilepath):
        if logfilepath not in self._log_handlers:
            self._log_handlers[logfilepath] = None

        hdlr = self._log_handlers[logfilepath]
        if not hdlr:
            hdlr = logging.FileHandler(logfilepath)
            fmt = self.cfg.get('bag_log_format', DEF_BAGLOG_FORMAT)
            hdlr.setFormatter(logging.Formatter(fmt))
            self._log_handlers[logfilepath] = hdlr

        return hdlr

    def connect_logfile(self, logfile=None, loglevel=NORM):
        """
        connect the bag's internal log file to this builder so that it can 
        record what it's doing.  

        :param str logfile:  the path to the log file to connect.  If the 
                             path is relative, it is taken to be relative to 
                             bag's top directory.  If None, the default 
                             (configured) logfile name ("preserv.log") is 
                             assumed.
        """
        if not logfile:
            logfile = self._logname
        if not os.path.isabs(logfile):
            logfile = os.path.join(self.bagdir, logfile)
        if self.logfile_is_connected(logfile):
            return
        hdlr = self._get_log_handler(logfile)
        hdlr.setLevel(loglevel)
        
        self.log.addHandler(hdlr)

    def disconnect_logfile(self, logfile=None):
        """
        disconnect the log file from this builder.  This ensures that the 
        logfile is closed so that the bag can be savely removed, moved, etc.
        It may be reconnected automatically when the builder is called to 
        update the bag.  

        :param str logfile:  the path to the log file to connect.  If the 
                             path is relative, it is taken to be relative to 
                             bag's top directory.  If None, all connected 
                             logfiles will be disconnected.
        """
        if not logfile:
            files = self._log_handlers.keys()
            if not files:
                logfile = os.path.join(self.bagdir, self._logname)
                if logfile not in self._log_handlers:
                    self._log_handlers[logfile] = None

        if not files and isinstance(logfile, str):
            if not os.path.isabs(logfile):
                logfile = os.path.join(self.bagdir, logfile)
            files = [ logfile ]

        self.log.debug("Disconnecting BagBuilder from internal log")

        for lf in files:
            hdlrs = [h for h in self.log.handlers if self._handles_logfile(h,lf)]
            for h in hdlrs:
                self.log.removeHandler(h)
                h.close()
            self._log_handlers[lf] = None
        
    def _set_logfile(self):
        # for backward compatiblity
        self.log.debug("Deprecated _set_logfile() called")
        self.connect_logfile()

    def _unset_logfile(self):
        # for backward compatiblity
        self.disconnect_logfile()
        self.log.debug("Deprecated _unset_logfile() called")

    @property
    def bagname(self):
        return self._name

    @property
    def bagdir(self):
        return self._bagdir

    @property
    def logname(self):
        return self._logname

    @property
    def bag(self):
        """
        a Bag instance providing read-only access to the contents so far of 
        the bag being built.  If None, not enough of the bag has been built 
        to create the view.  
        """
        return self._bag

    @property
    def id(self):
        """
        the identifier for the resource being stored in the bag.  If None, an 
        identifier has not yet been assigned to it.
        """
        return self._id

    @property
    def ediid(self):
        return self._ediid

    @ediid.setter
    def ediid(self, val):
        if val:
            self.record("Setting ediid: " + val)
        elif self._ediid:
            self.record("Unsetting ediid")
        self._ediid = val
        old = self._upd_ediid(val)
        if self._ediid and self._ediid != old:
            self._upd_downloadurl(self._ediid)

    def _upd_ediid(self, ediid):
        # this updates the ediid metadatum in the resource nerdm.json
        old = None
        if self.bag:
            mdfile = self.bag.nerd_file_for("")
            if os.path.exists(mdfile):
                mdata = read_nerd(mdfile)
                old = mdata.get('ediid')
                if old and old != ediid:
                    if ediid:
                        mdata['ediid'] = ediid
                    elif 'ediid' in mdata:
                        del mdata['ediid']
                    self._write_json(mdata, mdfile)
        return old

    def _upd_downloadurl(self, ediid):
        mdtree = os.path.join(self.bagdir, 'metadata')
        if os.path.exists(mdtree):
            for dir, subdirs, files in os.walk(mdtree):
                if FILEMD_FILENAME in files:
                    mdfile = os.path.join(dir, FILEMD_FILENAME)
                    mdata = read_nerd(mdfile)
                    if (DATAFILE_TYPE in mdata.get("@type", []) or \
                        DOWNLOADABLEFILE_TYPE in mdata.get("@type", [])) and \
                       mdata.get('filepath') and             \
                       mdata.get("downloadURL", self._distbase)    \
                            .startswith(self._distbase):
                        if ediid:
                            mdata["downloadURL"] = \
                               self._download_url(ediid, mdata['filepath'])
                                    
                        else:
                            del mdata["downloadURL"]
                        self._write_json(mdata, mdfile)

    def _download_url(self, ediid, destpath):
        path = "/".join(destpath.split(os.sep))
        return self._distbase + ediid + '/' + urlencode(path)

    def assign_id(self, id, keep_conv=False):
        """
        set or update the primary (ARK) identifier for the resource stored in 
        this bag.  Checks are done on the identifier for valid; if the 
        'validate_id' config parameter is set to True, the identifier is 
        is required to comply with "noid" ARK conventions.
        :param str id:  the new identifier.  This can either be a full ark
                        identifier or just the identifier path (with the base
                        URI being assumed).  The actual value assigned will be 
                        a full ARK identifier.
        :param bool keep_conv:  if True, update the existing metadata to 
                        maintain conventions related to the identifier.  
                        (Currently, no such conventions are supported, so this 
                        parameter has no effect; default: False).
        """
        if not id:
            raise ValueError("BagBuilder.assign_id(): id is empty or None")
        self._id = self._fix_id(id)  # may raise validity concerns

        self.ensure_bag_structure()
        md = self.update_metadata_for("", {"@id": self._id},
                                      message="setting resource ID: "+self._id)
        if '@context' in md:
            if not isinstance(md['@context'], list):
                md['@context'] = [ md['@context'], { "@base": self._id } ]
            elif len(md['@context']) < 2:
                md['@context'].append({"@base": self._id})
            else:
                md['@context'][1]['@base'] = self._id
            self.update_metadata_for("", {"@context": md['@context']}, message="")

        # no other metadata conventions requiring consistency with the ID 
        # is currently supported.
        
    def _fix_id(self, id):
        if id is None:
            return None
        
        if self.cfg.get('require_ark_id', True):
            if re.search(r"^/?\d+/", id):
                # id starts with authority number
                id = "ark:/" + id.lstrip('/')
            elif re.search(r"^A[Rr][Kk]:", id):
                id = "ark" + id[3:]
            elif not id.startswith('ark:'):
                # id is just the base path; authority number is needed
                naan = self.cfg.get('id_minter',{}).get('naan', ARK_NAAN)
                id = "ark:/" + naan + "/" + id.lstrip('/')

        if id.startswith("ark:"):
            if not re.match(r"^ark:/\d+/\w", id):
                raise ValueError("Invalid ARK identifier provided: "+id)
            if self.cfg.get('validate_id', True):
                try:
                    noid.validate(id)
                except noid.ValidationError as ex:
                    raise ValueError("Invalid ARK identifier provided: "+
                                     str(ex))
        return id

    def _has_resmd(self):
        if not self.bag:
            return False
        return os.path.exists(self.bag.nerd_file_for(""))

    def rename_bag(self, name):
        """
        rename the bag to the given name.  Note that finalize_bag() will need
        to be (re-)called after calling this method.
        """
        if name == self._name:
            return

        newdir = os.path.join(self._pdir, name)
        if os.path.exists(self._bagdir):
            os.rename(self._bagdir, newdir)

        self._name = name
        self._bagdir = newdir

        if self._bag:
            self._bag = NISTBag(self._bagdir)

    def ensure_bagdir(self):
        """
        ensure that the working bag directory exists with the proper name
        and that we can write to it.  
        """
        didit = False
        if not os.path.exists(self.bagdir):
            try:
                os.mkdir(self.bagdir)
                didit = True
            except OSError, e:
                raise BagWriteError("Unable to create bag directory: "+
                                    self.bagdir+": "+str(e), cause=e, sys=self)

        if not os.access(self.bagdir, os.R_OK|os.W_OK|os.X_OK):
            raise BagWriteError("Insufficient permissions on bag directory: " +
                                self.bagdir, sys=self)

        self.connect_logfile()
        if didit:
            self.record("Created bag with name, %s", self.bagname)
        self._bag = NISTBag(self.bagdir)
        if (not self._id or not self._ediid) and \
           os.path.exists(self._bag.nerd_file_for("")):
            # load the resource-level metadata that's already there
            md = self._bag.nerd_metadata_for("")
            if not self._id:
                self._id = md.get('@id')
            if not self._ediid:
                self._ediid = md.get('ediid')
        
    def ensure_bag_structure(self):
        """
        make sure that the working bag contains the basic directory structure--
        namely, has data and metadata directories.  
        """
        self.ensure_bagdir()

        dirs = [ "data", "metadata" ]
        self._extend_file_list(dirs, 'extra_tag_dirs')

        for dir in dirs:
            dir = os.path.join(self.bagdir, dir)
            if not os.path.exists(dir):
                os.mkdir(dir)

    def _extend_file_list(self, filelist, param):
        extras = self.cfg.get(param)
        if extras:
            if isinstance(extras, (str, unicode)):
                extras = [ extras ]
            if hasattr(extras, '__iter__'):
                bad = [f for f in extras if not isinstance(f, (str, unicode))]
                if bad:
                    self.log.warning("Ignoring entries in config param, "+param+
                                     ", with non-string type: " + str(bad))
                    extras = [f for f in extras if isinstance(f, (str, unicode))]
                filelist.extend(extras)
            else:
                self.log.warning("Ignoring config param, 'extra_tag_dirs': " +
                                 "wrong value type: " + str(extras))

    def ensure_metadata_dirs(self, destpath):
        destpath = os.path.normpath(destpath)
        if os.path.isabs(destpath):
            raise ValueError("data path cannot be absolute: "+destpath)
        if destpath.startswith(".."+os.sep):
            raise ValueError("data path cannot contain ..: "+destpath)

        self._ensure_metadata_dirs(destpath)
        
    def _ensure_metadata_dirs(self, destpath):
        self.ensure_bag_structure()
        path = os.path.join(self.bagdir, "metadata", destpath)
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception, ex:
            pdir = os.path.join(os.path.basename(self.bagdir),
                                "metadata", destpath)
            raise BagWriteError("Failed to create directory tree ({0}): {1}"
                                .format(str(ex), pdir), cause=ex, sys=self)

    def ensure_ansc_collmd(self, destpath):
        """
        ensure that the directories to contain a subcollection with a given 
        path and its metadata exist.

        :param destpath str:   the desired path for the file relative to the 
                               root of the dataset.
        """
        destpath = os.path.normpath(destpath)
        if os.path.isabs(destpath):
            raise ValueError("collection path cannot be absolute: "+destpath)
        if destpath.startswith(".."+os.sep):
            raise ValueError("collection path cannot contain ..: "+destpath)

        collpath = os.path.dirname(destpath)
        self._ensure_metadata_dirs(collpath)

        while collpath != "":
            if not os.path.exists(self.bag.nerd_file_for(collpath)):
                self._define_file_comp_md(collpath, "Subcollection")
            collpath = os.path.dirname(collpath)

    def ensure_datafile_dirs(self, destpath):
        """
        ensure that the directories to contain a data file with a given 
        path and its metadata exist.

        :param destpath str:   the desired path for the file relative to the 
                               root of the dataset.
        """
        destpath = os.path.normpath(destpath)
        if os.path.isabs(destpath) or destpath.startswith(".."+os.sep):
            raise ValueError("ensure_datafile_dirs: destpath cannot be an "
                             "absolute path")

        ddir = os.path.join(self.bagdir, "data")
        if not os.path.exists(ddir):
            self.ensure_bag_structure()

        pdir = os.path.dirname(destpath)
        if pdir:
            path = os.path.join(ddir, pdir)
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
            except Exception, ex:
                pdir = os.path.join(os.path.basename(self.bagdir), "data", pdir)
                raise BagWriteError("Failed to create directory tree ({0}): {1}"
                                     .format(str(ex), pdir), cause=ex, sys=self)

        self.ensure_metadata_dirs(destpath)
        


    
    def define_component(self, destpath, comptype, message=None):
        """
        ensure the definition of a component: if the specified component does 
        not exist, create its metadata entry with default metadata; if it does 
        exist, make sure it has the specified type.

        To later update this component, use update_component_metadata(); to 
        override the current metadata, use replace_component_metadata().  

        When destpath is a hierarchical filepath, this method, as a side effect, 
        will also define all of the anscestor Subcollection components as well,
        if they do not already exist.  This method will also check to make 
        sure that the parent component, if it exists, is of type Subcollection
        before creating the new component.  

        Note that method cannot be used to set resource-level metadata.

        :param str destpath:  the component's filepath (when comptype is 
                              DataFile, Subcollection, or similar downloadable
                              type) or relative identifier (for other types).
        :param str comptype:  the type of component to define; this will control
                              default metadata that is created.  Recognized 
                              values include ["DataFile", "Subcollection",
                              "ChecksumFile"].
        :param str message:   message to record in the bag's log when committing
                              this definition.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        :return dict:  the metadata for the component
        """
        if destpath.startswith("@id:"):
            if comptype == "Resource":
                raise ValueError("Resource: not a component type")
            if comptype in ["DataFile", "ChecksumFile", "Subcollection"]:
                if not destpath.startswith("@id:cmps/"):
                    raise ValueError("incorrect identifier form for " + 
                                     comptype + " component: " + destpath)
                destpath = destpath[len("@id:cmps/"):]
        elif comptype not in self._comp_types:
            raise ValueError(comptype+": not a supported component type (" +
                             str(self._comp_types))

        self.ensure_bagdir()
        if destpath.startswith("@id:"):
            return self._define_nonfile_comp_md(destpath, comptype, message)
        else:
            parent = os.path.dirname(destpath)
            while parent != '':
                if self.bag.comp_exists(parent):
                    if not self.bag.is_subcoll(parent):
                        raise BadBagRequest("Attempt to define file component "+
                                            "below non-Subcollection anscestor")
                    break
                parent = os.path.dirname(parent)

            out = self._define_file_comp_md(destpath, comptype, message)
            self.ensure_ansc_collmd(destpath)
            return out

    def _define_file_comp_md(self, destpath, comptype, msg=None):
        if os.path.exists(self.bag.nerd_file_for(destpath)):
            md = self.bag.nerd_metadata_for(destpath, True)
            if not metadata_matches_type(md, comptype):
                raise StateException("Existing component not a "+comptype+
                                     ": "+str(md.get('@type',[])))
        else:
            if msg is None:
                msg = "Initializing new %s component with default metadata: %s" \
                          % (comptype, destpath)
            md = self._create_init_md_for(destpath, comptype)
            self._replace_file_metadata(destpath, md, msg)

        return md

    def _define_nonfile_comp_md(self, compid, comptype, msg=None):
        if compid.startswith("@id:"):
            compid = compid[len("@id:"):]
        rmd, comps, found = self._fetch_nonfile_comp(compid, comptype)
                
        if found < 0:
            if msg is None:
                msg = "Initializing new %s component with default metadata: %s" \
                          % (comptype, compid)
            if msg:
                self.record(msg)
            md = self._create_init_md_for("@id:"+compid, comptype)
            comps.append(md)
            self.ensure_bag_structure()
            self._write_resmd(rmd)

        return comps[-1]

    def remove_component(self, destpath, trimcolls=False):
        """
        remove a data file or subcollection and all its associated metadata 
        from the bag.  

        Note that it is not an error to attempt to remove a component that 
        does not actually exist in the bag; rather, a warning is written to 
        the log.  

        :param destpath  str:  the root-collection-relative path to the data
                               file
        :parm trimcolls bool:  If True, remove any ancestor subcollections that
                               become empty as a result of the removal.
        :return bool:  True if anything was found and removed.  
        """
        if destpath.startswith("@id:cmps/"):
            destpath = destpath[len("@id:cmps/"):]
        if not destpath:
            raise ValueError("Empty destpath argument (not allowed to remove "
                             "root collection)")
        self.ensure_bag_structure()

        if destpath.startswith("@id:"):
            return self._remove_nonfile_component(destpath)
        else:
            return self._remove_file_component(destpath, trimcolls)

    def _remove_file_component(self, destpath, trimcolls=False):
        # this removes subcollection components as well
        removed = False

        # First look for metadata
        target = os.path.join(self.bag.metadata_dir, destpath)
        if os.path.isdir(target):
            removed = True
            rmtree(target)
        elif os.path.exists(target):
            raise BadBagRequest("Request path does not look like a data "+
                                "component (it's a file in the metadata tree): "+
                                destpath, bagname=self.bagname, sys=self)

        # remove the data file if it exists
        target = os.path.join(self.bag.data_dir, destpath)
        if os.path.isfile(target):
            removed = True
            os.remove(target)
        elif os.path.isdir(target):
            removed = True
            rmtree(target)

        if destpath and trimcolls:
            destpath = os.path.dirname(destpath)

            # is this collection empty?
            if destpath and len(self.bag.subcoll_children(destpath)) == 0:
                if self.remove_component(destpath, trimcolls):
                    removed = True

        if not removed:
            self.log.warning("Data component requested for removal does not exist in bag: %s",
                             destpath)

        return removed

    def _remove_nonfile_component(self, compid):
        if compid.startswith("@id:"):
            compid = compid[len("@id:"):]
        rmd, comps, found = self._fetch_nonfile_comp(compid)

        removed = False
        if found >= 0:
            self.record("Removing non-file component, id="+compid)
            del comps[found]
            removed = True
            self.replace_metadata_for("", rmd, "")

        return removed

    def replace_metadata_for(self, destpath, mdata, message=None):
        """
        Set the given metadata for the component with the given filepath or 
        identifier (for non-file components), overwriting any metadata that 
        may be there already.  Resource-level metadata can be set by providing
        an empty string ("") as the destination path

        Some care should be taken when using this method to set metadata as 
        no checks are made on the validity of this metadata, nor is any merging 
        with defaults done; the given metadata simply replaces any metadata 
        already there.  Thus, it is easy to create a bag that is invalid 
        against the NIST profile.  Instead, clients should prefer methods like
        register_data_file(), update_metadata_for(), and define_component().

        :param  str destpath: the component's filepath (when comptype is 
                              DataFile, Subcollection, or similar downloadable
                              type) or relative identifier (for other types).
        :param dict mdata:    the metadata to write
        :param  str message:  message to record in the bag's log when committing
                              this definition.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        :return dict:  the metadata for the component
        """
        if destpath is None:
            raise ValueError("replace_metadata_for: destpath cannont be None")
        self.ensure_bagdir()

        if destpath.startswith("@id:cmps/"):
            # file-based
            destpath = destpath[len("@id:cmps/"):]
        if destpath.startswith("@id:"):
            return self._replace_nonfile_metadata(destpath, mdata, message)
        else:
            return self._replace_file_metadata(destpath, mdata, message)

    def _replace_file_metadata(self, destpath, mdata, msg=None, outfile=None):
        if not outfile:
            outfile = self.bag.nerd_file_for(destpath)
            
        if msg is None:
            msg = "Setting "
            if os.path.exists(self.bag.nerd_file_for(destpath)):
                msg = "Over-writing "
            if destpath:
                msg += "component metadata: filepath="+destpath
            else:
                msg += "resource-level metadata"

        try:
            self.ensure_metadata_dirs(destpath)
            if msg:
                self.record(msg)
            self._write_json(mdata, outfile)
            self.ensure_ansc_collmd(destpath)
        except Exception, ex:
            self.log.exception("Trouble saving metadata for %s: %s",
                               destpath, str(ex))
            raise

        return mdata
        
    def _replace_nonfile_metadata(self, compid, mdata, msg=None, outfile=None):
        if not outfile:
            outfile = self.bag.nerd_file_for("")

        if compid.startswith("@id:"):
            compid = compid[len("@id:"):]
        if not compid:
            raise BagWriteError("Empty component id provided when writing "+
                                "metadata")    

        self.ensure_bag_structure()

        # look for a non-file component with the same identifier
        comps = []
        found = -1
        if os.path.exists(outfile):
            rmd = read_nerd(outfile)
            comps, found = self._find_nonfile_comp_by_id(rmd, compid)
        else:
            rmd = {'components': comps}    

        try:
            mdata = deepcopy(mdata)
            if '@id' not in mdata:
                mdata['@id'] = compid
            if found >= 0:
                # replace the previously save metadata with the current ID
                if msg is None:
                    msg = "Over-writing metadata for component: id="+compid
                if msg:
                    self.record(msg)
                comps[found] = mdata

            else:
                # add a new component
                if msg is None:
                    msg = "Setting metadata for new component: id="+compid
                if msg:
                    self.record(msg)
                comps.append(mdata)

            self._write_resmd(rmd, outfile)
        except Exception as ex:
            raise BagWriteError("Failed to write metadata for comp id="+compid+
                                str(ex))
        return mdata

    def _find_nonfile_comp_by_id(self, resmd, compid):
        # this finds non-file components; returns the component list and
        # the index of the component with a matching ID
        comps = []
        found = -1 
        try:
            if 'components' in resmd:
                comps = resmd['components']
                for i in range(len(comps)):
                    if '@id' in comps[i] and comps[i]['@id'] == compid:
                        found = i
                        break
        except Exception as ex:
            raise NERDError("Trouble interpreting existing JSON metadata " +
                            "for id="+compid+": "+str(ex))
        return (comps, found)

    def _fetch_nonfile_comp(self, compid, comptype=None):
        # this finds a non-file component with a matcthing ID, returning
        # the base resource metadata node, the components list, and the
        # index of the matching component.
        comps = []
        found = -1
        if self._has_resmd():
            rmd = self.bag.nerd_metadata_for("")
            comps, found = self._find_nonfile_comp_by_id(rmd, compid)
            if comptype and found >= 0 and comps[found] and \
               not metadata_matches_type(comps[found], comptype):
                raise StateException("Existing component not a "+comptype+
                                     ": "+str(comps[found].get('@type',[])))
        else:
            rmd = { "components": comps }

        return (rmd, comps, found)

    def _has_nonfile_comp(self, compid):
        rmd, comps, found = self._fetch_nonfile_comp(compid)
        return found > -1
    
    def _create_init_md_for(self, destpath, comptype):
        if destpath == "":
            return self._create_defmd_fn['Resource']()
        elif comptype in self._create_defmd_fn:
            return self._create_defmd_fn[comptype](destpath)

        if destpath.startswith("@id:") and ':' in comptype:
            # handle an arbitrary non-file component.  comptype must
            # have namespace prefix included
            return {
                "_schema": NERD_DEF + "Component",
                "@context": NERDM_CONTEXT,
                "@id": destpath[len("@id:"):],
                "@type": [ comptype ]
            }

        raise BagWriteError("Unrecognized component type: "+str(comptype))


    def update_metadata_for(self, destpath, mdata, comptype=None, message=None):
        """
        update the metadata for the given component of resource.  
        Resource-level metadata can be updated by providing an empty
        string as the component filepath.  The given metadata will be 
        merged with the currently saved metadata.  If there are no metadata
        yet saved for the filepath, the given metadata will be merged 
        with default metadata.

        When the metadata is merged, note that whole array values will be 
        replaced with corresponding arrays from the input metadata; the 
        arrays are not combined in any way.

        :param str filepath:   the filepath to the component to update.  An
                               empty string ("") updates the resource-level
                               metadata.  If the filepath begins with a '@id:',
                               it will be treated as the relative identifier
                               for the component.
        :param dict   mdata:   the new metadata to merge in
        :param str comptype:   the distribution type to assume for the 
                               component (with the default being "DataFile").  
                               If the component exists and is not of this type,
                               an exception will be raised; if it does not 
                               exist, default metadata based on this type will
                               be created.  
        :param str message:   message to record in the bag's log when committing
                              this definition.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        """
        self.ensure_bag_structure()
        if destpath.startswith("@id:cmps/"):
            # file-based
            destpath = destpath[len("@id:cmps/"):]

        if not comptype and '@type' in mdata:
            comptype = self._determine_comp_type(mdata)

        if destpath.startswith("@id:"):
            # non-file-based component
            return self._update_nonfile_metadata(destpath, mdata, comptype,
                                                 message)
        else:
            return self._update_file_metadata(destpath, mdata, comptype, message)

            
    def _update_nonfile_metadata(self, compid, mdata, comptype, msg=None):
        if compid.startswith("@id:"):
            compid = compid[len("@id:"):]
        self.ensure_bag_structure()

        rmd, comps, found = self._fetch_nonfile_comp(compid, comptype)
        if found < 0:
            # not found; get default data
            if msg is None:
                msg = "Creating new non-file component: id="+compid
            md = self._create_init_md_for("@id:"+compid, comptype)
            comps.append(md)
            found = -1
        elif msg is None:
            msg = "Updating non-file component: id="+compid

        if msg:
            self.record(msg)
        comps[found] = self._update_md(comps[found], mdata)
        self._write_resmd(rmd)

        return comps[found]

    def _update_file_metadata(self, destpath, mdata, comptype, msg=None):
        
        if os.path.exists(self.bag.nerd_file_for(destpath)):
            orig = self.bag.nerd_metadata_for(destpath)
            if comptype and '@type' in orig and \
               not metadata_matches_type(orig, comptype):
                raise StateException("Existing component not a "+comptype+
                                     ": "+str(orig.get('@type',[])))
            if msg is None:
                msg = "Updating %s metadata: %s" % (comptype, destpath)
        else:
            orig = self._create_init_md_for(destpath, comptype)
            if msg is None:
                if not destpath:
                    msg = "Creating new resource-level metadata"
                else:
                    msg = "Creating new %s: %s" % (comptype, destpath)

        mdata = self._update_md(orig, mdata)
        out = self.bag.nerd_file_for(destpath)
        self._replace_file_metadata(destpath, mdata, msg)
        return mdata

    def _update_md(self, orig, updates):
        # update the values of orig with the values in updates
        # this uses the same algorithm as used to merge config data
        return merge_config(updates, orig)

    def replace_annotations_for(self, destpath, mdata, message=None):
        """
        set the given metadata as the annotation metadata for a component of 
        the given path or identifier, overwriting any metadata that may already 
        be there.  Annotation metadata is NERDm metadata that is saved separately
        from the normal metadata and not merged in until the bag is finalized 
        (see class docuemtation for more information).  

        Some care should be taken when using this method to set metadata as 
        no checks are made on the validity of this metadata; thus, it is easy
        to create a bag that is invalid against the NIST profile.  

        :param  str destpath: the component's filepath (when comptype is 
                              DataFile, Subcollection, or similar downloadable
                              type) or relative identifier (for other types).
        :param dict mdata:    the metadata to write
        :param  str message:  message to record in the bag's log when committing
                              this definition.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        :return dict:  the metadata for the component
        """
        if destpath is None:
            raise ValueError("replace_annotations_for: destpath cannont be None")
        self.ensure_bagdir()

        if destpath.startswith("@id:cmps/"):
            # file-based
            destpath = destpath[len("@id:cmps/"):]

        msg = message
        if destpath.startswith("@id:"):
            out = self.bag.annotations_file_for("")
            if msg is None:
                if os.path.exists(out):
                    msg = "Over-writing annotations for component: id="+destpath
                else:
                    msg = "Setting annotations for component: id="+destpath
            return self._replace_nonfile_metadata(destpath, mdata, message, out)

        else:
            out = self.bag.annotations_file_for(destpath)
            if msg is None:
                if os.path.exists(out):
                    msg = "Over-writing annotations for component: filepath="+destpath
                else:
                    msg = "Setting annotations for component: filepath="+destpath
            return self._replace_file_metadata(destpath, mdata, message, out)

        
    def update_annotations_for(self, destpath, mdata, comptype=None,
                               message=None):
        """
        update the annotation metadata for the given component of resource.  
        Annotation metadata is NERDm metadata that is saved separately
        from the normal metadata and not merged in until the bag is finalized 
        (see class docuemtation for more information).  

        Resource-level metadata can be updated by providing an empty string as 
        the component filepath.  The given metadata will be merged with the 
        currently saved annotations.  Note that if destination component does 
        not exist, it will be defined with the minimal default metadata.

        Note that when the given metadata are merged with existing annotations, 
        note that whole array values will be replaced with corresponding arrays 
        from the input metadata; the arrays are not combined in any way.

        :param str filepath:   the filepath to the component to update.  An
                               empty string ("") updates the resource-level
                               metadata.  If the filepath begins with a '@id:',
                               it will be treated as the relative identifier
                               for the component.
        :param dict   mdata:   the new metadata to merge in
        :param str comptype:   the distribution type to assume for the 
                               component (with the default being "DataFile").  
                               If the component exists and is not of this type,
                               an exception will be raised; if it does not 
                               exist, default metadata based on this type will
                               be created.  
        :param str message:   message to record in the bag's log when committing
                              this definition.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        """
        self.ensure_bag_structure()
        if destpath.startswith("@id:cmps/"):
            # file-based
            destpath = destpath[len("@id:cmps/"):]

        if destpath.startswith("@id:"):
            # non-file-based component
            return self._update_nonfile_annotations(destpath, mdata, comptype,
                                                    message)
        else:
            return self._update_file_annotations(destpath, mdata, comptype,
                                                 message)

    def _update_file_annotations(self, destpath, mdata, comptype, message=None):
        if not os.path.exists(self.bag.nerd_file_for(destpath)):
            if not comptype:
                comptype = (destpath and "DataFile") or "Resource"
            self.define_component(destpath, comptype)
        elif comptype:
            orig = self.bag.nerd_metadata_for(destpath)
            if '@type' in orig and not metadata_matches_type(orig, comptype):
                raise StateException("Existing component not a "+comptype+
                                     ": "+str(orig.get('@type',[])))
        self.ensure_bag_structure()

        afile = self.bag.annotations_file_for(destpath)
        if os.path.exists(afile):
            if message is None:
                message = "Updating annoations for " + destpath
            orig = read_nerd(afile)
            mdata = self._update_md(orig, mdata)
        else:
            if message is None:
                message = "Adding annotations for " + \
                          (destpath or "the resource-level")
        return self._replace_file_metadata(destpath, mdata, message, afile)

    def _update_nonfile_annotations(self, compid, mdata,comptype,message=None):
        if compid.startswith("@id:"):
            compid = compid[len("@id:"):]
        self.ensure_bag_structure()

        rmd, comps, found = self._fetch_nonfile_comp(compid, comptype)
        if found < 0:
            if not comptype:
                raise ValueError("No comptype value given; "+
                                 "unable to initialize component, id="+compid)
            self.define_component("@id:"+compid, comptype)
            found = len(comps)

        afile = self.bag.annotations_file_for("")
        comps = []
        found = -1
        if os.path.exists(afile):
            armd = read_nerd(afile)
            comps, found = self._find_nonfile_comp_by_id(armd, compid)
        else:
            armd = { 'components': comps }

        if found < 0:
            comps.append({'@id': compid})
        
        comps[found] = self._update_md(comps[found], mdata)
        self._write_resmd(armd, afile)

        return comps[found]

    def add_data_file(self, destpath, srcpath, register=True, hardlink=False,
                      message=None, comptype=None):
        """
        add a data file into the bag at the given destination path.  Metadata
        will be created for the file unless the register parameter is False.  
        If a file already exists or is otherwise already registered for that 
        destination, the file and associated will be over-written.  

        Metadata is created for the file using the register_data_file() method,
        and by default the file will be examined for extractable metadata.  
        If one wants to avoid having the file examined, register should be set
        to False and register_data_file() should be called separately with 
        examine=False.  

        :param destpath str:   the desired path for the file relative to the 
                               root of the dataset.
        :param scrpath str:    the path to an existing file to copy into the 
                               bag's data directory.
        :param register bool:  If True, create and add metadata for the file.
                               If False, set only minimal metadata (via 
                               define_component()).  
                               Set this to False if the metadata was or will
                               be set separately (e.g. via register_data_file()).
        :param hardlink bool:  If True, attempt to create a hard link to the 
                               file instead of copying it.  For this to be 
                               successful, the bag directory and the srcpath
                               must be on the same filesystem.  A hard copy 
                               will be attempted if linking fails if the 
                               configuration option 'copy_on_link_failure' is
                               not false.
        :param  str message:  message to record in the bag's log when registering
                              the file.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        :param str comptype:   the distribution type to assume for the 
                               component.  If not specified, the type will be
                               discerned by examining the file (defaulting 
                               to "DataFile").  
        """
        if not os.path.exists(srcpath):
            raise BagWriteError("Unable add data file at %s: file not found: %s"
                                % (destpath, srcpath))
        self.ensure_datafile_dirs(destpath)

        action = "Added"
        if os.path.exists(os.path.join(self.bag.data_dir, destpath)):
            action = "Replaced"

        # insert the file into the data directory...
        outfile = os.path.join(self.bag.data_dir, destpath)
        if hardlink:
            # ... as a hard link (faster, saves disk space)
            try:
                if os.path.exists(outfile):
                    os.remove(outfile)
                os.link(srcpath, outfile)
                self.record("%s data file at %s" % (action, destpath))
            except OSError, ex:
                msg = "Unable to create link for data file ("+ destpath + \
                      "): "+ str(ex)
                if self.cfg.get('copy_on_link_failure', True):
                    hardlink = False
                    self.log.warning(msg)
                else:
                    self.log.exception(msg, exc_info=True)
                    raise BagWriteError(msg, sys=self)
        if not hardlink:
            # ... by copying source (hard link is not possible or desired)
            try:
                filecopy(srcpath, outfile)
                self.record("%s data file at %s" % (action, destpath))
            except Exception, ex:
                msg = "Unable to copy data file (" + srcpath + \
                      ") into bag (" + outfile + "): " + str(ex)
                self.log.exception(msg, exc_info=True)
                raise BagWriteError(msg, cause=ex, sys=self)

        # Now set its metadata
        if register:
            self.register_data_file(destpath, srcpath, True, comptype,
                                    "...and updated its metadata.")

    def register_data_file(self, destpath, srcpath=None, examine=True,
                           comptype=None, message=None):
        """
        create and install metadata into the bag for the given file to be 
        added at the given destination path.  The file itself is not actually 
        inserted into the bag (see add_data_file()).  

        :param str destpath:   the desired path for the file relative to the 
                               root of the dataset.
        :param str scrpath:    the path to an existing file that is being 
                               registered.  If not provided, only minimal 
                               metadata will be registered for the file
                               (via define_component()).
        :param bool examine:   If True, examine the file for extractable 
                               metadata.  This includes the checksum.  
        :param  str message:  message to record in the bag's log when registering
                              the file.  A value of None (default) causes 
                              a default message to be recorded.  To suppress a 
                              message, provide an empty string. 
        :param str comptype:   the distribution type to assume for the 
                               component.  If not specified, the type will be
                               discerned by examining the file (defaulting 
                               to "DataFile").  
        """
        # determine the component type
        if not comptype:
            comptype = self._determine_file_comp_type(srcpath or destpath)

        if srcpath:
            mdata = self.describe_data_file(srcpath, destpath, examine, comptype)
        else:
            mdata = self.define_component(destpath, comptype)
            self._add_mediatype(destpath, mdata)
            self.replace_metadata_for(destpath, mdata,'')

        if message is None:
            message = "adding file metadata for "+destpath
        return self.replace_metadata_for(destpath, mdata, message)

    def describe_data_file(self, srcpath, destpath=None, examine=True,
                           comptype=None):
        """
        examine the given file and return a metadata description of it.  

        :param str srcpath:    the full path to the file to examine
        :param str destpath:   the expected destination path under the bag's 
                               data subdirectory; this value will be set as the 
                               'filepath' property.  If None, the source file's
                               base filename will be used.
        :param bool examine:   if False, restrict the examination to determining,
                               the size and format (based on file extension 
                               only) of the file; do not calculate the checksum
                               nor evaluate the contents of the file.
                               A value of True may engage a variety of 
                               configured content evaluators and metadata
                               extractors.  
        :param str comptype:   the distribution type to assume for the 
                               component.  If not specified, the type will be
                               discerned by examining the file (defaulting 
                               to "DataFile").  
        """
        if not destpath:
            destpath = os.path.basename(srcpath)
        
        # determine the component type
        if not comptype:
            comptype = self._determine_file_comp_type(srcpath)
            
        mdata = self._create_init_md_for(destpath, comptype)

        try:
            self._add_file_specs(srcpath, mdata)
            if examine:
                self._add_checksum(checksum_of(srcpath), mdata)
                self._add_extracted_metadata(srcpath, mdata)
        except OSError as ex:
            raise BagWriteError("Unable to examine data file for metadata: "+
                                str(ex), cause=ex)

        return mdata

    def _determine_file_comp_type(self, filename):
        ext = os.path.splitext(filename)[1][1:]
        if ext in ["sha256", "sha512", "md5"]:
            return "ChecksumFile"
        return "DataFile"

    def _determine_comp_type(self, mdata):
        # this tries to figure out the comptype from the given metadata
        if '@type' in mdata:
            if any([':DataFile' in t for t in mdata['@type']]):
                return "DataFile"
            elif any([':ChecksumFile' in t for t in mdata['@type']]):
                return "ChecksumFile"
            elif any([':Subcollection' in t for t in mdata['@type']]):
                return "Subcollection"
            elif any([':PublicDataResource' in t for t in mdata['@type']]):
                return "Resource"
            else:
                return mdata['@type'][0]
        return None
            

    def get_file_specs(self, datafile, checksum=True):
        """
        return the OS file stats metadata in the NERDm model.  This includes the 
        properties 'size', 'mediaType' (based on the file extension), and 
        checksum (when checksum=True).

        :param str datafile:  the path to a file to be inspected for metadata
        :param bool checksum: if True, calculate the file's checksum; otherwise,
                              do not include the checksum.
        """
        out = OrderedDict()
        self._add_file_specs(datafile, out)
        if checksum:
            self._add_checksum(checksum_of(datafile), out)
        return out

    def _add_file_specs(self, datafile, mdata):
        # guess the media type base on the file extension
        self._add_mediatype(datafile, mdata)
        if os.path.exists(datafile):
            self._add_osfile_metadata(datafile, mdata)

    def _add_osfile_metadata(self, dfile, mdata, config=None):
        mdata['size'] = os.stat(dfile).st_size
    def _add_checksum(self, hash, mdata, algorithm='sha256', config=None):
        mdata['checksum'] = {
            'algorithm': { '@type': "Thing", 'tag': algorithm },
            'hash': hash
        }
    def _add_mediatype(self, dfile, mdata, config=None):
        if not self._mimetypes:
            mtfile = pkg_resources.resource_filename('nistoar.pdr',
                                                     'data/mime.types')
            self._mimetypes = build_mime_type_map([mtfile])
        mdata['mediaType'] = self._mimetypes.get(os.path.splitext(dfile)[1][1:],
                                                 'application/octet-stream')

    def _add_extracted_metadata(self, datafile, mdata, config=None):
        # deeper extraction not yet supported.
        pass

    def add_res_nerd(self, mdata, savefilemd=True, message=None):
        """
        write out the resource-level NERDm data into the bag.  

        :param mdata      dict:  the JSON object containing the NERDm Resource 
                                   metadata
        :param savefilemd bool:  if True (default), any DataFile or 
                                   Subcollection metadata will be split off and 
                                   saved in the appropriate locations for 
                                   file metadata.
        :param message     str:  a message to record for the whole operation; this
                                   will suppress messages for updating individual
                                   file metadata (when savefilemd=True) as well as
                                   the resource-level metadata. 
        """
        self.ensure_bag_structure()
        mdata = deepcopy(mdata)

        msg = message
        if msg is None:
            msg = "Adding resourse-level metadata"
        if msg:
            self.record(msg)
        
        # validate type
        if mdata.get("_schema") != NERDM_SCH_ID:
            if self.cfg.get('ensure_nerdm_type_on_add', True):
                raise NERDError("Not a NERDm Resource Record; wrong schema id: "+
                                str(mdata.get("_schema")))
            else:
                self.log.warning("provided NERDm data does not look like a "+
                                 "Resource record")
        
        msg = None
        if message is not None:
            msg = ""
        if "components" in mdata:
            components = mdata['components']
            if not isinstance(components, list):
                raise NERDTypeError("list", str(type(mdata['components'])),
                                    'components')
            for i in range(len(components)-1, -1, -1):
                tps = components[i].get('@type',[])
                comptype = None
                if DATAFILE_TYPE in tps:
                    comptype = "DataFile"
                elif SUBCOLL_TYPE in tps:
                    comptype = "Subcollection"
                elif CHECKSUMFILE_TYPE in tps:
                    comptype = "ChecksumFile"
                elif DOWNLOADABLEFILE_TYPE in tps:
                    comptype = ""
                if comptype is not None:
                    if savefilemd and 'filepath' not in components[i] and \
                       components[i].get('@id','').startswith("cmps/"):
                        components[i]['filepath'] = components[i]['@id'][5:]
                    if savefilemd and 'filepath' not in components[i]:
                        msg = "File component missing 'filepath' property"
                        if '@id' in components[i]:
                            msg += " ({0})".format(components[i]['@id'])
                        self.log.warning(msg)
                    else:
                        if savefilemd:
                            # update instead of replace (this sets defaults
                            # internally)
                            #
                            # # ensure we have default metadata filled out
                            # cmpmd = self._create_init_md_for(
                            #    components[i]['filepath'], comptype)
                            # cmpmd = self._update_md(cmpmd, components[i])
                            # self.replace_metadata_for(cmpmd['filepath'], cmpmd)
                            #
                            self.update_metadata_for(components[i]['filepath'],
                                                     components[i], comptype, msg)
                        components.pop(i)

        if 'inventory' in mdata:
            # we'll recalculate the inventory at the end; for now, get rid of it.
            del mdata['inventory']
        if 'dataHierarchy' in mdata:
            # we'll recalculate the dataHierarchy at the end; for now, get rid
            # of it.
            del mdata['dataHierarchy']
        if 'ediid' in mdata:
            self._ediid = mdata['ediid']
            #
            ## this will trigger updates to DataFile components unless
            ## self.ediid is not set or was already set to new value
            #self.ediid = mdata['ediid']

        defmd = self._create_init_md_for("", "Resource")
        mdata = self._update_md(defmd, mdata)
        # self.replace_metadata_for("", mdata, message="")
        self.update_metadata_for("", mdata, "Resource", message="")

    def add_ds_pod(self, pod, convert=True, savefilemd=True):
        """
        add the dataset-level POD data to the bag.  This will also, by default, 
        be converted to NERD metadata and added as well.  

        :param pod str or dict:  the POD Dataset metadata; if a str, the value
                             is the full pathname to a file containing the JSON
                             data; if it is a dictionary, it is the parsed JSON 
                             metadata.
        :param convert bool: if True, in addition to writing the POD file, it 
                             will be converted to NERDm data and written out 
                             as well.
        :param savefilemd bool:  if True (default) and convert=True, any DataFile
                             or Subcollection metadata will be split off and 
                             saved in the appropriate locations for file 
                             metadata.

        :return dict:  the NERDm-converted metadata or None if convert=False
        """
        if not isinstance(pod, (str, unicode, Mapping)):
            raise NERDTypeError("dict", type(pod), "POD Dataset")
        self.ensure_bag_structure()

        if self.log.isEnabledFor(logging.INFO):
            msg = "Adding POD data"
            if convert:
                msg += " and converting to NERDm"
            self.log.info(msg)

        outfile = os.path.join(self.bagdir, "metadata", POD_FILENAME)
        pdata = None
        if not isinstance(pod, Mapping):
            if convert:
                pdata = read_pod(pod)
            filecopy(pod, outfile)
        else:
            pdata = pod
            self._write_json(pdata, outfile)

        nerd = None
        if convert:
            useid = self.id
            if useid is None:
                useid = ""
                
            nerd = self.pod2nrd.convert_data(pdata, useid)
            if not useid and '@id' in nerd:
                self.log.warning("ARK identifier not set for resource")
                del nerd['@id']
            self.add_res_nerd(nerd, savefilemd)
        return nerd


    def finalize_bag(self, finalcfg=None, stop_logging=False):
        """
        Assume that all needed data and minimal metadata have been added to the
        bag and fill out the remaining bag components to complete the bag.

        When finalcfg (dict) is provided, its properties will be used to control 
        behavior of the bag finalization.  If not provided, the configuration 
        property 'finalize' provided at construction will control finalization.
        The following finalize sub-properties will be recognized:
          :prop 'ensure_component_metadata' bool (True):   if True, this will ensure 
                    that all data files and subcollections have been examined 
                    and had metadata extracted.  
          :prop 'trim_folders' bool (False):  if True, remove all empty data 
                    directories
          :prop 'confirm_checksums' bool (False):  if True, double check that 
                    recorded checksums are correct (by checksumming the data files)

        :param dict finalcfg:      the 'finalize' configuration properties
        :param bool stop_logging:  turn off logging to the bag-internal log file; 
                                   this is useful when finalize_bag() is the last 
                                   call made to this builder.  When True, any 
                                   subsequent updates made with this instance will 
                                   not get recorded in that log.  
        :return list:  a list of errors encountered while trying to complete
                       the bag.  An empty list indicates that the bag is complete
                       and ready to preserved.  
        """
        if finalcfg is None:
            finalcfg = self.cfg.get('finalize', {})

        # Start by trimming the empty data folders
        trim = finalcfg.get('trim_folders', False)
        if trim:
            self.trim_data_folders()

        # Make sure all remaining components have metadata
        if finalcfg.get('ensure_component_metadata', True):
            self.ensure_comp_metadata(updstats=True, extract=False)
        self.ensure_merged_annotations()

        # Now trim empty metadata folders
        if trim:
            self.trim_metadata_folders()

        self.ensure_bagit_ver()
        self.write_data_manifest(finalcfg.get('confirm_checksums', False))
        self.write_mbag_files()
        # write_ore_file
        # write_pidmapping_file
        self.write_about_file()
        # write_premis_file

        self.log.error("Implementation of Bag finalization is not complete!")
        self.log.info("Bag does not include PREMIS and ORE files")
        self.ensure_baginfo()

        if stop_logging:
            self._unset_logfile()
            


    def trim_data_folders(self, rmmeta=False):
        """
        look through the data directory for empty subdirectories and remove 
        them.  This will also eliminate the corresponding metadata folders 
        unless (1) they contain metadata files, AND (2) rmmeta is False.

        :param rmmeta bool:  If False, only purge a corresponding metadata 
                             directory if it contains no metadata.  If True,
                             any metadata for components that do not exist
                             under data nor in the fetch.txt will be removed. 
        """
        # ascend the data directory from leaves to root, looking for empty
        # directories
        droot = os.path.join(self.bagdir, "data")
        mroot = os.path.join(self.bagdir, "metadata")
        for ddir, subdirs, files in os.walk(droot, topdown=False):
            if ddir == droot:
                # don't delete the root "data" directory
                continue
            subdirs = [d for d in subdirs
                         if os.path.exists(os.path.join(ddir, d))]
            if len(files) == 0 and len(subdirs) == 0:
                # the data directory is empty
                try:
                    os.rmdir(ddir)

                    # check the contents of the corresponding metadata dir
                    mdir = os.path.join(mroot, ddir[len(droot)+1:])
                    if os.path.exists(mdir):
                        if os.path.isdir(mdir):
                            # is there anything in the metadata directory?
                            mcont = [os.path.join(mdir, d)
                                     for d in os.listdir(mdir)]

                            # rm metadata directory if it's empty or rmmeta=True
                            if len(mcont) == 0 or rmmeta:
                                rmtree(mdir)

                        else:
                            self.log.error("NIST bag profile error: not a " +
                                           "directory: " +
                                  os.path.join("metadata", ddir[len(droot)+1:]))
                except OSError, ex:
                    self.log.exception("Failed to remove empty data dir: " +
                                       ddir + ": " + str(ex))
                    
    def trim_metadata_folders(self):
        """
        look for empty directories in the metadata tree and remove them.  
        """
        mroot = os.path.join(self.bagdir, "metadata")
        for mdir, subdirs, files in os.walk(mroot, topdown=False):
            subdirs = [d for d in subdirs
                         if os.path.exists(os.path.join(mdir, d))]
            if len(files) == 0 and len(subdirs) == 0:
                # the metadata directory is empty
                try:
                    os.rmdir(mdir)
                except OSError, ex:
                    self.log.exception("Failed to remove empty metadata dir: " +
                                       mdir + ": " + str(ex))

    def ensure_comp_metadata(self, updstats=False, extract=False):
        """
        iterate through all the data files found under the data directory
        and ensure there is metadata describing them.  

        :param bool updstats: if True, re-examine each file for for its 
                              file specs metadata (i.e. size, type, checksum).
                              If False, this metadata will only be set if 
                              is not already set.
        :param bool extract:  if True, examine the file and extract metadata
                              from its contents.  If False, no metadata is 
                              extracted.  
        """
        if not self.bag:
            self.ensure_bagdir()
        for dfile in self.bag.iter_data_files():
            mdfile = self.bag.nerd_file_for(dfile)
            dfpath = os.path.join(self.bag.data_dir, dfile)
            if not os.path.exists(mdfile):
                # no metadata found; start from scratch
                comptype = self._determine_file_comp_type(dfile)
                self.register_data_file(dfile, dfpath, extract, comptype)
                if not extract:
                    # register does not do checksum when examine=False;
                    # get it now
                    md = OrderedDict()
                    self._add_checksum(checksum_of(dfpath), md)
                    self.update_metadata_for(dfile, md,
                                         message="Updating checksum for "+dfile)

            else:
                updcstats = updstats
                md = self.bag.nerd_metadata_for(dfile)
                if 'size' not in md or 'mediaType' not in md or \
                   'checksum' not in md:
                    updcstats = True
                md = None
                if updcstats:
                    md = self.get_file_specs(dfpath, True)

                if extract:
                    if not md:
                        md = OrderedDict()
                    self._add_extracted_metadata(dfpath, md)

                if md:
                    self.update_metadata_for(dfile, md)
                self.ensure_ansc_collmd(dfile)

    def ensure_merged_annotations(self):
        """
        ensure that the annotations have been merged into the primary 
        NERDm metadata.
        """
        # this implementation assumes that merging can be applied multiple
        # times and give the same result.  (It would be better to determine
        # if the annotation's already been applied and not repeat it, for
        # performance reasons.)

        mergeconv = self.cfg.get('merge_convention', DEF_MERGE_CONV)
        self.record("Merging in annotations into all metdata")

        # update the resource-level metadata
        if os.path.exists(self.bag.annotations_file_for("")):
            nerd = self.bag.nerd_metadata_for("", mergeconv)
            self.replace_metadata_for("", nerd, message="")

        # update the file metadata
        for dfile in self._bag.iter_data_components():
            if os.path.exists(self.bag.annotations_file_for(dfile)):
                nerd = self.bag.nerd_metadata_for(dfile, mergeconv)
                self.replace_metadata_for(dfile, nerd, message="")
        
    def ensure_bagit_ver(self):
        """
        ensure that the bag's bagit.txt file exists
        """
        if not os.path.exists(os.path.join(self.bagdir, "bagit.txt")):
            self.write_bagit_ver()

    def write_bagit_ver(self):
        """
        write the bagit.txt file
        """
        self.ensure_bagdir()
        ver = self.cfg.get('bagit_version', "0.97")
        enc = self.cfg.get('bagit_encoding', "UTF-8")

        try: 
            with open(os.path.join(self.bagdir, 'bagit.txt'), 'w') as fd:
                print("BagIt-Version: "+ver, file=fd)
                print("Tag-File-Character-Encoding: "+enc, file=fd)
        except OSError, ex:
            raise BagWriteError("Error writing bagit.txt: "+str(ex), cause=ex)

    def write_data_manifest(self, confirm=False):
        """
        Write the manifest-<algorithm>.txt file based on the data files that 
        are currently in the data directory.  Each datafile must have a 
        corresponding metadata file that contains the correct checksum.  

        :param confirm bool:  if False (default), the checksum found in the
                              data file's metadata will be assumed to be 
                              correct and added to the manifest file.  If 
                              True, the checksum will be calculated to ensure
                              the value in the metadata file is correct.
        """
        # the checksum should not be part of annotations (?).
        # self.ensure_merged_annotations()
        manfile = os.path.join(self.bagdir, "manifest-sha256.txt")
        try:
          with open(manfile, 'w') as fd:
            for datapath in self.bag.iter_data_files():
                md = self.bag.nerd_metadata_for(datapath, merge_annots=False)
                checksum = md.get('checksum')
                if not checksum or 'hash' not in checksum:
                    raise BagProfileError("Missing checksum for datafile: "+
                                          datapath)
                algo = checksum.get('algorithm', {}).get('tag')
                if algo != 'sha256':
                    raise BagProfileError("Unexpected checksum algorithm found: "+
                                          str(algo))
                checksum = checksum['hash']
                if confirm:
                    if checksum_of(self._bag._full_dpath(datapath)) != checksum:
                        raise BagProfileError("Checksum failure for "+datapath)

                self._record_manifest_checksum(fd, checksum,
                                               os.path.join('data', datapath))

        except Exception, e:
            if os.path.exists(manfile):
                os.remove(manfile)
            raise

    def _record_manifest_checksum(self, fd, checksum, filepath):
        fd.write(checksum)
        fd.write(' ')
        fd.write(filepath)
        fd.write('\n')        
                       
    def ensure_baginfo(self, overwrite=False, merge_annots=False):
        """
        ensure that a complete bag-info.txt file is written out to the bag.
        Any data that has already been written out will remain, and any missing
        default information will be added.
        """
        if not self._bag:
            self.ensure_bagdir()

        initdata = deepcopy(self.cfg.get('init_bag_info', OrderedDict()))

        # add items based on bag's contents
        try:
            nerdm = self._bag.nerd_metadata_for("", merge_annots)
        except ComponentNotFound as ex:
            raise BagProfileError("No resource metadata set! Can't set bag "+
                                  "metadata")
        if not nerdm.get('@id'):
            raise BagProfileError("Resource identifier not set! Can't set bag "+
                                  "metadata")
        initdata['Bagging-Date'] = datetime.date.today().isoformat()
        initdata['Bag-Group-Identifier'] = nerdm.get('ediid') or self.ediid
        initdata['Internal-Sender-Identifier'] = self.bagname

        desc = [p for p in nerdm.get('description', []) if len(p.strip()) > 0]
        if desc:
            initdata['External-Description'] = desc
        else:
            initdata['External-Description'] = \
"This collection contains data for the NIST data resource entitled, {0}". \
format(nerdm['title'])

        initdata['External-Identifier'] = [self.id]
        if nerdm.get('doi'):
            initdata['External-Identifier'].append("doi:"+nerdm['doi'])

        # Calculate the payload Oxum
        oxum = self._measure_oxum(self._bag._datadir)
        initdata['Payload-Oxum'] = "{0}.{1}".format(oxum[0], oxum[1])

        # update the multibag version, deprecation
        self.update_head_version(initdata, nerdm.get("version", "1"))

        # write everything except Bag-Size
        self.write_baginfo_data(initdata, overwrite=overwrite)

        # calculate and write the size of the bag 
        oxum = self._measure_oxum(self.bagdir)
        size = self._format_bytes(oxum[0])
        oxum[0] += len("Bag-Size: {0} ".format(size))
        oxum[0] += len("Bag-Oxum: {0}.{1} ".format(oxum[0], oxum[1]))
        size = self._format_bytes(oxum[0])
        szdata = OrderedDict([
            ('Bag-Oxum', "{0}.{1}".format(*oxum)),
            ('Bag-Size', size),
        ])
        self.write_baginfo_data(szdata, overwrite=False)

    def update_head_version(self, baginfo, version):
        """
        update the given bag info metadata with values for 
        'Multibag-Head-Version' and possibly 'Multibag-Head-Deprecates'
        """
        baginfo['Multibag-Head-Version'] = version

        # if there is a multibag/deprecated-info.txt, extract the
        # 'Multibag-Head-Deprecates' values
        #
        multibagdir = baginfo.get('Multibag-Tag-Directory', 'multibag')
        if isinstance(multibagdir, list):
            multibagdir = (len(multibagdir) >0 and multibagdir[-1]) or 'multibag'
        depinfof = os.path.join(self._bag.dir,multibagdir, "deprecated-info.txt")
        
        if os.path.exists(depinfof):
            # indicates that this is an update to a previous version of the
            # dataset.  Add deprecation information.
            
            depinfo = self._bag.get_baginfo(depinfof)

            if 'Multibag-Head-Deprecates' not in baginfo:
                baginfo['Multibag-Head-Deprecates'] = []

            # add the previous head version
            baginfo['Multibag-Head-Deprecates'].extend(
                depinfo.get('Multibag-Head-Version', ["1"]) )

            # add in all the previous deprecated versions
            for val in depinfo.get('Multibag-Head-Deprecates', []):
                if val not in baginfo['Multibag-Head-Deprecates']:
                    baginfo['Multibag-Head-Deprecates'].append( val )
                
            # this file was used to assist when this bag is an update on an
            # earlier version.  We no longer need it, so get rid of it.
            os.remove(depinfof)

    def _measure_oxum(self, rootdir):
        return measure_dir_size(rootdir)

    def _format_bytes(self, nbytes):
        prefs = ["", "k", "M", "G", "T"]
        ordr = 0
        while nbytes >= 1000.0 and ordr < 4:
            nbytes /= 1000.0
            ordr += 1
        pref = prefs[ordr]
        ordr = 0
        while nbytes >= 10.0:
            nbytes /= 10.0
            ordr += 1
        nbytes = str(round(nbytes, 3) * 10**ordr)
        if '.' in nbytes:
            nbytes = re.sub(r"0+$", "", nbytes)
        if nbytes.endswith('.'):
            nbytes = nbytes[:-1]    
        return "{0} {1}B".format(nbytes, pref)

    def write_baginfo_data(self, data, altfile=None, overwrite=False):
        """
        write out specific data to the bag-info.txt file.  Normally, this will
        append the provided data to the file.  Name-value pairs that already 
        exist in the file will not be overwritten.

        :param data dict:  a dictionary (preferably, an OrderedDict) containing
                           the data to add.  
        :param overwrite bool:  if True, any previously written data will be 
                           cleared before writing the new data.  
        """
        if not isinstance(data, Mapping):
            raise TypeError("write_baginfo_data(): Not a dictionary-like " +
                            "object: "+type(data))

        def upd_info(currdata, newdata):
            out = OrderedDict()
            for name, vals in newdata.items():
                out[name] = []
                if isinstance(vals, (str, unicode)) or \
                   not isinstance(vals, Sequence):
                    vals = [vals]
                if name in currdata:
                    for val in vals:
                        if val not in currdata[name]:
                            out[name].append(val)
                else:
                    out[name] = vals
            return out

        if not self._bag:
            self.ensure_bagdir()
        if not overwrite:
            data = upd_info(self._bag.get_baginfo(altfile), data)
        self._write_baginfo_data(data, altfile, overwrite)

    def _write_baginfo_data(self, data, infofile=None, overwrite=False):
        mode = 'w'
        if not overwrite:
            mode = 'a'

        if not infofile:
            infofile = os.path.join(self.bagdir, "bag-info.txt")
        with open(infofile, mode) as fd:
            for name, vals in data.items():
                if isinstance(vals, (str, unicode)) or \
                   not isinstance(vals, Sequence):
                    vals = [vals]
                for val in vals:
                    out = "{0}: {1}".format(name, val.encode('utf-8'))
                    if len(out) > 79:
                        out = textwrap.fill(out, 79, subsequent_indent=' ')
                    print(out, file=fd)

    def write_mbag_files(self, overwrite=False):
        """
        write out tag files for the MultiBag BagIt profile.  
        """
        self.ensure_bagit_ver()

        # Use the head bag interface provided by the external multibag package
        # Note that previously saved data (i.e. cached from previously
        # published version) will be retained.
        hbag = open_headbag(self.bagdir)

        # append the bag we're building to the member bag list and save
        url = self.cfg.get('bag-download-url')
        if url:
            if not url.endswith('/'):
                url += '/'
            url += self.bagname
        hbag.add_member_bag(self.bagname, url)
        hbag.save_member_bags()

        # update the file lookup with the contents of this new bag
        for dir, sdirs, files in os.walk(self._bag.data_dir):
            dir = dir[len(self.bagdir)+1:]
            for f in files:
                f = os.path.join(dir, f)
                f = "/".join(f.split(os.sep))
                hbag.add_file_lookup(f, self.bagname)
        for dir, sdirs, files in os.walk(self._bag.metadata_dir):
            dir = dir[len(self.bagdir)+1:]
            for f in files:
                f = os.path.join(dir, f)
                f = "/".join(f.split(os.sep))
                hbag.add_file_lookup(f, self.bagname)
        for f in "preserv.log ore.txt premis.xml".split():
            if hbag.exists(f):
                hbag.add_file_lookup(f, self.bagname)
        hbag.save_file_lookup()
        
    def write_about_file(self, merge_annots=False):
        """
        Write out the about.txt file.  This requires that the resource-level
        metdadata has been written out; if it hasn't, a BagProfileError is 
        raised.  The metadata annotations should be merged as well (i.e. via
        ensure_merged_annotations()); however, if they have not yet been, 
        the merge_annots parameter can be set to True.

        :param merge_annots bool:  if True, base the about file contents on 
                                   metadata that includes annotations merged 
                                   in.  (Setting to True, does not permanently
                                   merge annotations.)  Default: False.
        """
        if not self._bag:
            self.ensure_bagdir()
        nerdresf = self._bag.nerd_file_for("")
        podf = self._bag.pod_file()
        if not os.path.exists(podf):
            raise BagProfileError("Missing POD metadata file; is this bag complete?")
        if not os.path.exists(nerdresf):
            raise BagProfileError("Missing POD metadata file; is this bag complete?")
        try:
            mf = nerdresf
            nerdm = self._bag.nerd_metadata_for("", merge_annots)
            mf = podf
            podm = self._bag.read_pod(mf)
        except OSError, ex:
            raise BagItException("failed to read data from file, " +
                                 mf + ": " + str(ex), cause=ex)

        try:
            ec = 'utf-8'
            with open(os.path.join(self.bagdir, "about.txt"), 'w') as fd:
                print("This data package contain NIST Public Data\n", file=fd)

                # title
                print(textwrap.fill(podm['title'].encode(ec), 79), file=fd)

                # authors, if available
                if 'authors' in nerdm:
                    auths = []
                    affils = []
                    for auth in nerdm['authors']:
                        if auth.get('fn'):
                            aus = auth['fn']
                        else:
                            aus = " ".join([ auth.get('givenName',''),
                                            auth.get('middleName', ''),
                                            auth.get('familyName', '') ]).strip()
                        if aus and auth.get('affiliation'):
                            try:
                                whichaffil = affils.index(auth['affiliation'])+1
                            except ValueError:
                                affils.append(auth['affiliation'])
                                whichaffil = len(affils)

                            # using = as a non-breakable space here, see sub()
                            # below.
                            aus += "=[{0}]".format(whichaffil)

                        auths.append(aus)

                    if len(auths) > 0:
                        if len(auths) == 1:
                            aus = auths[0]
                        elif len(auths) == 2:
                            aus = auths[0] + " and " + auths[1]
                        else:
                            aus = " ".join(auths[:-1]) + ", and " + auths[-1]
                        print( re.sub(r'=', ' ', textwrap.fill(aus.encode(ec))),
                               file=fd )

                        i=1
                        for affil in affils:
                           print(textwrap.fill("[{0}] {1}".format(i, affil)
                                                          .encode(ec)), file=fd)

                # identifier(s)
                if nerdm.get('doi'):
                    print("Identifier: doi:{0} ({1})".format(nerdm['doi'],
                                                             nerdm['@id']),
                          file=fd)
                else:
                    print("Identifier: {0}".format(nerdm['@id']), file=fd)
                fd.write('\n')

                # contact
                if 'contactPoint' in nerdm:
                    cp = nerdm['contactPoint']
                    if cp.get('fn') and cp.get('hasEmail'):
                        aus = re.sub('^mailto:\s*', '', cp['hasEmail'])
                        print("Contact: {0} ({1})".format(cp['fn'], aus)
                                                  .encode(ec), file=fd)
                    else:
                        print("Contact: {0}".format(cp.get('fn') or
                                                    cp.get('hasEmail')),
                              file=fd)
                    if 'postalAddress' in cp:
                        for line in cp['postalAddress']:
                            print("         {0}".format(line.strip()).encode(ec),
                                  file=fd)
                    if 'phoneNumber' in cp:
                        print("         Phone: {0}".format(
                                          cp['phoneNumber'].strip()).encode(ec),
                              file=fd)
                    fd.write("\n")

                # description
                if podm.get('description'):
                    print( textwrap.fill(podm['description'].encode(ec)),
                           file=fd )
                    fd.write("\n")

                # landing page
                if nerdm.get('doi'):
                    print("More information:\nhttps://doi.org/" +
                          nerdm.get('doi'), file=fd)
                elif nerdm.get('landingPage'):
                    print("More information:\n" +
                          nerdm.get('landingPage').encode(ec),
                          file=fd)
                
        except OSError, ex:
            raise BagWriteError("Problem writing about.txt file: " + str(ex),
                                cause=ex)

    

    def __del__(self):
        self._unset_logfile()

    def validate(self, config=None):
        """
        Determine if the bag is complete and compliant with the NIST BagIt
        profile.

        :param config dict:  a configuration to pass to the validator; see 
                             nistoar.pdr.preserv.bagit.validate for details.
                             If not provided, the configuration for this 
                             builder will be checked for the 'validator' 
                             property to use as the configuration.
                             
        :return ValidationResults:  a 
                             nistoar.pdr.preserv.bagit.validate.ValidationResults
                             instance containing the lists of errors, warnings, 
                             or recommendations resulting. 
        """
        if not self._bag:
            raise BagItException("Bag directory for id=" + self._name +
                                 "has not been created.")
        if config is None:
            self.cfg.get('validator', {})
        vld8r = NISTAIPValidator(config)
        return vld8r.validate(self._bag)

    def record(self, msg, *args, **kwargs):
        """
        record a message in the bag's preservation log indicating a relevent 
        change made to this bag.
        """
        self.log.log(NORM, msg, *args, **kwargs)

    _comp_types = {
        "DataFile": [
            [ ":".join([NERDPUB_PRE, "DataFile"]),
              ":".join([NERDPUB_PRE, "DownloadableFile"]),
              "dcat:Distribution" ],
            [ NERDPUB_DEF + "DataFile" ]
        ],
        "ChecksumFile": [
            [ ":".join([NERDPUB_PRE, "ChecksumFile"]),
              ":".join([NERDPUB_PRE, "DownloadableFile"]),
              "dcat:Distribution" ],
            [ NERDPUB_DEF + "ChecksumFile" ]
        ],
        "Subcollection": [
            [ ":".join([NERDPUB_PRE, "Subcollection"]) ],
            [ NERDPUB_DEF + "Subcollection" ]
        ],
        "Resource": [
            [ ":".join([NERDPUB_PRE, "PublicDataResource"]) ],
            [ NERDPUB_DEF + "PublicDataResource" ]
        ]
    }
    _checksum_alg_names = { "sha256": "SHA-256" }

    def _create_def_datafile_md(self, destpath):
        if destpath.startswith("@id:"):
            if not destpath.startswith("@id:cmps/"):
                raise ValueError("incorrect identifier form for DataFile " +
                                 "component: " + destpath)
            destpath = destpath[len("@id:cmps/"):]
        destpath = destpath.strip('/')
                
        out = OrderedDict([
            ("_schema", NERD_DEF + "Component"),
            ("@context", NERDM_CONTEXT),
            ("@id", "cmps/" + urlencode(destpath)),
            ("@type", deepcopy(self._comp_types["DataFile"][0]))
        ])
        out["_extensionSchemas"] = deepcopy(self._comp_types["DataFile"][1])
        out["filepath"] = destpath
        if self.ediid:
            out['downloadURL'] = self._download_url(self.ediid, destpath)
        return out

    def _create_def_chksum_md(self, destpath):
        if destpath.startswith("@id:"):
            if not destpath.startswith("@id:cmps/"):
                raise ValueError("incorrect identifier form for ChecksumFile " +
                                 "component: " + destpath)
            destpath = destpath[len("@id:cmps/"):]
                
        out = OrderedDict([
            ("_schema", NERD_DEF + "Component"),
            ("@context", NERDM_CONTEXT),
            ("@id", "cmps/" + urlencode(destpath)),
            ("@type", deepcopy(self._comp_types["ChecksumFile"][0])),
            ("filepath", destpath)
        ])
        if self.ediid:
            out['downloadURL'] = self._download_url(self.ediid, destpath)

        fname = os.path.splitext(destpath)
        if fname[1] and fname[1][1:] in self._checksum_alg_names:
            out['algorithm'] = { "@type": "Thing", "tag": fname[1][1:] }
            out['describes'] = "cmps/" + fname[0]
            out['description'] = "checksum value for " + os.path.basename(fname[0])
            out['description'] = self._checksum_alg_names[fname[1][1:]] + \
                                 ' ' + out['description']

        out["_extensionSchemas"] = deepcopy(self._comp_types["ChecksumFile"][1])
        return out

    def _create_def_subcoll_md(self, destpath):
        if destpath.startswith("@id:"):
            if not destpath.startswith("@id:cmps/"):
                raise ValueError("incorrect identifier form for Subcollection " +
                                 "component: " + destpath)
            destpath = destpath[len("@id:cmps/"):]
        destpath = destpath.strip('/')
                
        out = OrderedDict([
            ("_schema", NERD_DEF + "Component"),
            ("@context", NERDM_CONTEXT),
            ("@id", "cmps/" + urlencode(destpath)),
            ("@type", deepcopy(self._comp_types["Subcollection"][0])),
            ("_extensionSchemas", deepcopy(self._comp_types["Subcollection"][1])),
            ("filepath", destpath)
        ])
        return out
    
    def _create_def_res_md(self, destpath="ignored"):
        out = OrderedDict([
            ("_schema", NERDM_SCH_ID),
            ("@context", NERDM_CONTEXT),
            ("@type", deepcopy(self._comp_types["Resource"][0])),
            ("_extensionSchemas", deepcopy(self._comp_types["Resource"][1]))
        ])
        return out
    
    def _write_json(self, jsdata, destfile):
        indent = self.cfg.get('json_indent', 4)
        write_json(jsdata, destfile, indent)

    def _write_resmd(self, resmd, destfile=None):
        # Coming: control the order that JSON properties are written
        if not destfile:
            destfile = self.bag.nerd_file_for("")
        self._write_json(resmd, destfile)


def metadata_matches_type(mdata, nodetype):
    """
    Return True if the given request type can be matched against any of the 
    types assigned to given metadata.
    """
    if '@type' not in mdata:
        return False

    types = mdata['@type']
    return matches_type(types, nodetype)

def matches_type(types, nodetype):
    if nodetype == "Resource":
        nodetype = "PublicDataResource"

    if ':' not in nodetype:
        basere = re.compile(r'^[^:]*:')
        types = [basere.sub('', t) for t in types]

    return any([t == nodetype for t in types])
