"""
CLI command that will scan all the files and ensure that the associated file metadata have correct 
size and checksum properties.
"""
import logging, argparse, sys, os, shutil, tempfile, json
from copy import deepcopy
from collections import Mapping

from nistoar.pdr.exceptions import ConfigurationException, PDRException, PDRServerError
from nistoar.pdr.preserv.bagger.prepupd import UpdatePrepService
from nistoar.pdr.preserv.bagger.midas3 import (moddate_of, UNSYNCED_FILE,
                                               MIDASMetadataBagger, _midadid_to_dirname as midas2recno)
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
from nistoar.pdr.utils import write_json
from nistoar.pdr.cli import PDRCommandFailure
from nistoar.pdr import def_schema_dir
from nistoar.nerdm.taxonomy import ResearchTopicsTaxonomy
from .. import validate as vald8, define_pub_opts, determine_bag_path

default_name = "filemd"
help = "ensure the size and checksum file metadata is up to date"
description = """
  examine files and update the NERDm file metadata accordingly; in particular, this ensures that 
  the file metadata includes accurate size and checksum data.  It will also automatically check that 
  any accompanying checksum data files contain a consistent checksum hash value, correcting them if 
  requested.

  This command assumes the midas3 bagging and preservation conventions.
"""

def load_into(subparser):
    """
    load this command into a CLI by defining the command's arguments and options.
    :param argparser.ArgumentParser subparser:  the argument parser instance to define this command's 
                                                interface into it 
    :rtype: None
    """
    p = subparser
    p.description = description
    define_pub_opts(p)  # defines AIPID and --bag-parent-dir

    p.add_argument("filepaths", metavar="FILEPATH", type=str, nargs='*',
                   help="path to a file component to update. If none are listed, all files will be checked")
    p.add_argument("-d", "--data-dir", metavar="DIR", type=str, dest="datadir", default=None,
                   help="directory that contains the data files that are part of this submission "+
                        "(This is equivalent to reviewdir/record-number.)")
    p.add_argument("-f", "--force", action="store_true", dest="force",
                   help="Force a re-examination of all (requested) files.  Without this, files will only "
                        "be examined if it appears they need to be, either because the underlying file is "
                        "newer than the last scan or the file is missing size or checksum data")
    p.add_argument("-C", "--correct-cs-file", action="store_true", dest="correctcsf",
                   help="correct the checksum file if it appears to be in disagreement with the value "
                        "in the NERDm metadata")
    p.add_argument("-n", "--dry-run", action="store_true", dest="dryrun",
                   help="Do not make any actual changes; only print out what files will be examined")
    p.add_argument("-V", "--validate", action="store_true", dest="validate",
                   help="validate the NERDm metadata after update.")

    return None

def execute(args, config=None, log=None):
    if not log:
        log = logging.getLogger(default_name)
    if not config:
        config = {}

    if isinstance(args, list):
        # cmd-line arguments not parsed yet
        p = argparse.ArgumentParser()
        load_into(p)
        args = p.parse_args(args)

    if not args.aipid:
        raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
    args.aipid = args.aipid[0]
    usenm = args.aipid
    if len(usenm) > 11:
        usenm = usenm[:4]+"..."+usenm[-4:]
    log = log.getChild(usenm)

    # create bagger from inputs
    bgr = create_bagger(args, config, log)

    if len(bgr.datafiles) < 1:
        log.info("No data files found (resubmit updated POD if necessary)")
        return

    # determine which files to look at
    if args.filepaths:
        missing = []
        for f in args.filepaths:
            if f not in bgr.datafiles:
                missing.append(f)
        if missing:
            raise PDRCommandFailure(default_name, "%s: requested files not found (resubmit POD?):\n  %s",
                                    args.aipid, "\n  ".join(missing))

    if not args.filepaths:
        args.filepaths = list(bgr.datafiles.keys())
        if args.dryrun or args.verbose:
            log.info("%s: will check all available files", args.aipid)

    examine_files = which_files(args, bgr, log)
    
    # now examine each selected file
    fixed_sha_files = []
    updated_mdata = []
    for filepath, srcfile in examine_files.items():
        xcs = None
        try:
            if not args.dryrun:
                xcs = examine_file(bgr, filepath, srcfile, log)
            updated_mdata.append(filepath)
        except Exception as ex:
            log.error("%s: Unable to update file metadata: %s", filepath, str(ex))
            log.warning("Skipping checksum file check")
            continue

        if filepath.endswith(".sha256"):
            log.debug("Skipping checksum file check on checksum file")
            continue

        # check for a corresponding checksum file
        chksumfile = srcfile + ".sha256"
        chksumpath = filepath + ".sha256"
        if os.path.exists(chksumfile):
            if not xcs:
                dfmd = bgr.bagbldr.bag.nerd_metadata_for(filepath)
                xcs = dfmd.get("checksum", {}).get("hash")

            if not xcs and (args.dryrun or args.verbose):
                log.debug("%s: NERDm checksum data not set yet", filepath)

            try:
                with open(chksumfile) as fd:
                    fcs = fd.readline().split()[0]
            except Exception as ex:
                log.warn("%s: unable to extract checksum hash value: %s", chksumfile, str(ex))
                if args.correctcsf:
                    log.info("%s: updating corrupted checksum file anyway", chksumpath)
                fcs = "1"
        else:
            fcs = "1"

        if xcs != fcs:
            if args.dryrun or not args.correctcsf:
                log.warn("%s: checksum file has incorrect value in it", chksumpath)
            elif args.correctcsf:
                try:
                    with open(chksumfile, 'w') as fd:
                        fd.write(xcs)
                except Exception as ex:
                    log.error("%s: unable to write out checksum: %s", chksumfile, str(ex))

                if chksumpath in bgr.datafiles:
                    examine_file(bgr, chksumpath, chksumfile, log)
            fixed_sha_files.append(filepath)

    if args.dryrun:
        log.info("%s: will examine %d file%s in total",
                 args.aipid, len(updated_mdata),
                 "s" if len(updated_mdata) != 1 else "")
    else:
        log.info("%s: examined %d file%s in total", 
                 args.aipid, len(updated_mdata),
                 "s" if len(updated_mdata) != 1 else "")
    if not args.correctcsf:
        log.info("%s: %d checksum file%s do not match metadata hash",
                 args.aipid, len(fixed_sha_files),
                 "s" if len(fixed_sha_files) != 1 else "")
    else:
        log.info("%s: %d checksum file%s were fixed",
                 args.aipid, len(fixed_sha_files),
                 "s" if len(fixed_sha_files) != 1 else "")

def create_bagger(args, config, log):
    # set the input bag
    workdir, bagparent, bagdir = determine_bag_path(args, config)
    if not os.path.isdir(bagdir):
        raise PDRCommandFailure(default_name, "Input bag does not exist (as a dir): "+bagdir, 2)
    log.info("Found input bag at "+bagdir)

    # create a Bagger instance for it
    if config.get('bagger') and isinstance(config['bagger'], Mapping):
        config = deepcopy(config)
        config.update(config['bagger'])
        del config['bagger']

    bgrmdfile = os.path.join(bagdir, "metadata", MIDASMetadataBagger.BGRMD_FILENAME)
    if not args.datadir and os.path.isfile(bgrmdfile):
        bgr = MIDASMetadataBagger.forMetadataBag(bagdir, config, for_pres=True)
    else:
        if not args.datadir:
            if not config.get('review_dir'):
                raise PDRCommandFailure(default_name, "Unable to determine data (review) directory", 3)
            args.datadir = os.path.join(config['review_dir'], midas2recno(args.aipid))
        bgr = MIDASMetadataBagger(args.aipid, bagparent, args.datadir, config.get('bagger',{}))
                                  
    bgr.ensure_res_metadata()  # sets self.datafiles
    return bgr

def which_files(args, bagger, log):
    lasttime = 0.0
    if not args.force:
        bmd = bagger.baggermd_for("")
        lasttime = bmd.get('last_file_examine', 0.0)

    if not args.filepaths:
        args.filepaths = list(bagger.datafiles.keys())

    examine_files = {}
    for filepath in args.filepaths:
        if filepath not in bagger.datafiles:
            if bagger.bagbldr.bag.comp_exists(filepath):
                msg = "data file for this path not found in data dir"
            else:
                msg = "not a file path registered in metadata bag"
            raise PDRCommandFailure(default_name, "%s: %s" % (filepath, msg), 4)

        srcpath = bagger.datafiles[filepath]
        examine = args.force
        dfmd = None
        if not examine:
            dfmd = bagger.bagbldr.bag.nerd_metadata_for(filepath)
            examine = 'size' not in dfmd or 'checksum' not in dfmd
            if args.dryrun or args.verbose:
                log.debug("%s: will examine datafile, %s: missing key metadata", args.aipid, filepath)

        if not examine:
            if srcpath and moddate_of(srcpath) > lasttime:
                examine = True
                if args.dryrun or args.verbose:
                    log.debug("%s: will examine datafile, %s: data file appears updated",
                              args.aipid, filepath)
                
            elif os.path.exists(os.path.join(os.path.dirname(bagger.bagbldr.bag.nerd_file_for(filepath)),
                                             UNSYNCED_FILE)):
                examine = True
                if args.dryrun or args.verbose:
                    log.debug("%s: will examine datafile, %s: marked as unsynced.",
                              args.aipid, filepath)
        if examine:
            examine_files[filepath] = srcpath

    return examine_files

def examine_file(bagger, filepath, location, log):
    """
    examine the referenced file and update its metadata accordingly.  
    """
    md = bagger.bagbldr.describe_data_file(location, filepath, True)
    if '__status' in md:
        md['__status'] = "updated"

    md = bagger.bagbldr.update_metadata_for(filepath, md, None,
                                            "cli-driven metadata update for file, "+filepath)
    if '__status' in md:
        del md['__status']
        bagger.bagbldr.replace_metadata_for(filepath, md, '')
    bagger._mark_filepath_synced(filepath)

    out = md.get('checksum', {}).get('hash')
    if not out:
        raise RuntimeException(filepath+": Failed to update checksum for unknown reason")
    return out


