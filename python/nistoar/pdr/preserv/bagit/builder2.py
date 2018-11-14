"""
Tools for building a NIST Preservation bags
"""
from __future__ import print_function, absolute_import
from __future__ import print_function, absolute_import
import os, errno, logging, re, json, pkg_resources, textwrap, datetime
import pynoid as noid
from shutil import copy as filecopy, rmtree
from copy import deepcopy
from collections import Mapping, Sequence, OrderedDict
from urllib import quote as urlencode

from .. import PreservationSystem
from .. import ConfigurationException, StateException, PODError
from .exceptions import BagProfileError, BagWriteError, BadBagRequest
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
    """

    nistprofile = "0.4"

    def __init__(self, parentdir, bagname, config=None, id=None, minter=None,
                 logger=None):
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
        :param minter IDMinter: an IDMinter to use to mint a new identifier to 
                                 assign to this resource.  
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
        
        if not config:
            config = {}
        self.cfg = self._merge_def_config(config)

        self._id = None   # set below
        self._ediid = None
        self._logname = self.cfg.get('log_filename', 'preserv.log')
        self._loghdlr = None

        self._minter = None
        if minter:
            self._minter = minter
        
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

        if id:
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

    def _get_minter(self):
        # lazy instantiation of a minter
        if not self._minter:
            mcfg = self.cfg.get('id_minter', {})
            self._minter = PDRMinter(self._pdir, cfg)
            if not os.path.exists(minter.registry.store):
                self.log.warning("Creating new ID minter for bag, "+self.bagname)
        return self._minter

    def _set_logfile(self):
        if self._loghdlr:
            self._unset_logfile()
        filepath = os.path.join(self.bagdir, self.logname)
        self._loghdlr = logging.FileHandler(filepath)
        self._loghdlr.setLevel(NORM)
        fmt = self.cfg.get('bag_log_format', DEF_BAGLOG_FORMAT)
        self._loghdlr.setFormatter(logging.Formatter(fmt))
        self.log.addHandler(self._loghdlr)
        if not self.log.isEnabledFor(NORM):
            self.log.setLevel(NORM)

    def _unset_logfile(self):
        if hasattr(self, '_loghdlr') and self._loghdlr:
            self.log.removeHandler(self._loghdlr)
            self._loghdlr.close()
            self._loghdlr = None

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
    def id(self):
        """
        the identifier for the resource being stored in the bag.  If None, an 
        identifier has not yet been assigned to it.
        """
        return self._id

    @property
    def ediid(self):
        return self._ediid

    @property
    def bag(self):
        """
        a Bag instance providing read-only access to the contents so far of 
        the bag being built.  If None, not enough of the bag has been built 
        to create the view.  
        """
        return self._bag

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
        self.update_metadata_for("", {"@id": self._id})

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

        if not self._loghdlr:
            self._set_logfile()
        if didit:
            self.record("Created bag with name, %s", self.bagname)
        self._bag = NISTBag(self.bagdir)
        if os.path.exists(self._bag.nerd_file_for("")):
            # load the resource-level metadata that's already there
            md = self._bag.nerd_metadata_for("")
            self._id = md.get('@id')
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
            if not metadata_matches_type(comptype):
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

    def replace_metadata_for(self, destpath, mdata, message=None):
        """
        Set the given metadata for the component with the given filepath or 
        identifier (for non-file components), overwriting any metadata that 
        may be there already.  This method cannot be used to set/replace the 
        resource-level metadata: a destpath="" will raise an exception

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
        if not destpath:
            raise BadBagRequest("Cannot set resource metadata with "+
                                "replace_metadata_for()")
        self.ensure_bagdir()

        if destpath.startswith("@id:cmps/"):
            # file-based
            destpath = destpath[len("@id:cmps/"):]
        if destpath.startswith("@id:"):
            return self._replace_nonfile_metadata(destpath, mdata, message)
        else:
            return self._replace_file_metadata(destpath, mdata, message)

    def _replace_file_metadata(self, destpath, mdata, msg=None):
        if msg is None:
            if os.path.exists(self.bag.nerd_file_for(destpath)):
                msg = "Over-writing metadata for component: filepath="+destpath
            else:
                msg = "Setting metadata for new component: filepath="+destpath

        try:
            self.ensure_metadata_dirs(destpath)
            self.record(msg)
            self._write_json(mdata, self.bag.nerd_file_for(destpath))
            self.ensure_ansc_collmd(destpath)
        except Exception, ex:
            self.log.exception("Trouble saving metadata for %s: %s",
                               destpath, str(ex))
            raise

        return mdata
        
    def _replace_nonfile_metadata(self, compid, mdata, msg=None):
        if compid.startswith("@id:"):
            compid = compid[len("@id:"):]
        if not compid:
            raise BagWriteError("Empty component id provided when writing "+
                                "metadata")    

        self.ensure_bag_structure()

        # look for a non-file component with the same identifier
        comps = []
        found = -1
        if self._has_resmd():
            rmd = self.bag.nerd_metadata_for("")
            comps, found = self._find_nonfile_comp_by_id(rmd, compid)
        else:
            rmd = {'components': comps}    

        try:
            mdata = deepcopy(mdata)
            if '@id' not in compid:
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

            self._write_resmd(rmd)
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

        raise BagWriteError("Unrecognized component type: "+comptype)


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
                msg = "Creating new %s: %s" % (comptype, destpath)

        mdata = self._update_md(orig, mdata)
        self._replace_file_metadata(destpath, mdata, msg)
        return mdata

    def _update_md(self, orig, updates):
        # update the values of orig with the values in updates
        # this uses the same algorithm as used to merge config data
        return merge_config(updates, orig)


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
                
        out = {
            "_schema": NERD_DEF + "Component",
            "@context": NERDM_CONTEXT,
            "@id": "cmps/" + urlencode(destpath),
            "@type": deepcopy(self._comp_types["DataFile"][0]),
            "filepath": destpath,
        }
        if self.ediid:
            out['downloadURL'] = self._download_url(self.ediid, destpath)
        out["_extensionSchemas"] = deepcopy(self._comp_types["DataFile"][1])
        return out

    def _create_def_chksum_md(self, destpath):
        if destpath.startswith("@id:"):
            if not destpath.startswith("@id:cmps/"):
                raise ValueError("incorrect identifier form for ChecksumFile " +
                                 "component: " + destpath)
            destpath = destpath[len("@id:cmps/"):]
                
        out = {
            "_schema": NERD_DEF + "Component",
            "@context": NERDM_CONTEXT,
            "@id": "cmps/" + urlencode(destpath),
            "@type": deepcopy(self._comp_types["ChecksumFile"][0]),
            "filepath": destpath,
        }
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
                
        out = {
            "_schema": NERD_DEF + "Component",
            "@context": NERDM_CONTEXT,
            "@id": "cmps/" + urlencode(destpath),
            "@type": deepcopy(self._comp_types["Subcollection"][0]),
            "filepath": destpath,
            "_extensionSchemas": deepcopy(self._comp_types["Subcollection"][1])
        }
        return out
    
    def _create_def_res_md(self, destpath="ignored"):
        out = {
            "_schema": NERDM_SCH_ID,
            "@context": NERDM_CONTEXT,
            "@type": deepcopy(self._comp_types["Resource"][0]),
            "_extensionSchemas": deepcopy(self._comp_types["Resource"][1])
        }
        return out
    
    def _write_json(self, jsdata, destfile):
        indent = self.cfg.get('json_indent', 4)
        write_json(jsdata, destfile, indent)

    def _write_resmd(self, resmd):
        # Coming: control the order that JSON properties are written
        self._write_json(resmd, self.bag.nerd_file_for(""))


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
    if ':' not in nodetype:
        basere = re.compile(r'^[^:]*:')
        types = [basere.sub('', t) for t in types]

    return any([t == nodetype for t in types])
