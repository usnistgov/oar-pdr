# A Sample Fedora Data Publication

This directory provides scripts for loading a test data publication
into a Fedora instance.  They operate on a submission information
package (SIP) that conforms to and provides metadata for the PDR
model.  A sample SIP that these scripts can operate on is available
only internally to NIST (see http://odiwiki.nist.gov/PubDataRepo for
details).

Included are two loading scripts:

* `installDP.sh` -- the main script that loads the data package into a
Fedora instance.  Command-line options can control where it gets
loaded, and verbosity or simulation mode can be turned on to see the
calls made to the rest interface.  

* `installSample.sh` -- a script that calls installDP.sh as well as
create its ancestor collections if necessary.  The intent is of this
script is to quietly load the data package into the default parent
collection "/DPR/vol1".

To load the sample dataset into Fedora, type:

```bash
bash installSample.sh
```
