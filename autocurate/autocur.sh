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
DPKEY="XXXX"

function advise {
    echo "$@" 1>&2
}

function expycmd {
    cmd=$1
    shift
    python -m curate.cmd.$cmd "$@"
}

function latest_headbag {
    bagcache="$2"
    [ -n "$bagcache" ] || bagcache=$STAGE_DIR
    headbag=`expycmd latest_bag $bagcache $1`
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

function ensure_revision_ready {
    id=$1
    [ -n "$id" ] || return 1
    headbag=$2
    [ -n "$headbag" ] || return 1
    bagparent=$3
    [ -n "$bagparent" ] || bagparent=$MDBAGS_DIR

    # is there already a cached metadata bag for the ID
    [ -d "$bagparent/$id" ] || return 0
    advise "$id: metadata bag exists"

    # does it appear that a preservation effort is in progress?
    if preservation_in_progress; then
        advise "${id}: preservation appears to be in progress (MIDAS3-SIP log)"
        return 1
    fi

    # does it appear that preservation has been requested
    # i.e. has the version been finalized
    if preservation_queued; then
        advise "${id}: preservation appears to have been requested (version finalized)"
        return 1
    fi

    # has the POD been updated?
    diffs=`expycmd json_difference $headbag/metadata/pod.json $bagparent/$id/metadata/pod.json | grep -Pv '^_'`
    [ -z "$diffs" ] || {
        # temporarily move the metadata bag out of the way
        dest="$bagparent/$id.podupated"
        [ \! -d "$dest" ] || {
            advise "${dest}: pending migrated metadata bag file exists already"
            return 1
        }
        advise "${id}: unpreserved updates detected in bag; migrating to holding dir"
        mv $bagparent/$id $dest
        return 0
    }

    # has the NERDm metadata been updated?
    diffs=`expycmd json_difference $headbag/metadata/annot.json $bagparent/$id/metadata/annot.json | grep -Pv '^_'`
    [ -z "$diffs" ] || {
        # temporarily move the metadata bag out of the way
        dest="$bagparent/$id.nerdupated"
        [ \! -d "$dest" ] || {
            advise "${dest}: pending migrated metadata bag file exists already"
            return 1
        }
        advise "${id}: unpreserved updates detected in bag; migrating to holding dir"
        mv $bagparent/$id $dest
        expycmd cache_key_md $dest nerdm.json $diffs
        # return 0
    }

    return 0
}

function midas_record_no {
    id=$1
    [ -n "$id" ] || return 1
    len=`echo $id | wc -c`
    [ "$len" -lt 30 ] || {
        out=`echo $id | awk '{ print substr($1, 33) }' | sed -Ee 's/^0+//'`
        [ -n "$out" ] || return 1
        echo $out
        return 0
    }

    { echo $id | grep -Psq '^mds2-'; } || {
        advise "$id: unrecognized edi-id form"
        return 1
    }
    out=`echo $id | sed -Ee 's/^mds2-0*//'`
    [ -n "$out" ] || return 1
    echo $out
}

function ensure_data_dir {
    id=$1
    [ -n "$id" ] || return 1
    datadir=$2
    [ -n "$datadir" ] || return 1
    
    recno=`midas_record_no $id`
    [ -n "$recno" ] || return 1

    src=$datadir/$recno
    if [ -d "$src" ]; then
        files=`ls $src | grep -v _preserv`
        [ -z "$files" ] || {
            dest="$src.curate"
            [ \! -e "$dest" ] || {
                advise "${dest}: already exists"
                return 1
            }
            advise "+" mv $src $dest
            mv $src $dest || {
                stat=$?
                advise Failed to migrate existing $src
                return $stat
            }
        }
    fi
}

function init_bag_with_pod {
    bagdir=$1
    [ -n "$bagdir" ] || return 1
    podfile="$bagdir/metadata/pod.json"
    [ -f "$podfile" ] || return 1
    advise '+' curl -vk --data @$podfile  -H "'Content-type: application/json'" -H "'Authorization: Bearer *****'" https://datapub.nist.gov/pdr/pod/latest
    stat=`curl -vk --data @$podfile  -H 'Content-type: application/json' -H "Authorization: Bearer $DPKEY" https://datapub.nist.gov/pdr/pod/latest |& grep HTTP/ | tail -1 | sed -e 's/^.* HTTP/\d\w+ //'`
    [ "$?" -eq 0 ] || {
        advise Failed to init md-bag via /latest "(status: $stat)"
        return 1
    }
    grep -qs 200 || {
        advise Failed to init md-bag via /latest "(status: $stat)"
        return 1
    }
}
