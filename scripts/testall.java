#! /bin/bash
#
# testall:  run all package tests
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
PACKAGE_DIR=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

$PACKAGE_DIR/scripts/setversion.sh
mvn test
