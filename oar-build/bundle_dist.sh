#! /bin/bash
#
# bundle_dist.sh:  bundle up the data products in the dist directory into a
#                  zip file
#
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
codedir=`(cd $execdir/.. > /dev/null 2>&1; pwd)`
distdir=$codedir/dist

true ${PACKAGE_NAME:=`basename $codedir`}
true ${DIST_BUNDLE:=${PACKAGE_NAME}-dist.zip}

distpath=$codedir/$DIS_BUNDLE

set -e
cd $distdir
set -x
zip -r $distpath *
