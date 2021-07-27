"""
package that enables README file generation from the command-line.
See nistoar.pdr.cli and the pdr script for info on the general CLI infrastructure.

This module defines a set of subcommands to a command called (by default) "author".  These subcommands
include
  - add:  creates a README.txt file and adds it to the bag
  - gen:  generate a README.txt file based on the NERDm metadata and stream it to standard out
  - show: stream the existing README.txt file to standard out
"""
from __future__ import print_function
import sys, os, logging, re
from collections import OrderedDict
from copy import deepcopy

from nistoar.pdr import cli
from nistoar.pdr.preserv.bagit import NISTBag
from nistoar.pdr.publish.readme import ReadmeGenerator
from nistoar.pdr.utils import read_nerd, NERDError
from nistoar.nerdm import PUB_SCHEMA_URI
from . import validate as vald8, define_pub_opts, determine_bag_path

default_name = "readme"
help = "generate, add, and display the dataset's README text"
description = """
  This command provides a suite of subcommands to generate, add, or display a bag's README file based on 
  its NERDm metadata.
"""

def load_into(subparser, as_cmd=None):
    """
    load this command into a CLI by defining the command's arguments and options.
    :param argparser.ArgumentParser subparser:  the argument parser instance to define this command's 
                                                interface into it 
    """
    p = subparser
    p.description = description

    if not as_cmd:
        as_cmd = default_name
    out = cli.CommandSuite(as_cmd, p)
    out.load_subcommand( GenReadmeCmd())
#    out.load_subcommand( AddReadmeCmd())
#    out.load_subcommand(ShowReadmeCmd())
    return out

class ReadmeCmd(object):
    """
    a base class for readme commands.  An instance of this class serves the same role as a command
    submodule in the PDRCLI framework.
    """

    def __init__(self, cmdname, logger=None):
        self.name = cmdname
        if not logger:
            logger = logging.getLogger(self.default_name)
        self.deflog = logger

    @property
    def default_name(self):
        """
        the name this command get invoked by.   This property is part of the standard PDRCLI interface
        """
        return self.name

    def define_common_opts(self, subparser):
        """
        Add arguments to the parser that are common across all commands
        :param ArgumentParser subparser:   the argparse subparser instance to add options to 
        """
        return define_pub_opts(subparser)

    def define_gen_opts(self, subparser):
        """
        Add arguments to the parser that control the creation of README text from the NERDm metadata
        """
        g = subparser
        g.add_argument("-B", "--brief", action="store_true", dest="brief",
                       help="create a brief version of the README (omit file listing)")
        g.add_argument("-P", "--without-prompts", action="store_false", dest="withprompts",
                       help="do not include editing prompts within the generated README")
        g.add_argument("-N", "--from-nerdm-file", metavar="FILE", type=str, dest="srcfile",
                       help="read the NERDm metadata from the given FILE rather from the metadata in the bag")
        g.add_argument("-T", "--template-dir", metavar="DIR", type=str, dest="tmpldir",
                       help="look for README template files in DIR")

    def _fail(self, message, exitcode=1):
        raise cli.PDRCommandFailure(self.default_name, message, exitcode)

class GenReadmeCmd(ReadmeCmd):
    """
    a CLI command for generating README text.  By default, it is printed to standard out.
    """
    _default_name = "gen"
    description = """
       this command generated README text and prints it (by default) to standard out.
    """
    help = "generate README text"
    usage = "[-b DIR] [-B] [-P] [-T DIR] [-o FILE] AIPID | -N FILE | -h"

    def __init__(self, cmdname=None):
        if not cmdname:
            cmdname = self._default_name
        super(GenReadmeCmd, self).__init__(cmdname)

    def load_into(self, subparser):
        """
        load the command-line arguments into the subparser
        """
        p = subparser
        p.usage = self.usage
        p.add_argument("aipid", metavar="AIPID", type=str, nargs='?',
                       help="the AIP-ID for the bag to examine or the file path to the bag's root directory")
        p.add_argument("-b", "--bag-parent-dir", metavar="DIR", type=str, dest='bagparent',
                       help="the directory to look for the specified bag; if not specified, it will either "+
                       "set to the metadata_bag_dir config or otherwise to the working directory.  Ignored "+
                       "if AIPID is given as a path.")

        self.define_gen_opts(p)
        p.add_argument("-o", "--output-file", metavar="FILE", type=str, dest="outfile", default="-",
                       help="write the README contents to FILE (instead of standard out)")
        
        return self

    def execute(self, args, config=None, log=None):
        if not log:
            log = self.log
        if not config:
            config = {}

        if isinstance(args, list):
            # cmd-line arguments not parsed yet
            p = argparse.ArgumentParser()
            self.load_into(p)
            args = p.parse_args(args)

        nerdm = None
        if args.srcfile:
            if not os.path.isfile(args.srcfile):
                self._fail("Input bag does not exist (as a file): "+args.srcfile, 1)
            try:
                nerdm = read_nerd(args.srcfile)
            except NERDError as ex:
                self._fail(str(ex), 2)

        else: 
            if not args.aipid:
                raise PDRCommandFailure(default_name, "AIP ID not specified", 1)
            args.aipid = args.aipid[0]
            usenm = args.aipid
            if len(usenm) > 11:
                usenm = usenm[:4]+"..."+usenm[-4:]
            log = log.getChild(usenm)

            # find the input bag
            workdir, bagparent, bagdir = determine_bag_path(args, config)
            if not os.path.isdir(bagdir):
                self._fail("Input bag does not exist (as a dir): "+bagdir, 2)
            log.info("Found input bag at "+bagdir)

            bag = NISTBag(bagdir)
            nerdm = bag.nerdm_record(True)

        if not args.outfile or args.outfile == "-":
            out = sys.stdout

        else:
            if os.path.isdir(args.outfile):
                args.outfile = os.join(args.outfile, "README.txt")
            elif not os.path.isdir(os.path.dirname(args.outfile)):
                self._fail("Output directory does not exist (as a directory): "+
                           os.path.dirname(args.outfile), 2)
            out = open(args.outfile, 'w')

        try:
            genr8tr = ReadmeGenerator(args.tmpldir)
            genr8tr.generate(nerdm, out, args.withprompts, args.brief)

        finally:
            if args.outfile and args.outfile != "-":
                out.close()
