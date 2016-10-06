#! /bin/bash
#
#
help() {
    cat <<EOF
Usage: $0 [ OPTIONS ] [ DIR [ NAME ]]

Ingest a test directory of data into a Fedora repository

OPTIONS
  -v, --verbose       print out the curl commands for uploading with Fedora
  -s, --simulate      show but do not execute the curl commands
  -h, --host HOST     connect to Fedora on the given HOST; apppend :PORT to the 
                       name if Fedora is not on the default HTTP port
  -r, --rest-url URL  use URL as the base URL for Fedora's rest interface 
                       (overrides -h)
  -p, --parent PATH   ingest the data into the parent collection, PATH; PATH
                       must begin with a slash (/)
  -u, --parent URL    use URL as the parent collection to ingest into 
                       (overrides -h and -p)
  -h, --help          print this message

EOF
}
#set -x
set -e

FEDORAHOST=localhost:8984
PARENT=/DPR/vol1
DPID=95DP01
DPDIR=95DP01
VERBOSE=
SIMULATE=
DEBUG=

FEDORA=
BASE=

function ingest {
    [ "$1" != "" ] && DPDIR=$1
    [ "$2" != "" ] && DPID=$2

    # create the DP collection
    mycurl -X PUT -H "Content-Type: text/turtle"  \
           --data-binary "@95DP01/__metadata.ttl"  \
           $BASE/$DPID

    # create each fileset...
    #
    FILESETS=( `ls -d $DPDIR/*/__metadata.ttl | sed -e 's#'$DPDIR'/##' -e 's#/.*##'` )
    for fs in ${FILESETS[*]}; do

        # ...collection
        mycurl -X PUT -H "Content-Type: text/turtle"        \
               --data-binary "@$DPDIR/$fs/__metadata.ttl"   \
               $BASE/$DPID/$fs

        # ...each file (that does not begin with "__")
        FILES=( `ls -d $DPDIR/$fs/* | sed -e 's#.*/##' | egrep -v '^__'` )
        for file in ${FILES[*]}; do
            if [ `echo $file|sed -e 's/.*\.//'` = "fits" ]; then
                contenttype="image/fits"
            elif [ `echo $file|sed -e 's/.*\.//'` = "gif" ]; then
                contenttype="image/gif"
            elif [ `echo $file|sed -e 's/.*\.//'` = "ps" ]; then
                contenttype="application/postscript"
            else
                contenttype="text/plain"
            fi

            mycurl -X PUT -H "Content-Type: $contenttype"                    \
                   -H "Content-Disposition: attachment; filename=\"$file\""  \
                   --upload-file $DPDIR/$fs/$file                            \
                   $BASE/$DPID/$fs/$file
        done
    done

}

function mycurl {
    TMP=/tmp/ingestDP.$$
    
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

function debug {
    [ "$1" != "" ] && DPDIR=$1
    [ "$2" != "" ] && DPID=$2

    echo FEDORAHOST=$FEDORAHOST
    echo FEDORA=$FEDORA
    echo PARENT=$PARENT
    echo DPID=$DPID
    echo DPDIR=$DPDIR
    echo BASE=$BASE
    echo VERBOSE=$VERBOSE
    echo SIMULATE=$SIMULATE
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
        -p|--parent)
            PARENT=$1; shift
            ;;
        --parent=*)
            PARENT=`echo $arg | sed -e s/^--host=//`
            ;;
        -u|--parent-url)
            BASE=$1; shift
            ;;
        --parent-url=*)
            BASE=`echo $arg | sed -e s/^--host=//`
            ;;
        -v|--verbose)
            VERBOSE=1
            ;;
        -s|--sim*)
            SIMULATE=1
            VERBOSE=1
            ;;
        -h|--help)
            help
            exit
            ;;
        --debug)
            DEBUG=1
            ;;
        *)
            args=(${args[@]} $arg)
            ;;
    esac
done

[ "$FEDORA" = "" ] && FEDORA=http://$FEDORAHOST/rest
[ "$BASE" = "" ] && BASE=$FEDORA$PARENT


[ "$DEBUG" != "" ] && {
    debug ${args[@]}
    exit
}
              

ingest ${args[@]}
