# jq conversion library from NIST-PDL-POD to NERDm schemas
#
# To convert a single POD Dataset document, execute the following:
#
#   jq -L $JQLIB --argjson id null -f $JQLIB/podcat2nerdres.jq CATFILE
#
# Here, JQLIB is the directory containing this library, and CATFILE is a file 
# containing a POD Dataset object.  (In this example, the output records
# are all given a null identifier.)
#

import "pod2nerdm" as nerdm;

nerdm::podcat2resources
