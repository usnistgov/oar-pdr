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

distvol=
distdir=
cmd=
args=()
while [ "$1" != "" ]; do
    case "$1" in
        --dist-dir)
            shift
            distdir="$1"
            mkdir -p $distdir
            distdir=`(cd $distdir > /dev/null 2>&1; pwd)`
            distvol="-v ${distdir}:/app/dist"
            args=(${args[@]} "--dist-dir=/app/dist")
            ;;
        --dist-dir=*)
            distdir=`echo $1 | sed -e 's/[^=]*=//'`
            mkdir -p $distdir
            distdir=`(cd $distdir > /dev/null 2>&1; pwd)`
            distvol="-v ${distdir}:/app/dist"
            args=(${args[@]} "--dist-dir=/app/dist")
            ;;
        -*)
            args=(${args[@]} $1)
            ;;
        *)
            if [ -z "$cmd" ]; then
                cmd=$1
            else
                args=(${args[@]} $1)
            fi
            ;;
    esac
    shift
done

echo '+' docker run $ti --rm -v $codedir:/dev/oar-pdr $distvol oar-pdr/pdrtest $cmd "${args[@]}"
exec docker run $ti --rm -v $codedir:/dev/oar-pdr $distvol oar-pdr/pdrtest $cmd "${args[@]}"
