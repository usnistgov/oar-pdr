"""
package that provides implementations of commands that can part of a command-line interface and 
which are part of the publishing workflow.  See nistoar.pdr.cli and the pdr script for info on 
the general CLI infrastructure.

This module defines a set of subcommands to a command called (by default) "pub".  These subcommands
include
  - prepupd:    setup a metadata bag based on the last published version of a specified dataset.
  - servenerd:  extract the full NERDm record from a bag and copy it to an export directory (or stdout)
  - fix:        fix various special problems via subcommands
"""
import os
from ... import cli

default_name = "pub"
help = "manage a publishing workflow via subcommands"
description = \
"""apply an action that is part of the publishing workflow"""

def load_into(subparser, as_cmd=None):
    """
    load this command into a CLI by defining the command's arguments and options.
    :param argparser.ArgumentParser subparser:  the argument parser instance to define this command's 
                                                interface into it 
    """
    from . import prepupd, servenerd, fix, validate, setver, author
    
    subparser.description = description

    if not as_cmd:
        as_cmd = default_name
    out = cli.CommandSuite(as_cmd, subparser)
    out.load_subcommand(prepupd)
    out.load_subcommand(author)
    out.load_subcommand(setver)
    out.load_subcommand(validate)
    out.load_subcommand(servenerd)
    out.load_subcommand(fix)
    return out

def define_pub_opts(subparser):
    """
    define some arguments that apply to all pub subcommands.  These are:
     - AIPID -- the AIP ID of the bag to operate on; its value is saved as the "aipid" arg attribute
     - --bag-parent-dir -- the directory to look for the AIP bag directory in; saved as "bagparent"
    """
    p = subparser
    p.add_argument("aipid", metavar="AIPID", type=str, nargs=1,
                   help="the AIP-ID for the bag to examine or the file path to the bag's root directory")
    p.add_argument("-b", "--bag-parent-dir", metavar="DIR", type=str, dest='bagparent',
                   help="the directory to look for the specified bag; if not specified, it will either "+
                   "set to the metadata_bag_dir config or otherwise to the working directory.  Ignored "+
                   "if AIPID is given as a path.")
    return p

def determine_bag_path(args, config):
    """
    determine the full path to the AIP bag as indicated by the given arguments and configuration.  This 
    function assumes the AIPID and --bag-parent-dir arguments defined by defin_pub_opts() and looks for
    'working_dir' and 'metadata_bag_dir' in the given configuration.  
    :param argparse.Namespace args:  the parsed command-line arguments
    :param dict config:              the configuration data 
    :return: 3-element tuple containing, in order, the determined paths to the working directory,
             the bag parent directory, and 
    """
    # working dir: cl arg takes precedence over configuration;
    # a relative path assumed relative to current dir
    workdir = config.get('working_dir', os.getcwd())
    if hasattr(args, 'workdir') and args.workdir:
        workdir = args.workdir
    workdir = os.path.abspath(workdir)

    # bag parent dir: cl arg takes precendence over config
    bagparent = config.get('metadata_bag_dir')
    if os.sep in args.aipid:
        # AIP is given as a path: assume a parent based on that path.  Assume relative to cwd,
        # if not there, try relative to workdir
        bagpath = os.path.abspath(args.aipid)
        if not os.path.exists(bagpath):
            if hasattr(args, 'workdir') and args.workdir:
                bagpath = os.path.join(args.workdir, args.aipid)
        bagparent = os.path.dirname(bagpath)
        args.aipid = os.path.basename(bagpath)  # get real aipid
    elif args.bagparent:
        bagparent = args.bagparent
    if not bagparent:
        bagparent = workdir
    elif not bagparent.startswith('.'+os.sep) and not bagparent.startswith('..'+os.sep) and \
         not os.path.isabs(bagparent):
        # if bag parent was specified as relative, assume relative to workdir
        bagparent = os.path.join(workdir, bagparent)
    bagparent = os.path.abspath(bagparent)

    # now we know full expected path to the bag
    bagdir = os.path.join(bagparent, args.aipid)

    return (workdir, bagparent, bagdir)
