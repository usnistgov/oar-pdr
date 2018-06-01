#!/bin/bash

set -e

[ "$DEVUID" == "" ] && {
    echo "DEVUID env var not set"
    false
}
[ `id -un` == "root" ] && exec gosu $DEVUID $0 "$@"

[ -f "$DOCKERDIR/env.sh" ] && . env.sh

op=$1
[ "$op" == "" ] && op=build
shift
case "$op" in
    build|makedist)
        echo '+' scripts/makedist.angular "$@"
        $CODEDIR/scripts/makedist.angular "$@"
        ;;
    shell)
        exec /bin/bash
        ;;
esac

