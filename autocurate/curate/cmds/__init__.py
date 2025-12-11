"""
utilities for running scripts
"""
import sys

USAGE_ERROR = 2

def carp(prog, msg):
    print >> sys.stderr, "%s: %s" % (prog, msg)

class FatalError(Exception):

    def __init__(self, msg, excode=1):
        super(FatalError, self).__init__(msg)
        self.excode = excode

