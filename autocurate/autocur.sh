#!/bin/bash
#
# set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD

OARDATA_DIR="/oar/data"
PDR_DIR="$OARDATA_DIR/pdr"
LOG_DIR="$OARDATA_DIR/logs"
STAGE_DIR="$PDR_DIR/stage.midas_review"
MIDAS_SIP_LOGDIR="$LOG_DIR/preserver/MIDAS3-SIP"

function latest_headbag {
    bagcache="$2"
    [ -n "$bagcache" ] || bagcache=$STAGE_DIR
    headbag=`python -m curate.cmds.latest_bag $bagcache $1`
    [ "$?" -eq 0 ] || return 1
    echo $headbag
}

function unzip_latest_headbag {
    bagfile=`latest_headbag $1 $2`
    [ "$?" -eq 0 -a -n "$bagfile" ] || return 1
    unzip -q "$bagfile" 
    bagfile=`basename $bagfile | sed -Ee 's/\.[^\.]*$//'`
    echo $bagfile
}

function preservation_in_progress {
    logdir=$2
    [ -n "$logdir" ] || logdir=$MIDAS_SIP_LOGDIR
    test -f $logdir/$1.log
}

function preservation_queued {
    bagparent=$2
    [ -n "$bagparent" ] || bagparent=$MDBAGS_DIR
    annot="$MDBAGS_DIR/$1/metadata/annot.json"
    [ -f "$annot" ] || return 1
    version=`cat $annot | jq '.version'`
    [ "$version" != "null" ] || return 1
    { echo $version | grep -qs '+'; } || return 1
    return 0
}


