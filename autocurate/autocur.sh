#!/bin/bash
#
# set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD

OARDATA_DIR="/oar/data"
PDR_DIR="$OARDATA_DIR/pdr"
MDBAGS_DIR="$PDR_DIR/mdbags"
LOG_DIR="$OARDATA_DIR/logs"
STAGE_DIR="$PDR_DIR/stage.midas_review"
MIDAS_SIP_LOGDIR="$LOG_DIR/preserver/MIDAS3-SIP"
# DPKEY=
UPLOADS_PARENT=/share/midas_uploads
REVIEW_PARENT=/share/midas_review

[ -n "$PDR_CONFIG" ] || PDR_CONFIG=pdr.conf
[ -n "$LOG" ] || LOG=autocur.log
[ -n "$WORKDIR" ] || WORKDIR="$PWD/autocur.work"

# write a message to standard error
# @param words...  the message to write
# 
function advise {
    [ -z "$prog" ] || echo -n "${prog}: "
    echo "$@" 1>&2
}

# execute a python curate command
# @param cmd      the name of the command to run
# @param args...  the arguments to pass to the command
# 
function expycmd {
    cmd=$1
    shift
    python -m curate.cmds.$cmd "$@"
}

# find the latest head bag for a specified publication and return its path
# @param aipid     the AIP ID for the publication
# @param bagcache  (optional, for testing) a directory where head bags are cached
# 
function latest_headbag {
    bagcache="$2"
    [ -n "$bagcache" ] || bagcache=$STAGE_DIR
    headbag=`expycmd latest_bag $bagcache $1`
    [ "$?" -eq 0 ] || return 1
    echo $headbag
}

# find the latest head bag for a specified publication, unzip it in the current
# directory, and return the bag name (i.e. its root directory).
# @param aipid     the AIP ID for the publication
# @param bagcache  (optional, for testing) a directory where head bags are cached
# 
function unzip_latest_headbag {
    bagfile=`latest_headbag $1 $2`
    [ "$?" -eq 0 -a -n "$bagfile" ] || return 1
    unzip -q "$bagfile" 
    bagfile=`basename $bagfile | sed -Ee 's/\.[^\.]*$//'`
    echo $bagfile
}

# clean out a POD file so that it can be used to initialize a draft metadata bag
# @param PODFILE   the POD file to update
#
function clean_pod_file {
    podf=$1
    [ -n "$podf" ] || return 1
    [ -f "$podf" ] || {
        advise ${podf}: not found as a file
        return 1
    }
    expycmd clean_pod_props $podf
}

# return true if it appears that preservation of a specified publication is
# currently in progress.  This looks for artifacts of the process (rather than
# the process itself).
# @param aipid    the AIP identifier for the publicaiton
# @param logdir   (optional, for testing) the directory for preservation logs
# 
function preservation_in_progress {
    logdir=$2
    [ -n "$logdir" ] || logdir=$MIDAS_SIP_LOGDIR
    test -f $logdir/$1.log
}

# return true if it appears that preservation of a specified publication has
# been queued but not necessarily started.  
# @param aipid    the AIP identifier for the publicaiton
# @param bagsdir  (optional, for testing) the directory containing metadata bags
#                 (for publications currently being edited).
# 
function preservation_queued {
    bagparent=$2
    [ -n "$bagparent" ] || bagparent=$MDBAGS_DIR
    annot="$MDBAGS_DIR/$1/metadata/annot.json"
    [ -f "$annot" ] || return 1
    version=`cat $annot | jq -r '.version'`
    [ "$version" != "null" ] || return 1
    { echo $version | grep -qs '+'; } || return 1
    return 0
}

# ensure that a publication is in a state ready to undergo revision.  It is ready if:
#  1. a metadata bag (indicating a publication under edit) does not exist, or
#  2. the metadata contains no updates since its last publication, and
#  3. preservation is neither currently in progress or queued
# If (3) is true but (2) is false (i.e. edits are present), then the metadata will be 
# moved out of the way (to be returned after we're done with our revisions).  If (3) is
# false, then an error is returned.
# @param aipid      the AIP identifier for the publicaiton
# @param headbag    the open head bag for the last published version of the AIP
# @param bagparent  (optional, for testing) the directory containing cached head bags
# 
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
    diffs=`echo $diffs | sed -e 's/versionHistory//' -e 's/releaseHistory//' -e 's/version//'`
    diffs=`echo $diffs`
    [ -z "$diffs" ] || {
        # temporarily move the metadata bag out of the way
        dest="$bagparent/$id.nerdupated"
        [ \! -d "$dest" ] || {
            advise "${dest}: pending migrated metadata bag file exists already"
            return 1
        }
        advise "${id}: unpreserved updates detected in bag; migrating to holding dir"
        mv $bagparent/$id $dest
        expycmd cache_key_md $dest annot.json $diffs
        # return 0
    }

    return 0
}

# restore a metadata bag that was cached because it appeared to have edits in progress.
# The updates will be merged into the last published version (usually the one that added
# the dataset to the target collection).
# @param id         the AIP ID of the dataset
# @param bagparent  (optional) the directory containing metadata bags
#
function restore_inprog_cached {
    id=$1
    [ -n "$id" ] || return 1
    bagparent=$2
    [ -n "$bagparent" ] || bagparent=$MDBAGS_DIR
    [ -d "$bagparent" ] || return 1

    bagdir=$bagparent/$id
    [ \! -e "$bagdir" ] || {
        advise "${aipid}: Bag directory exists; won't restore on top of it"
        return 1
    }

    cached="$bagparent/$aipid.podupdated"
    [ -d "$cached" ] || cached="$bagparent/$aipid.nerdupdated"
    if [ -d "$cached" ]; then
        init_bag_with_pod "$cached"
        if [ -f "$cached/metadata/__annot.json.update" ]; then
            mdir="$cached/metadata"
            expycmd merge_into $mdir/__annot.json.update $mdir/annot.json || {
                advise "${aipid}: Failed to restore in-progress editing (via annot.json)"
                return 1
            }
            [ -d "$bagdir" ] || {
                advise "${aipdi}: Failed to restore in progress editing"
                return 1
            }
            advise 'o' rm -rf $cached
            # rm -rf $cached
        fi
    else
        advise "FYI: No previous draft bag in progress"
    fi
}

# return the MIDAS record number for a given EDI or AIP identifier
# @param id   the AIP or EDI identifier for the publicaiton
# 
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

# ensure that a MIDAS data directory is in a state ready for our revision.  If it
# appears to contain data files, the directory will be moved out of the way and
# replaced with an empty directory.
# @param id        the AIP or EDI identifier for the publicaiton to be revised
# @param datadir   the parent directory to search for a corresponding data directory.
#                  This is typically the path to either the review or uploads directory.
# 
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
            advise "+" mkdir $src
            mkdir $src
        }
    else
        advise "+" mkdir $src
        mkdir $src
    fi
    [ -d "$src" ] || {
        advise Failed to ensure data dir, $src
        return 1
    }
}

# ensure that a MIDAS data directory that was cached away is restored with any new
# SHA files folded in.
# @param id        the AIP or EDI identifier for the publicaiton to be revised
# @param datadir   the parent directory to search for a corresponding data directory.
#                  This is typically the path to either the review or uploads directory.
# 
function restore_cached_data_dir {
    aipid=$1
    [ -n "$aipid" ] || return 1
    datadir=$2
    [ -n "$datadir" ] || return 1
    [ -d "$datadir" ] || {
        advise ${datadir}: directory not found
        return 2
    }
    
    recno=`midas_record_no $aipid`
    [ "$?" -eq 0 -a -n "$recno" ] || return 1

    recdir=$datadir/$recno
    cached=$recdir.curate
    if [ -d "$cached" ]; then
        if [ -d "$recdir" ]; then
            files=`ls $recdir | grep -v _preserv`
            [ -z "$files" ] || {
                advise Data files found in current datadir: $recdir
                return 1
            }
            files=`ls $recdir/_preserv | grep ${aipid}_.*\.sha256`
            [ -z "$files" ] || {
                for f in $files; do
                    if [ \! -e "$cached/_preserv/$f" ]; then
                        advise '+' mv "$recdir/_preserv/$f" "$cached/_preserv/$f"
                        mv "$recdir/_preserv/$f" "$cached/_preserv/$f" || {
                            advise Trouble moving SHA files to cachedir, $cached
                            return 1
                        }
                    else
                        cmp -s "$recdir/_preserv/$f" "$cached/_preserv/$f" || {
                            advise Two identically-named SHA files with different values: \
                                   $recdir/_preserv/$f\; will not overwrite.
                            return 1
                        }
                    fi
                done
            }

            advise '+' rm -rf $recdir
            rm -rf $recdir || {
                advise Failed to remove $recdir
                return 1
            }
        fi
        advise '+' mv $cached $recdir
        mv $cached $recdir || {
            advise Failed to move cached $cached back into place
            return 1
        }
    fi
}

# start the revision process of a publication by initializing the metadata bag based 
# on the POD record from last published version.  It is assumed that the publication
# is in a state ready to do this.  
# @param bagdir   the open head bag for the last published version of the publication
# 
function init_bag_with_pod {
    bagdir=$1
    [ -n "$bagdir" ] || return 1
    podfile="$bagdir/metadata/pod.json"
    [ -f "$podfile" ] || return 1
    advise '+' curl -vk --data @$podfile  -H "'Content-type: application/json'" -H "'Authorization: Bearer *****'" https://datapub.nist.gov/pdr/pod/latest
    stat=`curl -vk --data @$podfile  -H 'Content-type: application/json' -H "Authorization: Bearer $DPKEY" https://datapub.nist.gov/pdr/pod/latest |& grep HTTP/ | tail -1 | sed -e 's/^.* HTTP\/1\.[0-9] //'`
    [ "$?" -eq 0 ] || {
        advise Failed to init md-bag via /latest "(status: $stat)"
        return 1
    }
    { echo $stat | egrep -qs '200|201'; } || {
        advise Failed to init md-bag via /latest "(status: $stat)"
        return 1
    }
}

# add or upgrade the release history of the dataset
# @param aipid     the AIPID identifier for an open metadata bag that should be repaired
# @param bagparent (optional) the directory to look for the metadata bag in
#
function fix_history {
    aipid=$1
    bagparent=$2
    [ -n "$bagparent" ] || bagparent=$MDBAGS_DIR
    bagdir=$bagparent/$aipid
    [ -d "$bagdir" ] || {
        advise ${aipid}: "can't find metadata bag:" $bagdir
        return 1
    }
    expycmd fix_history $bagdir
}

# merge the new collection metadata into the metadata bag
# @param mdfile   the path to the file containing the updated NERDm metadata to merge
# @param scheme   (optional) the taxonomy scheme label (or URI) to merge; default: "additiveman"
# @param aipid    (optional) the AIP identifier to assume; if not provided, the ID in mdfile
#                 will be assumed
# @param outfile  the output (annotation) file to merge the collection metadata file into; if
#                 not provided, it will be written into the metadata bag's annot.json.
# 
function collmdmerge {
    [ -n "$2" ] || set -- "$1" additiveman
    expycmd merge_coll_md "$@"
}

# increment the version on the metadata bag in preparation for preservation
# @param aipid    the AIP for the dataset with an open metadata bag
# @param descrip  the message to record as the reason for the update (usually something like
#                 "added to Additive Manufacturing collection")
function update_version {
    AIPID=$1
    shift
    desc="$@"
    advise '+' pdr -l $LOG -c $PDR_CONFIG pub setver -am $AIPID -b $MDBAGS_DIR
    pdr -l $LOG -c $PDR_CONFIG pub setver -am $AIPID -b $MDBAGS_DIR || return 1
    advise '+' pdr -l $LOG -c $PDR_CONFIG pub setver -aH "$desc" $AIPID -b $MDBAGS_DIR
    pdr -l $LOG -c $PDR_CONFIG pub setver -aH "$desc" $AIPID -b $MDBAGS_DIR || return 1
}

# cache a NERDm record for perviewing the record over the web
# @param aipid   the AIP identifier for the dataset to cache
#
function servenerd {
    AIPID=$1
    advise '+' pdr -l $LOG -c $PDR_CONFIG pub servenerd $AIPID -b $MDBAGS_DIR
    pdr -l $LOG -c $PDR_CONFIG pub servenerd $AIPID -b $MDBAGS_DIR
}

function init {
    AIPID=$1
    [ -n "$AIPID" ] || return 1

    [ -d "$WORKDIR" ] || mkdir $WORKDIR || {
        advise Unable to create working directory: $WORDIR
        return 1
    }
    cd $WORKDIR

    # unpack the last published headbag
    bagdir=`unzip_latest_headbag $AIPID`
    [ "$?" -eq 0 ] || {
        advise Failed to unpack latest head bag
        return 1
    }

    # clean the POD file from head bag
    clean_pod_file $bagdir/metadata/pod.json || {
        advise Failed to clean POD file, $bagdir/metadata/pod.json
        return 1
    }

    # if necessary, protect any MIDAS updates in progress
    ensure_revision_ready $AIPID $bagdir || {
        advise Unable to protect revisions in progress
        return 1
    }

    # if necessary protect the corresponding uploads and review directories
    ensure_data_dir $AIPID $UPLOADS_PARENT || return $?
    ensure_data_dir $AIPID $REVIEW_PARENT || return $?

    # now establish the draft metadata bag that will accept new collection metadata
    init_bag_with_pod $bagdir
}

# Create a draft revision of a publication with the given collection metadata merged
# into it.
# @param updmdfile  the NERDM metadata file containing the collection metadata to merge
# @param colllabel  (optional) the collection short name (default: additiveman)
# 
function colladd {
    mdfile=$1
    [ -f "$mdfile" ] || {
        advise "${mdfile}: not found as a file"
        return 1
    }
    colllabel=$2
    [ -n "$colllabel" ] || colllabel="additiveman"
    id=`cat $mdfile | jq -r '.ediid'`
    [ -n "$id" ] || id=`cat $mdfile | jq -r '."@id"'`
    aipid=`echo $id | sed -re 's/ark:\/\d+\///'`

    # initialize the draft metadata bag
    init $aipid || {
        advise Failed to initialize draft metadata bag
        return 1
    }

    # merge in the collection metadata
    collmdmerge $mdfile $colllabel $aipid

    # set the new version
    update_version $aipid "added to $colllabel collection" || return 1
    fix_history $aipid || return 1

    # make update previewable
    servenerd $aipid

    echo $aipid is ready for review at https://datapub.nist.gov/od/id/$aipid
}

function preserve {
    aipid=$1
    [ -n "$aipid" ] || return 1

    bagdir=$MDBAGS_DIR/$aipid
    [ -d "$bagdir" ] || {
        advise "${aipid}: draft metadata bag not found"
        return 1
    }

    annotf=$bagdir/metadata/annot.json
    [ -f "$annotf" ] || {
        advise "${aipid}: draft metadata bag not ready: missing annot.json"
        return 1
    }
    ready=`cat $annotf | jq '.isPartOf'`
    [ -n "$ready" -a "$ready" != "null" ] || {
        advise "${aipid}: draft metadata bag not ready: isPartOf not found"
        return 1
    }
    
    podf=$bagdir/metadata/pod.json
    [ -f "$podf" ] || {
        advise "${aipid}: draft metadata bag not ready: missing POD file"
        return 1
    }

    # Now submit for preservation
    advise '+' curl -vk -X PATCH --data @$podf -H "'Authorization: Bearer ******'" https://datapub.nist.gov/preserve/midas/ark:/88434/$aipid
    stat=`curl -vk -X PATCH --data @$podf -H "Authorization: Bearer $DPKEY" https://datapub.nist.gov/preserve/midas/ark:/88434/$aipid |& grep HTTP/ | tail -1 | sed -e 's/^.* HTTP\/1\.[0-9] //'`
    [ "$?" -eq 0 ] || {
        advise Failed to submit $aipid for preservation "(status: $stat)"
        return 1
    }
    { echo $stat | egrep -qs '200|201|202'; } || {
        advise Failed to submit $aipid for preservation "(status: $stat)"
        return 1
    }

    echo ${aipid} submitted for preservation
}

function presstatus {
    aipid=$1
    [ -n "$aipid" ] || return 1
    advise '+' curl -k --data @$podf -H "'Authorization: Bearer ******'" https://datapub.nist.gov/preserve/midas/ark:/88434/$aipid
    curl -k --data @$podf -H "Authorization: Bearer $DPKEY" https://datapub.nist.gov/preserve/midas/ark:/88434/$aipid | jq -r '.message + " " + .updated'
    [ "$?" -eq 0 ] || {
        advise Failed to get status of $aipid preservation
        return 1
    }
}

function cleanup {
    id=$1
    [ -n "$id" ] || return 1
    bagparent=$2
    [ -n "$bagparent" ] || bagparent=$MDBAGS_DIR
    [ -d "$bagparent" ] || return 1

    [ \! -d "$bagparent/$id" ] || {
        advise Unpreserved metadata bag exists for $id
        return 1
    }

    restore_cached_data_dir $id $UPLOADS_PARENT || return $?
    restore_cached_data_dir $id $REVIEW_PARENT || return $?

    restore_inprog_cached $id $bagparent
}

