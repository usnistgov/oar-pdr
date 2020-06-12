# PDR Publishing Services

This directory provides the `pdr-publish` software product, an
implementation for PDR publishing services.  Written in Python, this
software supports the PDR publishing process for (in the language of
the Open Archival Information System reference model) ingesting a
submission information package and transforming it into an archival
information package and a dissemination information package.

This software currently is compatible with with Python 2.7 (2.7.11
through 2.7.13).  An update to support Python 3.5 is expected in the
near future.

## Prerequisites

This software requires Python 2.7.X (where 11 <= X <= 13).

The oar-metadata package is a prerequisite which is configured as git
sub-module of this package.  This means after you clone the oar-pdr git
repository, you should use `git submodule` to pull in the oar-metadata
package into it:
```
git submodule update --init
```

See oar-metadata/README.md for a list of its prerequisites.

In addition to oar-metadata and its prerequisites, this package requires
the following third-party packages:

* multibag-py v0.4 or later
* bagit v1.6.X
* fs v2.X.X

## Building and Testing the Software

The Python build tool, `setup.py`, is used to build and test the
software.  To build, type while in this directory:

```
  python setup.py build
```

This will create a `build` subdirectory and compile and install the
software into it.  To install it into an arbitrary location, type

```
  python setup.py --prefix=/oar/home/path install
```

where _/oar/home/path_ is the path to the base directory where the
software should be installed.

The `makedist` script (in [../scripts](../scripts)) will package up an
installed version of the software into a zip file, writing it out into
the `../dist` directory.  Unpacking the zip file into a directory is
equivalent to installing it there.

To run the unit tests, type:

```
  python setup.py test
```

The `testall.python` script (in [../scripts](../scripts)) will run
some additional integration tests after running the unit tests.  In
the integration tests, the web service versions of the services are
launched on local ports to test for proper responses via the web
interface.

