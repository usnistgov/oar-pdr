# PDR Metadata Support (via NERDm)

This directory provides support for the PDR's metadata model
(NERDm). In includes the JSON Schema definitions for NERDm types,
validators, translators, and scripts for loading.

## Contents

```
docker/    --> Docker containers for running tests
java/      --> Java source code supporting NERDm metadata
jq/        --> Conversion libraries for the jq, used for translating POD to NERDm
model/     --> Directory contain JSON Schemas, Context maps, and field 
                 documentation supporting the NERDm metadata framework
 examples/ --> Sample NERDm instance documents
python/    --> Python source code supporting NERDm metadata
scripts/   --> Tools for creating and loading metadata, installing this package,
                 and running all tests
```

## Prerequisites

Record translation, validation, and loading require a few third-party tools:

* Python 2.7.X
* Python library: jsonschema 2.5.x or later
* Python library: jsonspec 0.9.16
* Python library: requests
* jq (build with libonig2)
* Python library: pymongo 3.4.X

Pymongo is used to load metadata into a MongoDB database; thus,
loading also requires a running instance of MongoDB.  Loading unit
tests require that the environment variable MONGO_TESTDB_URL be set to
an accessible MongoDB database; it's value has the form,
'mongodb://HOST[:PORT]/TESTDB'.

As an alternative to explicitly installing the prerequisites to run
the tests, the `docker` directory contains scripts for building a
Docker container with these installed.  Running the `docker/run.sh`
script will build the containers (caching them locally), start the
container, and put the user in a bash shell in the container.  From
there, one can run the tests or use the `jq` and `validate` tools to
interact with metadata files.

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
jq -L jq --arg id ark:ID -f jq/podds2nerdres.jq jq/tests/data/janaf_pod.json > janaf_nerdm.json
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
## Loading data into MongoDB

NERDm resource records, like those created by pdl2resources.py, can be
loaded into a MongoDB database via the script, `ingest-nerdm-res.py`.
To load the records created from the the above example running
pdl2resources.py, where the NERDm records were written to a directory
called `tmp`, simply type:

```
scripts/ingest-nerdm-res.py -M mongodb://localhost/testdb tmp
```

This assumes there is a MongoDB instance running on the local
machine where the user has write access to the `testdb` database.  The
script will validate each NERDm file against the NERDm schemas before
loading it into the database.

Note that NERDm resource records must have unique identifier (stored
in its `@id` property.  Thus loading a new record will overwrite any
previous record with the same identifier.  

### Loading NERDm field documentation

This package also provides support for loading NERDm field
documentation into the database as well, via the
`ingest-field-info.py` script.  This documentation is used by the
Science Data Portal (or any other client) to get information about
available NERDm properties that are available and searchable.

This data is stored in a JSON format, and a default version exists as
`model/nerdm-fields-help.json`.  To load this data into the database,
simply type:

```
  scripts/ingest-field-info.py -M mongodb://localhost/testdb model/nerdm-fields-help.json
```

Each field record has a unique name, so loading a new record will
overwrite any previous record with the same name.  

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


