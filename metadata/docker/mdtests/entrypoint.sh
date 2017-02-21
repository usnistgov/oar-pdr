#! /bin/bash
#
mongod_ctl=/usr/local/bin/mongod_ctl.sh
[ "$1" = "" ] && exec /bin/bash

while [ "$1" != "" ]; do
    case "$1" in
        testall)
            [ -x $mongo_ctl ] && $mongod_ctl start && sleep 1
            scripts/testall.py
            ;;
        install)
            scripts/install.sh
            ;;
        testshell)
            [ -x $mongo_ctl ] && $mongod_ctl start && sleep 1
            exec /bin/bash
            ;;
        shell)
            exec /bin/bash
            ;;
        *)
            echo Unknown command: $1
            echo Available commands:  testall install shell
            ;;
    esac
    shift
done
