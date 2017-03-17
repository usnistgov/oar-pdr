"""
Tools for reading data from a bag
"""

import os, logging, re, json, hashlib
from collections import OrderedDict

from .. import PreservationSystem
from .. import NERDError, PODError, StateException
from .builder import find_jq_lib
from ....nerdm.merge import MergerFactory
from ....nerdm.convert import ComponentCounter

POD_FILENAME = "pod.json"
NERDMD_FILENAME = "nerdm.json"
ANNOT_FILENAME = "annot.json"
DEFAULT_MERGE_CONVENTION = "dev"

JQLIB = find_jq_lib()

class NISTBag(PreservationSystem):
    """
    an interface for reading data in a NIST-compliant BagIt bag.
    """

    # NOTE: this is an imcomplete implementation 

    def __init__(self, rootdir, merge_annots=False):
        if not os.path.isdir(rootdir):
            raise StateException("Bag directory does not exist as a directory: "+
                                 rootdir, sys=self)
        self._dir = rootdir
        self._name = os.path.basename(rootdir)

        self._datadir = os.path.join(rootdir, "data")
        self._metadir = os.path.join(rootdir, "metadata")

        self._mergeannots = merge_annots

    @property
    def dir(self):
        """
        the path to the root directory of the bag
        """
        return self._dir

    @property
    def name(self):
        """
        the bag's name
        """
        return self._name

    @property
    def data_dir(self):
        """
        the path to the data directory for the bag
        """
        return self._datadir

    @property
    def metadata_dir(self):
        """
        the path to the metadata directory for the bag
        """
        return self._metadir

    def pod_file(self):
        return os.path.join(self._metadir, POD_FILENAME)

    def nerd_file_for(self, destpath):
        return os.path.join(self._metadir, destpath, NERDMD_FILENAME)

    def nerd_metadata_for(self, destpath):
        return self.read_nerd(self.nerd_file_for(destpath))

    def nerdm_record(self, merge_annots=None):
        """
        return a full NERDm resource record for the data in this bag.

        :param merge_annots bool:  merge in any annotation data found in the bag.
                                   (Default is the value of the 'merge_annots'
                                   constructor argument.)  For a complete bag,
                                   annotations will already be merged into main
                                   NERDm metadata; however, if this is not the 
                                   case, yet, one can merge on the fly while 
                                   creating the record.  
        """
        if merge_annots is None:
            merge_annots = self._mergeannots
        if merge_annots is True:
            merge_annots = DEFAULT_MERGE_CONVENTION
        compmerger = None
        if merge_annots:
            compmerger = MergerFactory.make_merger(merge_annots, 'Component')

        out = None
        for root, subdirs, files in os.walk(self._metadir):
            if root == self._metadir:
                out = self.nerd_metadata_for("")
                if 'components' not in out:
                    out['components'] = []

                if merge_annots:
                    annotfile = os.path.join(root,ANNOTS_FILENAME)
                    if os.path.exists(annotfile):
                        annots = self.read_nerd(annotfile)
                        merger = MergerFactory.make_merger(merger_annots,
                                                           'Resource')
                        out = merger.merge(out, annots)

            elif NERDMD_FILENAME in files:
                comp = self.read_nerd(os.path.join(root, NERDMD_FILENAME))

                if merge_annots:
                    annotfile = os.path.join(root,ANNOTS_FILENAME)
                    if os.path.exists(annotfile):
                        annots = self.read_nerd(annotfile)
                        comp = compmerger.merge(comp, annots)

                out['components'].append(comp)

        if 'inventory' not in out:
            self.inventory(out)
        return out

    def inventory(self, resmd):
        resmd['inventory'] = {}

        if 'components' in resmd:
            components = resmd['components']
            cc = ComponentCounter(JQLIB)
            resmd['inventory'] = cc.inventory(components)

        return resmd

    def read_pod(self, podfile):
        try:
            with open(podfile) as fd:
                return json.load(fd, object_pairs_hook=OrderedDict)
        except IOError, ex:
            raise PODError("Unable to read POD file: "+str(ex),
                           cause=ex, src=podfile, sys=self)

    def read_nerd(self, nerdfile):
        try:
            with open(nerdfile) as fd:
                return json.load(fd, object_pairs_hook=OrderedDict)
        except IOError, ex:
            raise NERDError("Unable to read NERD file: "+str(ex),
                            cause=ex, src=nerdfile, sys=self)

    
    
