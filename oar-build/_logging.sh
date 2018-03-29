#! /bin/bash
#
# Defines logging functions
#
set -e
true ${prog:=_logging.sh}

true ${LOGAPPEND:=}                 # can be set by caller

function log_intro {
    if [ -n "$LOGPATH" ]; then
        [ -e "$LOGPATH" ] && {
            if [ -n "$LOGAPPEND" ]; then
                echo >> $LOGPATH
                echo '+++++++++++++++++++++++++++++++++++++++++++++' >> $LOGPATH
            else
                echo -n > $LOGPATH
            fi
        }
        echo Exec: $prog $CL4LOG >> $LOGPATH
        echo "  " started at `date` >> $LOGPATH
    elif [ -n "$QUIET" ]; then
        echo "${prog}: Warning: log will not be written."
    fi
}

function logit {
    if [ -z "$LOGPATH" ]; then
        cat
    elif [ -n "$QUIET" ]; then
        cat >> $LOGPATH
    else
        tee -a $LOGPATH
    fi
}

