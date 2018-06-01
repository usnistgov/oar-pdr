#! /bin/bash 
#
# Supported commands
#   build         build the angular components via scripts/makedist.angular
#                 (any arguments are passed onto this scripts/makedist.angular)
#
#   test          run the angular tests via scripts/testall.angular
#                 (any arguments are passed onto this scripts/testall.angular)
#
#   shell         run an interactive bash shell in this container
#
set -e

[ "$DEVUID" == "" ] && {
    echo "DEVUID env var not set"
    false
}
[ `id -un` == "root" ] && exec gosu $DEVUID $0 "$@"

[ -f "$DOCKERDIR/env.sh" ] && . env.sh

args=
cmds=
while [ "$1" != "" ]; do
    case "$1" in
        -*)
            args="$args $1"
            ;;
        *)
            cmds="$cmds $1"
            ;;
    esac
    shift
done

function build {
    echo '+' $CODEDIR/scripts/makedist.angular "$@"
    $CODEDIR/scripts/makedist.angular "$@"
}

function test {
    echo '+' $CODEDIR/scripts/testall.angular "$@"
    $CODEDIR/scripts/testall.angular "$@"
}

if echo "$cmds" | grep -qsw build; then
    build "$args"
fi

if echo "$cmds" | grep -qsw test; then
    test
fi

if echo "$cmds" | grep -qsw shell; then
    exec /bin/bash
fi
