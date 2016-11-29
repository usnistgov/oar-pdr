# jq conversion library from NIST-PDL-POD to NERDm schemas
#
# To convert a single POD Dataset document, execute the following:
#
#   jq -L $JQLIB --arg id ID -f $JQLIB/podds2nerdres.jq DSFILE
#
# Here, JQLIB is the directory containing this library, ID is the identifier
# that should be assigned for that record, and DSFILE is a file containing a
# POD Dataset object.
#

import "pod2nerdm" as nerdm;

nerdm::podds2resource
