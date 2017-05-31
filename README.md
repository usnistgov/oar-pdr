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
sub-module of this package.  This means if you clone the git
repository, you should get the oar-metadata automatically.  See
oar-metadata/READM.md for a list of its prerequisites.




