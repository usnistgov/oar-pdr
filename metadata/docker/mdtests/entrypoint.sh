#! /bin/bash
#
if [ "$1" = "testall" ]; then
    metadata/scripts/testall.py
elif [ "$1" != "" ]; then
    echo Unknown command: $1
    echo Available commands:  testall
else
    exec /bin/bash
fi
