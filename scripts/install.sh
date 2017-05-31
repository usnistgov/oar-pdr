#! /bin/bash
#
# This script installs the PDR system (including metadata support fronm the
# oar-metadata submodule.
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD

base=`(cd $execdir/.. > /dev/null 2>&1; pwd)`
oarmd_pkg=$base/oar-metadata

[ -d "$oarmd_pkg" -a -d "$oarmd_pkg/python/nistoar" ] || {
    echo "$prog: Missing oar-metadata submodule"
    echo Clone the oar-metadata repo in this directory
    exit 3
}

. $oarmd_pkg/scripts/_install-env.sh

#install the PDR python library
mkdir -p $PY_LIBDIR
echo Installing python libraries into $PY_LIBDIR...
(cd $SOURCE_DIR/python && python setup.py install --install-purelib=$PY_LIBDIR --install-scripts=$BINDIR)

#install the JAVA jars
# None at this time

$oarmd_pkg/scripts/install_extras.sh --install-dir=$INSTALL_DIR

mkdir -p $INSTALL_DIR/var/logs
mkdir -p $INSTALL_DIR/var/testmidas/work
echo cp -r $SOURCE_DIR/python/nistoar/pdr/preserv/tests/data/midassip \
           $INSTALL_DIR/var/testmidas/midas
cp -r $SOURCE_DIR/python/nistoar/pdr/preserv/tests/data/midassip \
      $INSTALL_DIR/var/testmidas/midas
