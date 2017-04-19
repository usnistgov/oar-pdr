#! /bin/bash
#
[ "$1" = "" ] && exec /bin/bash

function install {
    scripts/install.sh --prefix=/app/oar-pdr
    export OAR_HOME=/app/oar-pdr
    export PYTHONPATH=$OAR_HOME/lib/python
    export OAR_LOG_DIR=$OAR_HOME/var/logs
}

function launch_test_mdserv {
    echo starting uwsgi...
    uwsgi --daemonize $OAR_HOME/var/logs/uwsgi.log --plugin python --uwsgi-socket :9090 --wsgi-file scripts/ppmdserver-uwsgi-test.py
    echo starting nginx...
    service nginx start
}

while [ "$1" != "" ]; do
    case "$1" in
        testall)
            libdir=`ls /dev/oar-pdr/python/build | grep lib-`
            export PYTHONPATH=/dev/lib/python/build/$libdir
            export OAR_JQ_LIB=/dev/oar-pdr/oar-metadata/jq
            export OAR_MERGE_ETC=/dev/oar-pdr/oar-metadata/etc/merge
            scripts/testall.py || {
                echo $? > testall.exit
                exit
            }
            install && launch_test_mdserv
            echo Launching/testing the metadata server via nginx...
            curl http://localhost/midas/3A1EE2F169DD3B8CE0531A570681DB5D1491 \
                 > mdserv_out.txt || {
                echo 10 > testall.exit
                exit
            }
            python -c 'import sys, json; fd = open("mdserv_out.txt"); data = json.load(fd); sys.exit(0 if data["doi"]=="doi:10.18434/T4SW26" else 20)'
            echo $? > testall.exit
            if cat testall.exit; then
                echo All tests passed
            else
                echo Server test failed
            fi
            ;;
        install)
            install
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
        installshell)
            install
            printenv
            exec /bin/bash
            ;;
        testmdservshell)
            install && launch_test_mdserv
            exec /bin/bash
            ;;
        *)
            echo Unknown command: $1
            echo Available commands:  testall testshell install shell installshell testmdserv
            ;;
    esac
    
    shift
done
