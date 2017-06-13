"""
This module manages the preparation of the metadata needed by pre-publication
landing page service.  It uses an SIPBagger to create the NERDm metadata from 
POD metadata provided by MIDAS and assembles it into an exportable form.  
"""
import os, logging, re, json

from collections import Mapping
from .. import PublishSystem
from ...exceptions import ConfigurationException, StateException, SIPDirectoryNotFound
from ...preserv.bagger import MIDASMetadataBagger
from ...preserv.bagit import NISTBag
from ....id import PDRMinter

log = logging.getLogger(PublishSystem().subsystem_abbrev)

class PrePubMetadataService(PublishSystem):
    """
    The class providing the implementation for the pre-publication metadata
    service.

    This service wraps the MIDASMetadataBagger class which examines the MIDAS 
    upload and review directories for data and metadata and prepares the 
    NERDm metadata.  This class then will serve out the final, combined NERDm 
    record, converting (if so configured) the downloadURLs to bypass the 
    data distribution service (as is necessary for the pre-publication data).  
    """

    def __init__(self, config, workdir=None, reviewdir=None, uploaddir=None,
                 idregdir=None):
        """
        initialize the service.

        :param config   dict:  the configuration parameters for this service
        :param workdir   str:  the path to the workspace directory where this
                               service will write its data.  If not provided,
                               the value of the 'working_dir' configuration 
                               parameter will be used.
        :param reviewdir str:  the path to the MIDAS-managed directory for SIPs 
                               in the review state.  If not provided,
                               the value of the 'review_dir' configuration 
                               parameter will be used.
        :param uploaddir str:  the path to the MIDAS-managed directory for SIPs
                               in the upload state.  If not provided,
                               the value of the 'upload_dir' configuration 
                               parameter will be used.
        """
        if not isinstance(config, Mapping):
            raise ValueError("PrePubMetadataService: config argument not a " +
                             "dictionary: " + str(config))
        self.cfg = config

        self.log = log.getChild("mdserv")
        
        if not workdir:
            workdir = self.cfg.get('working_dir')
        if not workdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "working_dir", sys=self)
        if not os.path.isdir(workdir):
            raise StateException("Working directory does not exist as a " +
                                 "directory: " + workdir, sys=self)
        self.workdir = workdir

        if not reviewdir:
            reviewdir = self.cfg.get('review_dir')
        if not reviewdir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "review_dir", sys=self)
        if not os.path.isdir(reviewdir):
            raise StateException("MIDAS review directory does not exist as a " +
                                 "directory: " + reviewdir, sys=self)
        self.reviewdir = reviewdir

        if not uploaddir:
            uploaddir = self.cfg.get('upload_dir')
        if not uploaddir:
            raise ConfigurationException("Missing required config parameters: "+
                                         "upload_dir", sys=self)
        if not os.path.isdir(uploaddir):
            raise StateException("MIDAS Upload directory does not exist as a " +
                                 "directory: " + uploaddir, sys=self)
        self.uploaddir = uploaddir

        if not idregdir:
            idregdir = self.cfg.get('id_registry_dir', self.workdir)
        if not os.path.isdir(idregdir):
            raise StateException("ID Registry directory does not exist as a " +
                                 "directory: " + idregdir, sys=self)

        self._minter = self._create_minter(idregdir)

        mimefiles = self.cfg.get('mimetype_files', [])
        if not isinstance(mimefiles, list):
            mimefiles = [mimefiles]
        self.mimetypes = build_mime_type_map(mimefiles)

    def _create_minter(self, parentdir):
        cfg = self.cfg.get('id_minter', {})
        out = PDRMinter(parentdir, cfg)
        if not os.path.exists(out.registry.store):
            self.log.warn("Creating new ID minter")
        return out

    def prepare_metadata_bag(self, id):
        """
        Bag up the metadata from data provided by MIDAS for a given MIDAS ID.  
        """
        cfg = self.cfg.get('bagger', {})
        bagger = MIDASMetadataBagger(id, self.workdir, self.reviewdir,
                                     self.uploaddir, cfg, self._minter)
        bagger.ensure_preparation()
        return bagger

    def make_nerdm_record(self, bagdir, baseurl=None):
        """
        Given a metadata bag, generate a complete NERDm resource record.  

        This may convert all downloadURLs that go through the data distribution 
        service (i.e. that match that service's base URL) to URLs that go
        through a different server.  This is needed for as-yet unreleased data
        as this service is intended to serve.  Conversion is done either by 
        setting the 'download_base_url' parameter in the configuration or by
        providing a baseurl argument.  The value in both cases is the base URL
        to convert the download URLs to.  The config parameter, 
        'datadist_base_path', indicates the base URL path to look for to 
        recognize data distribution service URLs.

        :param bagdir str:  the directory representing the output bag to serve
                            the metadata from 
        :param baseurl str: the baseurl to convert downloadURLs to; if None,
                            conversion will not be applied unless 
                            'download_base_url' is set (see above).  
        """
        bag = NISTBag(bagdir)
        out = bag.nerdm_record()

        if not baseurl:
            baseurl = self.cfg.get('download_base_url')
        if baseurl and 'components' in out:
            ddspath = self.cfg.get('datadist_base_url', '/od/ds/')
            if ddspath[0] != '/':
                ddspath = '/' + ddspath
            pat = re.compile(r'https?://[\w\.]+(:\d+)?'+ddspath)
            for comp in out['components']:
                if 'downloadURL' in comp and pat.search(comp['downloadURL']):
                    comp['downloadURL'] = pat.sub(baseurl, comp['downloadURL'])

        return out

    def resolve_id(self, id):
        """
        return a full NERDm resource record corresponding to the given 
        MIDAS ID.  
        """
        return self.make_nerdm_record(self.prepare_metadata_bag(id).bagdir)

    def locate_data_file(self, id, filepath):
        """
        return the location and recommended MIME-type for a data file associated
        with the dataset of a given ID.

        :param id       str:   the dataset's identifier
        :param filepath str:   the relative path to the data file within the 
                                 dataset
        :return tuple:  2-element tuple giving the full filepath and recommended
                                 MIME-type
        """
        bagger = self.prepare_metadata_bag(id)
        if filepath not in bagger.datafiles:
            return (None, None)

        loc = bagger.datafiles[filepath]
        mt = self.mimetypes.get(os.path.splitext(loc)[1][1:],
                                'application/octet-stream')
        return (loc, mt)
        
        
def_ext2mime = {
    "html": "text/html",
    "txt":  "text/plain",
    "xml":  "text/xml",
    "json": "application/json"
}

def update_mimetypes_from_file(map, filepath):
    """
    load the MIME-type mappings from the given file into the given dictionary 
    mapping extensions to MIME-type values.  The file can have either an nginx
    configuration format or the common format (i.e. used by Apache).  
    """
    if map is None:
        map = {}
    if not isinstance(map, Mapping):
        raise ValueError("map argument is not dictionary-like: "+ str(type(map)))

    commline = re.compile(r'^\s*#')
    nginx_fmt_start = re.compile(r'^\s*types\s+{')
    nginx_fmt_end = re.compile(r'^\s*}')
    with open(filepath) as fd:
        line = '#'
        while line and (line.strip() == '' or commline.search(line)):
            line = fd.readline()

        if line:
            line = line.strip()
            if nginx_fmt_start.search(line):
                # nginx format
                line = fd.readline()
                while line:
                    if nginx_fmt_end.search(line):
                        break
                    line = line.strip()
                    if line and not commline.search(line):
                        words = line.rstrip(';').split()
                        if len(words) > 1:
                            for ext in words[1:]:
                                map[ext] = words[0]
                    line = fd.readline()

            else:
                # common server format
                while line:
                    if commline.search(line):
                        continue
                    words = line.strip().split()
                    if len(words) > 1:
                        for ext in words[1:]:
                            map[ext] = words[0]
                    line = fd.readline()

    return map

def build_mime_type_map(filelist):
    """
    return a dictionary mapping filename extensions to MIME-types, given an 
    ordered list of files defining mappings.  Entries in files appearing later 
    in the list can override those in the earlier ones.  Files can be in either 
    the nginx configuration format or the common format (i.e. used by Apache).  

    :param filelist array:  a list of filepaths defining the MIME-types to
                            extensions mappings.
    """
    out = def_ext2mime.copy()
    for file in filelist:
        update_mimetypes_from_file(out, file)
    return out


