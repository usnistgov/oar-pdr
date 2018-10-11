"""
Support for the multibag BagIt profile.  In particular, this module can split 
a single bag into multiple output multbags for preservation.  
"""
from __future__ import print_function, absolute_import
import os, logging, re, json, shutil
from functools import cmp_to_key

import multibag

from .. import ConfigurationException, StateException, AIPValidationError
from ... import utils
from .bag import NISTBag

class MultibagSplitter(object):
    """
    a class responsible for splitting a source bag into one or more multibags.

    The constructor takes configuration parameters specifying target sizes for 
    output bags.  The check_and_split() function handles the splitting.  If the 
    source bag exceeds a single bag size limit, it will be split into 2 or more 
    bags.  Otherwise the multibag metadata is added to the source bag set for a
    single multibag.  

    This class provides a front end to the multibag module to apply NIST 
    policies to preservation bags.  The splitting plan is a variation on the 
    multibag's NeighborlySplitter algorithm (which prefers collecting files 
    from the same directory together) in which the head bag is kept small and 
    typically contains only the metadata.  

    This class takes a configuration dictionary at construction and looks for 
    the following properties.  

    :prop max_bag_size int:      the maximum desired size in bytes of an output
                                 bag.  This size will only be exceeded when an
                                 output bag must contain a single data file that
                                 is larger than this amount.  If not provided or 
                                 less than zero, no maximum size limit is 
                                 imposed (see also target_bag_size).
    :prop max_headbag_size int:  the maximum desired size in bytes of the 
                                 output mutlibag aggregation's head bag.  If 
                                 not provided, it defaults to the value of 
                                 max_bag_size.
    :prop target_bag_size int:   the target size, in bytes, for each output bag
                                 (other than the head bag).  An output bag will
                                 be filled until it is close to this size 
                                 (either larger or less than).  If not set, less
                                 than or equal to zero, or more than 
                                 max_bag_size, then the target size will 
                                 effectively be the max_bag_size.  If both this 
                                 and max_bag_size are not set, the source bag
                                 will not be set.
    :prop convert_small bool:    if True, the check_and_split() function will 
                                 convert the input bag to a single multibag
                                 aggregation if the bag is too small to exceed
                                 the split requirements.  Default: False
    :prop verify_complete bool:  if True, run checks that make sure that the 
                                 output bags appear to be complete in that they 
                                 include all of the input files.  Default: True
    :prop validate bool:         if True, (re-)validate each of the output 
                                 multibags.  Default: False
    :prop replace bool:          When splitting, replace the input bag if 
                                 output directory is the same as the input's.
    """

    def __init__(self, source_bagdir, config=None):
        """
        Initialize the splitter.  

        :param str source_bagdir:  the root directory of the (unserialized)
                                   source bag.
        :param dict config:        the data for configuring the behavior of 
                                   this spitter (see class documentation 
                                   above).  
        """
        if not config:
            config = {}
        self.cfg = config
        self.srcdir = source_bagdir

        if not os.path.exists(self.srcdir):
            raise StateException("Bag directory not found: "+self.srcfir)

        self._chk_cfg()
        self.maxsz = self.cfg.get("max_bag_size", 0)
        self.maxhbsz = self.cfg.get("max_headbag_size", self.maxsz)
        self.trgsz = self.cfg.get("target_bag_size", self.maxsz)
        if self.trgsz <= 0:
            self.trgsz = self.maxsz

    def _chk_cfg(self):
        prob = []
        for fld in "max_bag_size max_headbag_size target_bag_size".split():
            if self.cfg.get(fld) == "":
                del self.cfg[fld]
            if self.cfg.get(fld):
                try:
                    self.cfg[fld] = int(self.cfg[fld])
                except ValueError as ex:
                    prob.append(fld)
        if prob:
            raise ConfigurationException("Properties not interpretable as " +
                                         "integers: " + ", ".join(prob))

    def check(self, log=None):
        """
        determine if the size of the source bag warrants being split.  The
        bag size is taken from from the Bag-Size info.  

        :return boolean:  True if the source bag will be split by split()
        """
        if self._szoor(self.maxsz) and self._szoor(self.maxhbsz) and \
           self._szoor(self.trgsz):
            if log:
                log.debug("multibag thresholds prevent splitting: "+
                          "head bag size=%d max size=%d target size=%d",
                          self.maxhbsz, self.maxsz, self.trgsz)
            return False
        srcbag = NISTBag(self.srcdir)
        try:
            sz = srcbag.get_baginfo().get('Bag-Oxum')
            if sz:
                sz = int(sz[-1].split('.')[0])
        except ValueError as e:
            sz = None
            if log:
                val = srcbag.get_baginfo().get('Bag-Oxum','')
                if val: val = ": "+val[-1]
                log.warning("'Bag-Oxum' not set as expected in %s%s",
                            os.path.basename(self.srcdir), val)
            sz = -1

        if not sz:
            if log:
                log.debug("Bag-Oxum value not found in bag-info; calculating...")
            sz = utils.measure_dir_size(self.srcdir)[0]

        if log:
            log.debug("Base bag size: %d bytes", sz)
            
        if sz > self.maxhbsz or sz > self.maxsz:
            return True

        return False

    def _szoor(self, sz):
        return sz <= 0

    def split(self, destdir, log=None):
        """
        split the source bag into one or more multibags written to a given 
        directory

        :param str destdir:  the directory where output bags will be written.
        """
        nameiter = _OARNamer(self.srcdir)

        origsrc = self.srcdir
        if os.path.dirname(self.srcdir) == destdir:
            # our convention is to have the first output multibag have the
            # same name as the source bag; thus, if the input and output bags
            # are set to be in the same parent directory, we will have to deal
            # with a name collision.
            if self.cfg.get('replace'):
                # rename the source bag to a temporary name
                self.srcdir = os.path.join(os.path.dirname(origsrc),
                                           "_" + os.path.basename(origsrc))
                try:
                    if os.path.isdir(self.srcdir):
                        shutil.rmtree(self.srcdir)
                    os.rename(origsrc, self.srcdir)
                except:
                    self.srcdir = origsrc
                    raise
            else:
                nameiter.sn += 1

        oldsplre = re.compile(nameiter.base+r'\d+$')
        needclean = []
        for b in os.listdir(destdir):
            bp = os.path.join(destdir, b)
            if not oldsplre.match(b) or bp == self.srcdir:
                continue
            needclean.append(bp)
        if needclean:
            if log:
                if len(needclean) > 1:
                    log.warning("Removing %d previously existing multibags",
                                len(needclean))
                else:
                    log.warning("Removing previously existing multibag: %s",
                                os.path.basename(needclean[0]))
            for mb in needclean:
                if log:
                    log.debug("Removing %s...", mb)
                shutil.rmtree(mb)

        try:
            spltr = OARSplitter(self.maxsz, self.trgsz, self.maxhbsz)
            out = spltr.split(self.srcdir, destdir, nameiter, ['Bag-Oxum'],
                              logger=log)
        except:
            # error occurred: restore the original name to the source bag
            if origsrc != self.srcdir:
                if os.path.exists(origsrc):
                    shutil.rmtree(origsrc)
                    os.rename(self.srcdir, origsrc)
            raise

        if self.cfg.get('verify_complete', True):
            self._verify_complete(self.srcdir, out)

        if self.cfg.get('validate'):
            for bagdir in out:
                try:
                    multibag.open_bag(bagdir).validate()
                except multibag.BagError as ex:
                    raise AIPValidationError(str(ex), cause=ex)
            try:
                multibag.validate_headbag(out[-1])
            except multibag.BagError as ex:
                raise AIPValidationError(str(ex), cause=ex)

        if self.cfg.get('replace') and origsrc != self.srcdir:
            shutil.rmtree(self.srcdir)
            self.srcdir = origsrc

        return out

    def _verify_complete(self, srcdir, multidirs):
        headbag = multibag.open_headbag(multidirs[-1])
        if not headbag.is_head_multibag():
            raise AIPValidationError("Expected to be a head bag: "+multidirs[-1])

        # walk through all data and metadata files found in source bag
        errors = []
        datadir = os.path.join(srcdir, "data")
        for dir, subdirs, files in os.walk(datadir):
            dir = dir[len(datadir)-4:]   # = "data/..."
            for file in files:
                file = os.path.join(dir, file)
                error = self._confirm_found(file, multidirs, headbag)
                if error:
                    errors.append(error)

        datadir = os.path.join(srcdir, "metadata")
        for dir, subdirs, files in os.walk(datadir):
            dir = dir[len(datadir)-8:]   # = "metadata/..."
            for file in files:
                file = os.path.join(dir, file)
                error = self._confirm_found(file, multidirs, headbag)
                if error:
                    errors.append(error)

        if len(errors) > 0:
            raise AIPValidationError("Output multibags look incomplete", errors)

    def _confirm_found(self, filepath, multidirs, headbag):
        # confirm that we can find the given file path in the output multibags
        
        # is it listed in the lookup file?
        location = headbag.lookup_file(filepath)
        if not location:
            return  "Failed to find input file in output multibag: " + filepath
        
        # is the designated location one of our multibags?
        bagdir = [b for b in multidirs if b.endswith("/"+location)]
        if len(bagdir) == 0:
            return "Unrecognized location for " + filepath + ": "+location
        bagdir = bagdir[0]

        # is the file in the output multibag it's supposed to be in?
        if not os.path.isfile(os.path.join(bagdir, filepath)):
            return "file not found in "+location+": "+filepath

        return None

    def make_single_multibag(self):
        """
        add necessary multibag metadata to convert the source bag into the 
        head bag for a single bag aggregation.
        """
        mkr = multibag.SingleMultibagMaker(self.srcdir)
        mkr.write_member_bags()
        mkr.write_file_lookup("data metadata about.txt".split() +
                              "preservation.log oai-ore.txt premis.xml".split(),
                              trunc=True)
        mkr.update_info("1.0")

    def check_and_split(self, destdir, log=None):
        """
        First check the input source bag to see if it should be split; if so,
        use split() to carry out the split.  Otherwise, call 
        make_single_multibag() to update the source bag's metadata.
        """
        if self.check(log):
            if log:
                log.info("Input bag will be split")
            return self.split(destdir, log=log)
        
        if self.cfg.get('convert_small', False):
            self.make_single_multibag()
        return [self.srcdir]

class OARSplitter(multibag.NeighborlySplitter):
    """
    an implementation of multibag.split.Splitter used to split a source bag
    "the OAR way".  
    """
    def __init__(self, maxsize=60000, targetsize=None, maxhdsize=None,
                 hbslop=0.05):
        """
        Create the splitter based on the "neighborly" algorithm

        :param int maxsize:  the maximum size of an output bag.  No bag will be 
                             bigger than this limit except when a single file
                             exceeds this limit (in this case,  this file will 
                             be placed in its on multibag by itself).
        :param int targetsize:  the preferred size of an output bag.  Bags will 
                             be packed until they just exceed this fize by one
                             file.  The total size will still be kept less than 
                             maxsize. 
        :param int maxhdsize:  the maximum size of the head bag.  This is 
                             typically smaller than maxsize (for faster 
                             retrieval and cheaper storage).  If not provided
                             (or out of range), it defaults to maxsize.
        """
        if not maxhdsize or maxhdsize > maxsize:
            maxhdsize = maxsize
        super(OARSplitter, self).__init__(maxsize, targetsize)
        self.maxhdsz = maxhdsize
        self.hbslop = float(hbslop)

    def _sorted_files(self, bag):
        datafs = bag._root.subfspath("data")
        finfos = [{"path": "/data"+p, "size": f.size, "name": p.split('/')[-1]}
                   for p,f in datafs.fs.walk.info(namespaces=['details'])
                       if not f.is_dir and p not in self.forhead]
                          
        finfos.sort(key=cmp_to_key(self._cmp_by_size))
        return finfos
    
    def _create_plan(self, bagpath):
        out = super(OARSplitter, self)._create_plan(bagpath)

        # the head bag should contain the metadata tree, the preservation log,
        # and other metadata files.  Now check to see if combining the last
        # non-head bag with the head bag keeps the head bag below its limit;
        # if so, combine them.  
        mfs = list(out.manifests())
        if len(mfs) > 1 and \
           (mfs[-2]['totalsize'] + mfs[-1]['totalsize']) <= \
               self.maxhdsz*(1+self.hbslop):
            mfs[-2]['contents']  += mfs[-1]['contents']
            mfs[-2]['totalsize'] += mfs[-1]['totalsize']
            del mfs[-1]
            out._manifests = mfs

        return out

class _OARNamer(object):
    """
    A naming iterator that creates bag names matching the NIST-OAR bag 
    naming convention.  It is used to assign names to multbags resulting from 
    splitting a large bag.  It is initialized from the name of the bag getting 
    split: it looks for the sequence number at the end of the bag name and 
    increments it for each of the output bags.  The sequence number of the first 
    bag in the output set will be the same as the input progenitor bag.  

    This is not intended for external use.  

    See the external multibag.split.SplitPlan.name_output_bags() for details 
    for how a the naming iterator works.
    """
    def __init__(self, progenitor):
        """
        set up the naming iterator based on the name of the progenitor bag 
        being split.  

        :param str progenitor:  the name or path to the progenitor bag
        """
        progenitor = os.path.basename(progenitor)
        m = re.search(r'-(\d+)$', progenitor)
        if m:
            seq = m.group(1)
            self.base = progenitor[:-1*len(seq)]
        else:
            seq = -1
            self.base = progenitor

        self.sn = int(seq) - 1

    def __iter__(self):
        return self

    def __next__(self):
        self.sn += 1
        return self.base + str(self.sn)

    def next(self):
        return self.__next__()


    
