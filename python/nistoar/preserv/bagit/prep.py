"""
This module handles preparing a dataset by organizing it into the NIST 
BagIt structure and initializing key data (including initial NERDm data).

The PreppedValidater checks to see that if the directory is properly 
structured, and the Prepper class does the reorganization as necessary.  

"""

import os, errno, logging, re, json
from shutil import copy2 as copy
from abc import ABCMeta, abstractmethod, abstractproperty

from ..validate import SIPValidater, SimpleAssessment
from ..exceptions import (SIPDirectoryError, SIPDirectoryNotFound, NERDError,
                          ConfigurationException, StateException, PODError)

log = logging.getLogger(__name__)

DEF_MBAG_VERSION = "0.2"
MIDAS_POD_FILE = "_pod.json"
AIP_POD_FILE = "metadata/pod.json"

class SIPPrepper(object):
    """
    This class will prepare an SIP organized in a particular form 
    by re-organizing its contents into a working bag.  Subclasses adapt 
    different SIP format.  This abstract class provides common code.  

    SIPPrepper implementations should be written to be indepodent: running 
    it mutliple times on the same input and output directories should result
    in the same end state.  That is, if run a second time and nothing is 
    different in the input directory, nothing changes in the output directory.
    If a file is added in the input directory and the prepper is rerun, that
    new file will get added to the output directory.  

    Note that user-provided datafiles are added to the output directory as a 
    hard link.  That is, no bytes are copied.  Metadata data files are copied.
    """
    __metaclass__ = ABCMeta

    def __init__(self, indir, outdir, config):
        """
        initialize the class by setting the input SIP directory and the 
        output working directory where the root bag directory can be created.  
        """
        self.sipdir = indir
        self.bagparent = outdir
        self.cfg = config
        self.poddata = None
        self.dsid = None
        self.bagdir = None

        # ensure we have a readable directory
        if not self.sipdir:
            raise ValueError("DirStructureValidator: No input directory "
                             "provided")
        if not os.path.exists(self.sipdir):
            raise SIPDirectoryNotFound(indir)
        if not os.path.isdir(self.sipdir):
            raise SIPDirectoryError(indir, "not a directory")
        if not os.access(self.sipdir, os.R_OK|os.X_OK):
            raise SIPDirectoryError(indir, "lacking read/cd permission")

        # do a sanity check on the bag parent directory
        if not self.cfg.get('relative_to_indir', False):
            sipdir = os.path.abspath(self.sipdir)
            if sipdir[-1] != os.sep:
                sipdir += '/'
            if os.path.abspath(self.bagparent).startswith(sipdir):
                if self.cfg.get('relative_to_indir') == False:
                    # you said it was not relative, but it sure looks that way
                    raise ConfigurationException("'relative_to_indir'=False but"
                                                 +" bag dir (" + self.bagparent+
                                                 ") appears to be below "+
                                                 "submitted directory (" +
                                                 self.sipdir+")")
                # bagparent is inside sipdir
                self.bagparent = os.path.abspath(self.bagparent)[len(sipdir):]
                self.cfg['relative_to_indir'] = True

        if self.cfg.get('relative_to_indir'):
            self.bagparent = os.path.join(self.sipdir, self.bagparent)

    def ensure_bag_parent_dir(self):
        if not os.path.exists(self.bagparent):
            if self.cfg.get('relative_to_indir'):
                try:
                    os.makedirs(self.bagparent)
                except OSError, e:
                    bagparent = self.bagparent[len(self.sipdir):]
                    raise SIPDirectoryError("unable to create working bag ("+
                                            bagparent + ") under SIP "+
                                            "dir: " + str(e), cause=e)
            else:
                raise StateException("Bag Workspace dir does not exist: " +
                                     self.bagparent)

    @abstractmethod
    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """
        raise NotImplemented

    @abstractmethod
    def ensure_preparation(self):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP directory, ready for annotation 
        and preservation.  
        """
        raise NotImplemented

    def form_bagdir_name(self, dsid):
        """
        return the name to use for the working bag directory
        """
        fmt = self.cfg.get('bag_name_format', "{0}.mbag{1}-{2}")
        bseq = self.cfg.get('mbag_seqno', 1)
        bver = self.cfg.get('mbag_version', DEF_MBAG_VERSION)
        bver = re.sub(r'\.', '_', bver)
        return fmt.format(dsid, bver, bseq)

    def read_pod(self, podfile):
        try:
            with open(podfile) as fd:
                return json.load(fd)
        except IOError, ex:
            raise PODError("Unable to read POD file: "+str(ex), src=podfile)

    def read_nerd(self, nerdfile):
        try:
            with open(nerdfile) as fd:
                return json.load(fd)
        except IOError, ex:
            raise PODError("Unable to read NERD file: "+str(ex), src=nerdfile)

    def set_bagdir(self):
        podfile = os.path.join(self.sipdir, self.find_pod_file())
        self.poddata = self.read_pod(podfile)
        try: 
            self.dsid = self.poddata['identifier']
        except KeyError, ex:
            raise PODError("Missing identifier field", src=podfile)
        self.bagdir = os.path.join(self.bagparent,
                                   self.form_bagdir_name(self.dsid))

    def ensure_bagdir(self):
        """
        ensure that the working bag directory exists with the proper name
        an that we can write to it.  
        """
        if not self.bagdir:
            self.set_bagdir()

        if not os.path.exists(self.bagdir):
            self.ensure_bag_parent_dir()
            try:
                os.mkdir(self.bagdir)
            except OSError, e:
                raise StateException("Unable to create working bag directory: "+
                                     self.bagdir+": "+str(e), cause=e)

        if not os.access(self.bagdir, os.R_OK|os.W_OK|os.X_OK):
            raise StateException("Insufficient permissions on bag directory: " +
                                 self.bagdir)

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
                    log.warn("Ignoring entries in config param, "+param+
                             ", with non-string type: " + str(bad))
                    extras = [f for f in extras if isinstance(f, (str, unicode))]
                filelist.extend(extras)
            else:
                log.warn("Ignoring config param, 'extra_tag_dirs': " +
                         "wrong value type: " + str(extras))

    def ensure_data_file(self, inpath):
        """
        create a hard link to a data file in output working bag directory.
        A data file is a file provided by the dataset's author (as opposed 
        to a metadata file, like a POD file).

        :param inpath  str:  the path to the data file relative to the base
                             SIP directory.
        """
        self.ensure_bagdir()
        outfile = os.path.join(self.bagdir, 'data', inpath)
        infile = os.path.join(self.sipdir, inpath)
        if not os.path.exists(infile) or not os.path.isfile(infile):
            raise ValueError("Not an existing file: "+inpath)
        
        if not os.path.exists(outfile):
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            os.link(infile, outfile)
            
        elif os.stat(infile).st_mtime > os.stat(outfile).st_mtime:
            # this extra check is in case the file was copied here or otherwise
            # does not match the input file (based on its modification time)
            if not self.cfg.get('ignore_rm_copy_warning'):
                log.warn("Updating apparent copy of data file: "+inpath)
            os.remove(outfile)
            os.link(infile, outfile)

    def ensure_metadata_file(self, inpath, outpath, allow_update=True):
        """
        create a hard line to a data file in output working bag directory.
        A data file is a file provided by the dataset's author (as opposed 
        to a metadata file, like a POD file).  Note that the file's metadata
        (i.e. creation, mod times, etc) are copied as well.

        :param inpath  str:  the path to the metadadata file relative to the base
                             SIP directory.
        :param outpath str:  the path to copy the file to in the working bag
                             directory
        """
        self.ensure_bagdir()
        outfile = os.path.join(self.bagdir, outpath)
        infile = os.path.join(self.sipdir, inpath)
        
        if not os.path.exists(outfile):
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            copy(infile, outfile)
            
        elif allow_update and \
             os.stat(infile).st_mtime > os.stat(outfile).st_mtime:
            if not self.cfg.get('ignore_rm_copy_warning'):
                log.warn("Updating apparent copy of metadata file: "+inpath)
            os.remove(outfile)
            copy(infile, outfile)

    def list_submitted_files(self):
        """
        return a list of all files that are part of the submission.  This 
        implementation simply returns a deep list of plain files as paths 
        relative to the base SIP directory.  Directories are not included.

        This returns a list generator, intended to be iterated on.  
        """
        start = re.compile(self.sipdir+r'/?')
        for root, dirs, files in os.walk(self.sipdir):
            root = start.sub('', root)

            for file in files:
                if file.startswith('.'):
                    log.warn("Skipping hidden file in SIP: " +
                             os.path.join(root,file))
                    continue
                yield os.path.join(root,file)

            hidden = [d for d in enumerate(dirs) if d[1].startswith('.')]
            if hidden:
                for h in reversed(hidden):
                    log.warn("Skipping hidden directory in SIP: " +
                             os.path.join(root, h[1]))
                    del dirs[h[0]]

            # make sure the output directory is not searched
            if not root and self.cfg.get('relative_to_indir'):
                ignore = [d for d in enumerate(dirs)
                          if d[1] in [ os.path.basename(self.bagparent) ]]
                if ignore:
                    for h in reversed(ignore):
                        del dirs[h[0]]


class MIDASFormatPrepper(SIPPrepper):
    """
    This class will prepare an SIP organized in a form expected from the MIDAS 
    application by re-organizing its contents into a working bag
    """

    MDFILE_DEST = {
        MIDAS_POD_FILE: "metadata/pod.json",
        "_premis.xml":  "premis.xml",
        "_oai-ore.txt": "oai-ore.txt",
        "_oai-ore.xml": "oai-ore.xml",
        "_mets.xml":    "mets.xml"
    }

    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """
        locs = self.cfg.get('pod_locations', [ MIDAS_POD_FILE ])
        for loc in locs:
            path = os.path.join(self.sipdir, loc)
            if os.path.exists(path):
                return loc
        raise PODError("POD file not found in expected locations: "+str(locs))

    def ensure_all_data_files(self, metadata_files=None):
        """
        ensure that all data files have been added to the working bag directory.
        The given metadata_files list the files that are not considered "data
        files".  
        """
        if metadata_files is None:
            metadata_files = []
            
        start = re.compile(self.sipdir+r'/?')
        for root, dirs, files in os.walk(self.sipdir):
            root = start.sub('', root)
            for file in files:
                file = os.path.join(root,file)
                if file not in metadata_files:
                    self.ensure_data_file(file)

    def ensure_preparation(self):
        """
        create and update the output working bag directory to ensure it is 
        a re-organized version of the SIP directory, ready for annotation 
        and preservation.  
        """

        # create the output working bag directory
        self.ensure_bag_structure()

        # identify the input metadata files
        podfile = self.find_pod_file()
        dest = self.MDFILE_DEST.copy()
        if podfile not in dest:
            dest[podfile] = dest[MIDAS_POD_FILE]
            del dest[MIDAS_POD_FILE]
        md_files = [ podfile ]
        self._extend_file_list(md_files, 'allow_metadata_files')

        # find all the files and replicate them into the output working
        # bag directory
        for fil in self.list_submitted_files():
            if fil in md_files:
                # it's a metadata file
                if fil in self.MDFILE_DEST:
                    # has a special place
                    self.ensure_metadata_file(fil, self.MDFILE_DEST[fil])
                else:
                    # put under the metadata directory
                    self.ensure_metadata_file(fil,
                            os.path.join(self.bagdir, 'metadata', fil))
            else:
                # it's a data files
                self.ensure_data_file(fil)
                                              

# NOTE: SIPFormatPrepper is start here for a future version 
    
class SIPFormatPrepper(SIPPrepper):
    """
    This class will prepare an SIP organized in a bag-like form by 
    re-organizing its contents into a working AIP bag
    """

    def find_pod_file(self):
        """
        find an existing pod file given a list of existing possible locations
        """

        locs = self.cfg.get('pod_locations', [ AIP_POD_FILE ])
        out = find_file(self.sipdir, locs)
        if not out:
          raise PODError("POD file not found in expected locations: "+str(locs))
        return out
    
def find_file(base, locs):
    """
    find an existing pod file given a list of existing possible locations
    relative to the base directory.
    """
    for loc in locs:
        loc = os.path.join(base, loc)
        if os.path.exists(loc):
            return loc
    return None

def detect_SIP_format(sipdir):
    """
    determine the submission information format in use in the given 
    submission information package (SIP) directory.

    This implementation simply tests the location of the POD record file
    with only one format recognized MIDASFormatPrepper.

    A type label is returned for the detected format, and None is returned 
    if the format is not recognized.  
    """
    locs_by_type = {
        "MIDAS":  [ MIDAS_POD_FILE ]
    }

    for key in locs_by_type:
        if find_file(sipdir, locs_by_type[key]):
            return key

    return None

def create_prepper(sipdir, workdir, config):
    """
    create the correct SIPPrepper class to handle the given SIP directory 
    and the format it complies with.

    :param sipdir   str:   path to the submission directory
    :param workdir  str:   path to work directory where the working bag 
                            directory can be created
    :param config  dict:   a configuration dictionary to pass to the prepper.
    """
    prepper_classes = {
        "MIDAS": MIDASFormatPrepper
    }

    format = detect_SIP_format(sipdir)
    if not format:
        raise SIPDirectoryError(sipdir, "Unable to determine submission format")
    if format not in prepper_classes:
        raise SIPDirectoryError(sipdir, "Unsupported submission format: "+format)

    return prepper_classes[format](sipdir, workdir, config)
