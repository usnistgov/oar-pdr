"""
This module creates bags from Submission Information Packages (SIP) of known
organization.

The SIPBagger base class provides the abstract interface for preparing
a bag.  The implementation classes use knowledge of particular SIPs to 
create bags (via the BagBuilder class).  For example, the MIDASBagger 
understands how to bag up data provided by MIDAS.  
"""

from midas import MIDASMetadataBagger
from prepupd import UpdatePrepService
