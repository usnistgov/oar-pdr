#! /bin/bash
#
[ "$1" = "" ] && exec /bin/bash

while [ "$1" != "" ]; do
    case "$1" in
        testall)
            scripts/testall.py
            ;;
        install)
            scripts/install.sh
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
