"""
package that provides implementations of commands that can part of a command-line interface and 
which are part of the preservation process.  See nistoar.pdr.cli and the pdr script for info on 
the general CLI infrastructure.

This module defines a set of subcommands to a command called (by default) "preserve".  These subcommands
include
  - midas:      preserve an SIP according to the midas3 conventions
  - status:     print information about the preservation status of an SIP
"""
from . import midas3
from ... import cli

default_name = "preserve"
help = "manage the preservation of SIPs via subcommands"
description = \
"""
This command is typically for initiating the preservation of prepared submission information packages 
(SIPs), but it can do other things related to preservation as well.
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
    out.load_subcommand(midas3, "midas")
    return out

    
