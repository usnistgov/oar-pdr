# #! /bin/bash
# #
# prog=`basename $0`
# execdir=`dirname $0`
# [ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
# execdir=`(cd $execdir && pwd)`
# basedir=`dirname $execdir`
# oarmd=$basedir/oar-metadata/docker
# [ -d "$oarmd" ] || {
#     echo "Missing oar-metadata submodule!"
#     exit 5
# }
# set -ex

# $oarmd/buildall.sh
# docker build -t oarpdr/pdrtest $execdir/pdrtest
