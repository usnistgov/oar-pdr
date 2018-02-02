#! /bin/bash
#
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
codedir=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

set -e

(docker images | grep -qs oar-pdr/pdrtest) || {
    echo "${prog}: Docker image mdtests not found; building now..."
    echo '+' $execdir/dockbuild.sh -q
    $execdir/dockbuild.sh -q || {
        echo "${prog}: Failed to build docker containers; see" \
             "docker/dockbuild.log for details."
        false
    }
}

ti=
(echo "$@" | grep -qs shell) && ti="-ti"

echo docker run $ti --rm -v $codedir:/dev/oar-pdr oar-pdr/pdrtest "$@"
exec docker run $ti --rm -v $codedir:/dev/oar-pdr oar-pdr/pdrtest "$@"
