# PDR Metadata Support (via NERDm)

This directory provides support for the PDR's metadata model
(NERDm). In includes the JSON Schema definitions for NERDm types
(under `model`) and translators (under `jq`).

## Prerequisites

Record translation and validation require a few third-party tools:

* Python 2.7.X
* Python library: jsonschema 2.5.x or later
* Python library: jsonspec 0.9.16
* Python library: requests
* jq (build with libonig2)

As an alternative to explicitly installing these to run the tests, the
`docker` directory contains scripts for building a Docker container
with these installed.  Running the `docker/run.sh` script will build
the containers (caching them locally), start the container, and put
the user in a bash shell in the container.  From there, one can run
the tests or use the `jq` and `validate` tools to interact with
metadata files.  

## Converting a POD record

If relying on the Docker container for the prerequisite tools (see
above), start the container via the `run.sh` to start a bash shell.
Inside this shell, the curent directory will be `oar-pdr/metadata`
(i.e. the directory that contains this README).  

To convert a single POD format Dataset document into a NERDm Resource
document, run the `jq` command with the following pattern:

```
jq -L jq --arg id ID -f jq/podds2nerdres.jq POD-FILE > NERDM-FIlE
```

where POD-FILE is the input POD Dataset filename, NERDM-FILE is the
output NERDm Resource document filename, and ID is the identifier to
assign to the output record.  The `jq/tests/data` a sample
POD Dataset document, `janaf_pod.json`; to convert it, then, to NERDm,
type:

```
jq -L jq --arg id ark:ID -f jq/podds2nerdres.jq jq/tests/data/javaf_pod.json > janaf_nerdm.json
```

The test data directory also contains a copy of the NIST PDL Catalog;
it can be converted to an array of NERDm Resource records with the
following:

```
jq -L jq --arg id ark:ID -f jq/podcat2nerdres.jq jq/tests/data/nist-pdl-oct2016.json > nist-resources.json
```

## Converting a POD Catalog

An entire POD Catalog document can be converted to a set of NERDm
Resource files (i.e. each output file containing one Resource record)
using the `pdl2resource.py` script.  Here's an example running the
script on the example PDL file that is in the `jq/tests/data` directory:

```
scripts/pdl2resources.py -d tmp jq/tests/data/nist-pdl-oct2016.json
```

The `-d` option sets the directory where the output files are stored.
Other command-line options allow one to convert only a portion of the
datasets found in the file; run with the `--help` option to see the
details.

With this script each output resource docuemnt is assigned an ARK
identifier.  

## Validating a NERDm record

This module includes a schema documents that can be used to validate
NERDm record.  The `validate` command accomplishes this.  For example,
to validate the `janaf_nerdm.json` file, type:

```
validate -L model janaf_nerdm.json
```


## Running Tests

To run all the tests associated with this metadata component (assuming
all prerequisites are installed), type:

```
  scripts/testall.py
```

If prerequisites are not installed (e.g. they're not easily
installable), you can test the metadat component via docker as
described above.  To run the tests within docker, type:

```
  docker/run.sh testall
```


