#! /bin/bash
#
# Processes command line arguments for run.sh and defines functions it
# can use.
#
set -e
true ${prog:=_run.sh}

[ -z "$PACKAGE_DIR" ] && {
    echo "${prog}: \$PACKAGE_DIR is not set."
    exit 10
}

true ${OAR_BUILD_DIR:=$PACKAGE_DIR/oar-build}
true ${OAR_DOCKER_DIR:=$PACKAGE_DIR/docker}
true ${RM:=}

true ${PACKAGE_NAME:=`basename $PACKAGE_DIR`}
true ${SHELL_COMMANDS:="bshell shell"}

LOGFILE=run.log
LOGPATH=$PWD/$LOGFILE
. $OAR_BUILD_DIR/_logging.sh

function set_interactive {
    shcmds=:`echo $SHELL_COMMANDS | perl -pe 's/ +/:/'`:
    cmd=$1
    [ -z "$cmd" ] && cmd=build

    INTERACTIVE=
    if (echo $shcmds | grep -qs :${cmd}:); then
        INTERACTIVE=-ti
    else
        true
    fi
}

function collect_run_opts {
    RUN_OPTS="$RM -e PACKAGE_NAME=$PACKAGE_NAME -v ${PACKAGE_DIR}:/dev/$PACKAGE_NAME"
}

function setup_run {
    set_interactive
    collect_run_opts
}

function build_images {
    echo '+' buildall.sh $QUIET
    $OAR_DOCKER_DIR/buildall.sh $QUIET
}

function help {
    helpfile=$OAR_BUILD_DIR/run_help.txt
    [ -f "$OAR_DOCKER_DIR/run_help.txt" ] && \
        helpfile=$OAR_DOCKER_DIR/run_help.txt
    sed -e "s/%PROG%/$prog/g" $helpfile
}

CL4LOG=$@

while [ "$1" != "" ]; do
    case "$1" in
        --logfile=*)
            LOGPATH=`echo $1 | sed -e 's/[^=]*=//'`
            ;;
        -l)
            shift
            LOGPATH=$1
            ;;
        --quiet|-q)
            QUIET=-q
            ;;
        --no-remove|-R)
            RM=
            ;;
        --build|-b)
            BUILD_FIRST=1
            ;;
        --help|-h)
            help
            exit 0
            ;;
        -*)
            echo "${prog}: unsupported option:" $1 "(should this be placed after cmd?)"
            false
            ;;
        *)
            # remainder of arguments will be passed to entrypoint script
            break
            ;;
    esac
    shift
done
[ $# -eq 0 ] && set -- "build"

(echo $LOGPATH | egrep -qs '^/') || LOGPATH=$PWD/$LOGPATH

    
