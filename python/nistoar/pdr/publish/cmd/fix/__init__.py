"""
package that provides implementations of special-purpose commands that fix specific issues with 
bags and SIPs generally. See nistoar.pdr.cli and the pdr script for info on 
the general CLI infrastructure.

This module defines a set of subcommands to a command called (by default) "fix".  These subcommands
include
  - topics:  set the research topics as topic vocabulary based on the POD themes property
"""
# from . import topics
from .... import cli
from . import topics

default_name = "fix"
help = "fix specials SIP problems via subcommands"
description = \
"""This provides a suite of subcommands that fix special problems with bags and SIPs"""

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
    out.load_subcommand(topics)
    return out

    
