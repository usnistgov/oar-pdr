"""
This bagger submodule provides functions for preparing an update to a previously
preserved collection.  This includes a service client for retrieving previous
head bags from cache or long-term storage.  
"""
import os, shutil, json, logging
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import OrderedDict
from zipfile import ZipFile

from .base import sys as _sys
from .. import (ConfigurationException, StateException, CorruptedBagError,
                NERDError)
from . import utils as bagutils
from ...describe import rmm
from ... import distrib
from ...exceptions import IDNotFound
from ... import utils
from ..bagit.builder import BagBuilder
from ..bagit.bag import NISTBag

deflog = logging.getLogger(_sys.system_abbrev).getChild(_sys.subsystem_abbrev)

class HeadBagCacher(object):
    """
    a helper class that manages serialized head bags in a local cache.
    """
    def __init__(self, distrib_service, cachedir, infodir=None):
        """
        set up the cache
        :param RESTServiceClient distrib_service:  the distribution service 
                               to use to pull in head bags from.
        :param str cachedir:   the path to the directory where bags will be 
                               cached.
        :param str infodir:    the path to the directory where bag metadata 
                               will be stored.  If not provided, a subdirectory
                               of cachedir, "_info", will be used.
        """
        self.distsvc = distrib_service
        self.cachedir = cachedir
        if not infodir:
            infodir = os.path.join(self.cachedir, "_info")
        self.infodir = infodir

        if not os.path.exists(self.cachedir):
            os.mkdir(self.cachedir)
        if not os.path.isdir(self.cachedir):
            raise StateException("HeadBagCacher: not a directory: "+
                                 self.cachedir)
        if not os.path.exists(self.infodir):
            os.mkdir(self.infodir)
        if not os.path.isdir(self.infodir):
            raise StateException("HeadBagCacher: not a directory: "+
                                 self.cachedir)
        

    def cache_headbag(self, aipid, version=None, confirm=True):
        """
        ensure a copy of the serialized head bag in the cache
        :rtype: str giving the path to the cached, serialized head bag or 
                None if no such bag exists.  
        """
        bagcli = distrib.BagDistribClient(aipid, self.distsvc)

        hinfo = None
        if version and version != 'latest':
            # map id,version to bagfile using our local cache
            info = self._recall_head_info(aipid)
            if version in info and 'name' in info[version]:
                hinfo = info[version]

        if not hinfo:
            # map id,version to bagfile using the remote service
            try:
                hinfo = bagcli.describe_head_for_version(version)
            except distrib.DistribResourceNotFound as ex:
                return None

            # cache the info locally
            if not version or version == 'latest':
                version = hinfo['sinceVersion']
            self._cache_head_info(aipid, version, hinfo)

        # look for bag in cache; if not there, fetch a copy
        bagfile = os.path.join(self.cachedir, hinfo['name'])
        if not os.path.exists(bagfile):
            bagcli.save_bag(hinfo['name'], self.cachedir)
        if confirm:
            self.confirm_bagfile(hinfo)

        return bagfile

    def confirm_bagfile(self, baginfo, purge_on_error=True):
        """
        Make sure the cached bag described by bag metadata was transfered
        correctly by checking it checksum.  
        :raise CorruptedBagError: if an error was detected.
        """
        bagfile = os.path.join(self.cachedir, baginfo['name'])
        try:
            if utils.checksum_of(bagfile) != baginfo['checksum']['hash']:
                if purge_on_error:
                    # bag file looks corrupted; purge it from the cache
                    self._clear_from_cache(bagfile, baginfo)
                    
                raise CorruptedBagError(bagfile, bagfile+": checksum failure")
        except OSError as ex:
            if purge_on_error:
                self._clear_from_cache(bagfile, baginfo)
                
            raise CorruptedBagError(bagfile, "Failure reading bag file: " +
                                    bagfile + ": " + str(ex), cause=ex)

    def _clear_from_cache(self, bagfile, baginfo=None):
        if os.path.exists(bagfile):
            os.remove(bagfile)
        if baginfo:
            info = self._recall_head_info(baginfo['aipid'])
            if baginfo['sinceVersion'] in info:
                del info[baginfo['sinceVersion']]
                self._save_head_info(baginfo['aipid'], info)

    def _cache_head_info(self, aipid, version, info):
        out = self._recall_head_info(aipid)
        out[version] = info
        self._save_head_info(aipid, out)

    def _save_head_info(self, aipid, info):
        with open(self._head_info_file(aipid), 'w') as fd:
            json.dump(info, fd, indent=2)

    def _head_info_file(self, aipid):
        return os.path.join(self.infodir, aipid)

    def _recall_head_info(self, aipid):
        hif = self._head_info_file(aipid)
        if not os.path.exists(hif):
            return OrderedDict()
        with open(hif) as fd:
            return json.load(fd, object_pairs_hook=OrderedDict)
            

class UpdatePrepService(object):
    """
    a factory class that creates UpdatePrepper instances
    """
    def __init__(self, config):
        self.cfg = config

        self.sercache = self.cfg.get('headbag_cache')
        if not self.sercache:
            raise ConfigurationException("UpdatePrepService: Missing property: "+
                                         "headbag_cache")
        scfg = self.cfg.get('distrib_service', {})
        self.distsvc = distrib.RESTServiceClient(scfg.get('service_endpoint'))
        scfg = self.cfg.get('metadata_service', {})
        self.mdsvc  = rmm.MetadataClient(scfg.get('service_endpoint'))
        self.cacher = HeadBagCacher(self.distsvc, self.sercache)

    def prepper_for(self, aipid, version=None, log=None):
        """
        return an UpdatePrepper instance for the given dataset identifier
        """
        return UpdatePrepper(aipid, self.cfg, self.cacher, self.mdsvc,
                             version, log)


class UpdatePrepper(object):
    """
    a class that restores the latest head bag of a previously preserved dataset
    to disk and prepares it for access and possible update by the PDR publishing 
    system.  
    """

    def __init__(self, aipid, config, headcacher, pubmdclient,
                 version=None, log=None):
        """
        create the prepper for the given dataset identifier.  

        This is not intended to be instantiated directly by the user; use
        the UpdatePrepService.prepper_for() factory method. 
        """
        self.aipid = aipid
        self.cacher = headcacher
        self.version = version
        self.mdcli = pubmdclient
        self.mdcache = os.path.join(self.cacher.cachedir, "_nerd")
        if not os.path.exists(self.mdcache):
            os.mkdir(self.mdcache)
        if not os.path.isdir(self.mdcache):
            raise StateException("UpdatePrepper: not a directory: "+self.mdcache)

        if not log:
            log = deflog.getChild(self.aipid[:8]+'...')
        self.log = log

    def cache_headbag(self):
        """
        ensure a copy of the serialized head bag in the read-only cache
        :rtype: str giving the path to the cached, serialized head bag or 
                None if no such bag exists.  
        """
        try:
            return self.cacher.cache_headbag(self.aipid, self.version)
        except CorruptedBagError as ex:
            # try again (now that the cache is clean)
            return self.cacher.cache_headbag(self.aipid, self.version)

    def cache_nerdm_rec(self):
        """
        ensure a cached copy of the latest NERDm record from the repository.
        This is called for datasets that are in the PDL but have not gone 
        through the preservation service.  
        :rtype: str giving the path to the cached NERDm record, or
                None if no such bag exists.  
        """
        out = os.path.join(self.mdcache, self.aipid+".json")
        if not os.path.exists(out):
            try:
                data = self.mdcli.describe(self.aipid)
                with open(out, 'w') as fd:
                    json.dump(data, fd, indent=2)
            except IDNotFound as ex:
                return None
        return out

    def aip_exists(self):
        """
        return true if a previously ingested AIP with the current ID exists in 
        the repository.  
        """
        return self.cache_nerdm_rec() is not None
        
    def _unpack_bag_as(self, bagfile, destbag):
        if bagfile.endswith('.zip'):
            with ZipFile(bagfile, 'r') as zip:
                contents = zip.namelist()
                root = None
                for name in contents:
                    parts = name.split("/")
                    root = parts[0]
                    if root:
                        break

                if not root:
                    raise StateException("Bag appears to be empty: "+bagfile)
                destdir = os.path.dirname(destbag)
                if not os.path.exists(destdir):
                    raise StateException("Bag destination directory not found: "+
                                         bagfile)
                zip.extractall(destdir)

            tmpname = os.path.join(destdir, root)
            if not os.path.isdir(tmpname):
                raise RuntimeException("Apparent bag unpack failure; root "+
                                       "not created: "+tmpname)
            os.rename(tmpname, destbag)

        else:
            raise StateException("Don't know how to unpack serialized bag: "+
                                 os.path.basename(bagfile))

    def create_new_update(self, destbag):
        """
        create an updatable metadata bag for the purposes of creating a new 
        version of the dataset.   If this dataset has been through the 
        preservation service before, it will be built form the latest headbag;
        otherwise, it will be created from its latest public NERDm record.  

        :param str destbag:  the full path to the root directory of the metadata 
                             bag to create
        """
        mdbag = destbag
        if os.path.exists(mdbag):
            self.log.warning("Removing existing metadata bag for id="+self.aipid+
                             "\n   (may indicate earlier failure)")
            shutil.rmtree(mdbag)

        latest_headbag = self.cache_headbag()
        if latest_headbag:
            fmt = "Preparing update based on previous head preservation bag (%s)"
            self.log.info(fmt, os.path.basename(latest_headbag)) 
            self.create_from_headbag(latest_headbag, mdbag)
            return True

        latest_nerd = self.cache_nerdm_rec()
        if latest_nerd:
            self.log.info("No previous bag available; preparing based on " +
                          "existing published NERDm record")
            self.create_from_nerdm(latest_nerd, mdbag)
            return True

        self.log.info("ID not published previously; will start afresh")
        return False


    def create_from_headbag(self, headbag, mdbag):
        """
        create an updatable metadata bag from the latest headbag for
        the purposes of creating a new version.

        :param str headbag:  the path to an existing head bag to convert
        :param str mdbag:    the destination metadata bag to create (and 
                             thus should not yet exist).
        """
        if os.path.exists(mdbag):
            raise StateException("UpdatePrepper: metadata bag already exists "+
                                 "for id=" + self.aipid + ": " + mdbag)
        parent = os.path.dirname(mdbag)
        if not os.path.isdir(parent):
            raise StateException("metadata bag working space does not exist: "+
                                 parent)

        if os.path.isdir(headbag):
            # unserialized bag
            shutil.copytree(headbag, mdbag)
            
        elif not os.path.isfile(headbag):
            raise ValueError("UpdatePrepper: head bag does not exist: "+headbag)

        else:
            # serialized bag file
            self._unpack_bag_as(headbag, mdbag)

        # save the the bag-info.txt as deprecated-info.txt for later use
        mbdir = os.path.join(mdbag, "multibag")
        if not os.path.isdir(mbdir):
            os.mkdir(mbdir)
        shutil.copyfile(os.path.join(mdbag,"bag-info.txt"),
                        os.path.join(mbdir,"deprecated-info.txt"))

        # now remove certain bits that will get updated later
        datadir = os.path.join(mdbag, "data")
        if os.path.exists(datadir):
            shutil.rmtree(datadir)
        os.mkdir(datadir)

        for file in "bagit.txt bag-info.txt manifest-sha256.txt tagmanifest-sha256.txt".split():
            file = os.path.join(mdbag, file)
            if os.path.exists(file):
                os.remove(file)

        # update the metadata to the latest NERDm schema version
        # (this assumes forward compatibility).
        bag = NISTBag(mdbag)
        nerdm = bagutils.update_nerdm_schema(bag.nerdm_record())
        if not nerdm.get('@id'):
            raise StateException("Bag {0}: missing @id"
                                 .format(os.path.basename(mdbag)))
        bag = BagBuilder(parent, os.path.basename(mdbag), {}, nerdm.get('@id'),
                         logger=deflog)
        bag.add_res_nerd(nerdm, savefilemd=True)

        # finally set the version to a value appropriate for an update in
        # progress
        self.update_version_for_edit(mdbag)

    def create_from_nerdm(self, nerdfile, mdbag):
        """
        create an updatable metadata bag from the latest NERDm record for
        the purposes of creating a new version of the dataset.

        :param str nerdfile:  the path to a cached NERDm record
        :param str mdbag:     the destination metadata bag to create (and 
                              thus should not yet exist).
        """
        if os.path.exists(mdbag):
            raise StateException("UpdatePrepper: metadata bag already exists "+
                                 "for id=" + self.aipid + ": "+mdbag)
        parent = os.path.dirname(mdbag)
        bagname = os.path.basename(mdbag)
        if not os.path.isdir(parent):
            raise StateException("metadata bag working space does not exist: "+
                                 parent)

        if not os.path.exists(nerdfile):
            raise ValueError("Cached NERDm record not found: " + nerdfile)

        nerd = utils.read_nerd(nerdfile)
        if not '@id' in nerd:
            raise NERDError("Missing @id from NERD rec, "+nerdfile)

        # update the schema version to the latest supported version
        # (this assumes forward compatibility).
        bagutils.update_nerdm_schema(nerd)
        
        bldr = BagBuilder(parent, bagname, {}, nerd['@id'], logger=deflog)
        bldr.add_res_nerd(nerd, savefilemd=True)

        # update the version appropriate for edit mode
        self.update_version_for_edit(bldr.bagdir)

    def update_version_for_edit(self, bagdir):
        """
        update the version metadatum to something appropriate for edit mode.
        This will get updated according to policy as needed later.
        """
        bag = NISTBag(bagdir)
        mdata = bag.nerd_metadata_for('', merge_annots=True)
        oldvers = mdata.get('version', "1.0.0")
        verhist = mdata.get('versionHistory', [])
        edit_vers = self.make_edit_version(oldvers)
        self.log.debug('Setting edit version to "%s"', edit_vers)

        annotf = bag.annotations_file_for('')
        if os.path.exists(annotf):
            adata = utils.read_nerd(annotf)
        else:
            adata = OrderedDict()
        adata['version'] = edit_vers

        if oldvers != edit_vers and ('issued' in mdata or 'modified' in mdata) \
           and not any([h['version'] == oldvers] for h in verhist):
            issued = ('modified' in mdata and mdata['modified']) or \
                     mdata['issued']
            verhist.append(OrderedDict([
                ('version', oldvers),
                ('issued', issued),
                ('@id', mdata['@id']),
                ('location', 'https://data.nist.gov/od/id/'+mdata['@id'])
            ]))
            if oldvers == "1.0.0" or oldvers == "1.0" or oldvers == "1":
                verhist[-1]['description'] = 'initial release'
            adata['versionHistory'] = verhist
        
        utils.write_json(adata, annotf)
        
    def make_edit_version(self, prev_vers):
        return prev_vers + "+ (in edit)"
        

        
                             

        

