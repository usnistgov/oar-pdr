#! /bin/bash
#
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
codedir=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

set -e

$execdir/buildall.sh

ti=
(echo "$@" | grep -qs shell) && ti="-ti"

echo docker run $ti --rm -v $codedir:/dev/oar-pdr oarpdr/pdrtest "$@"
exec docker run $ti --rm -v $codedir:/dev/oar-pdr oarpdr/pdrtest "$@"
