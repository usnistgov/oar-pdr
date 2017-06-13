#! /bin/bash
#
help() {
    cat <<EOF
Usage: $0 [ -C|--no-create-parent ] [ PARENT ]

Ingest a sample dataset in a Fedora instance, creating its parent collection
if needed.  This wraps ingestDP.sh.

OPTIONS
  -v, --verbose       print out the curl command
  -C, --no-create-parent   Do not create the parent collection
  -h, --host HOST     connect to Fedora on the given HOST; apppend :PORT to the 
                       name if Fedora is not on the default HTTP port
  -r, --rest-url URL  use URL as the base URL for Fedora's rest interface 
                       (overrides -h)
EOF
}

FEDORAHOST=localhost:8984
PARENT=/DPR/vol1
FEDORA=
BASE=
CREATE_PARENT=1
VERBOSE=

set -e
#set -x

function ingest {
    [ "$CREATE_PARENT" != "" ] && create_parent
    [ "$VERBOSE" == "" ] || {
        echo bash ingestDP.sh -u $BASE $VERBOSE
    }
    bash ingestDP.sh -u $BASE $VERBOSE
}

function coll_exists {
    if [ "$1" != "" ]; then
        code=`curl -s -i $FEDORA$1 | egrep '^HTTP/' | tail -1 | sed -re 's#^HTTP/\S+ ##' | awk '{ print $1 }'`
        [ "${code:0:1}" == "2" ] || false
    fi
}

function create_parent {
    path=(`echo $PARENT | sed -e 's#/# #g'`)
    _create_parent ${path[@]}
}

function _create_parent {
    ANSCESTOR=
    while [[ $# -ge 1 ]]; do
        ANSCESTOR=${ANSCESTOR}/$1
        coll_exists $ANSCESTOR || mycurl -X PUT $FEDORA$ANSCESTOR
        shift
    done
}

function mycurl {
    TMP=/tmp/ingestSample.$$
    
    [ "$VERBOSE" == "" ] || \
        echo curl "$@" 
    [ "$SIMULATE" == "" ] && {
        curl -sS -D ${TMP}.hdr "$@" > ${TMP}.out
        status=`egrep '^HTTP/' ${TMP}.hdr | tail -1 | sed -re 's#^HTTP/\S+\s##'`
        code=`echo $status | awk '{ print $1 }'`
        [ "$VERBOSE" == "" ] || {
            [ `cat ${TMP}.out | wc -c` != "0" ] && {
                sed -e 's/^/> /' ${TMP}.out && echo
            }
            echo "> STATUS" $status
            echo
        }
        [ "${TMP:0:5}" == "/tmp/" ] && rm -f ${TMP}*
        [ "${code:0:1}" == "2" ] || {
            [ "$VERBOSE" == "" ] && echo ERROR $status
            false
        }
    }
    
}

args=()
while [[ $# -ge 1 ]]; do
    arg=$1; shift

    case $arg in
        -h|--host)
            FEDORAHOST=$1; shift
            ;;
        --host=*)
            FEDORAHOST=`echo $arg | sed -e s/^--host=//`
            ;;
        -r|--rest-url)
            FEDORA=$1; shift
            ;;
        --rest-url=*)
            FEDORA=`echo $arg | sed -e s/^--host=//`
            ;;
        -v|--verbose)
            VERBOSE=-v
            ;;
        -h|--help)
            help
            exit
            ;;
        *)
            args=(${args[@]} $arg)
            ;;
    esac
done

[ "${#args}" -gt 0 ] && {
    PARENT=${args[0]}
}

[ "$FEDORA" = "" ] && FEDORA=http://$FEDORAHOST/rest
[ "$BASE" = "" ] && BASE=$FEDORA$PARENT

ingest
