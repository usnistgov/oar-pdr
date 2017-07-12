#! /bin/bash
#
# This script creates a distribution bundle for installing into the OAR system
# via oar-docker
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
base=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

true ${SOURCE_DIR:=$base}

# handle command line options
while [ "$1" != "" ]; do 
  case "$1" in
    --dist-dir=*)
        DIST_DIR=`echo $1 | sed -e 's/[^=]*=//'`
        ;;
    --dist-dir)
        shift
        DIST_DIR=$1
        ;;
    --source-dir=*|--dir=*)
        SOURCE_DIR=`echo $1 | sed -e 's/[^=]*=//'`
        ;;
    -d|--dir|--source-dir)
        shift
        SOURCE_DIR=$1
        ;;
    -*)
        echo "$prog: unsupported option:" $1
        false
        ;;
    *)
        echo "Warning: ignoring argument: $1"
        ;;
  esac
  shift
done

true ${DIST_DIR:=$SOURCE_DIR/dist}

installdir=$DIST_DIR/pdr
set -x
mkdir -p $installdir
scripts/install.sh --install-dir=$installdir

(cd $DIST_DIR && zip -qr pdr.zip pdr)
