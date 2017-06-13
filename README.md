# Publishing Data Repository (oar-pdr)

This repository provides the implementation of the NIST Publishing
Data Repository (PDR) platform, the technology that provides the NIST
Data Publishing Repository (DPR).

## Contents

```
docker/    --> Docker containers for running tests
java/      --> Java source code (none at this time)
python     --> Python source code for the metadata and preservation
                services
scripts    --> Tools for running the services and running all tests
```

## Prerequisites

The oar-metadata package is a prerequisite which is configured as git
sub-module of this package.  This means after you clone the git
repository, you should use `git submodule` to pull in the oar-metadata
package into it:

```
git submodule update --init
```

See oar-metadata/README.md for a list of its prerequisites.

As an alternative to explicitly installing prerequisites to run
the tests, the `docker` directory contains scripts for building a
Docker container with these installed.  Running the `docker/run.sh`
script will build the containers (caching them locally), start the
container, and put the user in a bash shell in the container.  From
there, one can run the tests or use the `jq` and `validate` tools to
interact with metadata files.




