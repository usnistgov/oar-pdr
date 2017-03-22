#! /bin/bash
#
[ "$1" = "" ] && exec /bin/bash

while [ "$1" != "" ]; do
    case "$1" in
        testall)
            libdir=`ls /dev/oar-pdr/python/build | grep lib-`
            export PYTHONPATH=/dev/lib/python/build/$libdir
            export OAR_JQ_LIB=/dev/oar-pdr/oar-metadata/jq
            export OAR_MERGE_ETC=/dev/oar-pdr/oar-metadata/etc/merge
            scripts/testall.py
            echo $? > testall.exit
            ;;
        install)
            scripts/install.sh --prefix=/app/oar-pdr
            export OAR_HOME=/app/oar-pdr
            export PYTHONPATH=$OAR_HOME/lib/python
            ;;
        testshell)
            libdir=`ls /dev/oar-pdr/python/build | grep lib-`
            export PYTHONPATH=/dev/lib/python/build/$libdir
            export OAR_JQ_LIB=/dev/oar-pdr/oar-metadata/jq
            export OAR_MERGE_ETC=/dev/oar-pdr/oar-metadata/etc/merge
            exec /bin/bash
            ;;
        shell)
            libdir=`ls /dev/oar-pdr/python/build | grep lib-`
            export PYTHONPATH=/dev/lib/python/build/$libdir
            exec /bin/bash
            ;;
        *)
            echo Unknown command: $1
            echo Available commands:  testall install shell
            ;;
    esac
    
    shift
done
