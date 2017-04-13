#!/bin/bash
#
#set -e

MONGOD_CMD="mongod --config=/etc/mongod.conf --fork"
MONGOD_PID_FILE="/data/mongod.pid"

function start_mongod {
    echo $MONGOD_CMD $@ 1>&2
    $MONGOD_CMD $@ | grep "forked process:" | sed -e 's/^.*: //'
}
function start {
    if running; then
        echo mongod already running
    else
        pid=`start_mongod`
        echo $pid > $MONGOD_PID_FILE
    fi
}
function running {
    if [ -f "$MONGOD_PID_FILE" ]; then
        ps -p `cat $MONGOD_PID_FILE` > /dev/null 
    else
        false
    fi
}
function stop {
    if running; then
        kill `cat $MONGOD_PID_FILE`
        sleep 1
        running && echo "Warning: Mongod having a slow shutdown." 
    else
        echo "Mongod is not found to be running"
    fi
}
    
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        if running; then
            echo mongod is running
        else
            echo mongod is not running
        fi
        ;;
    *)
        echo Usage: $0 start\|stop\|status
        exit 1
        ;;
esac

exit 0

             
