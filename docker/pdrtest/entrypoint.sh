#! /bin/bash
#
[ "$1" = "" ] && exec /bin/bash

function install {
    scripts/install.sh --prefix=/app/oar-pdr || return 1
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

function exitopwith {
    echo $2 > $1.exit
    exit $2
}

case "$1" in
    testall)
        install || {
            echo "testall: Failed to install oar-pdr"
            exitopwith testall 2
        }
        scripts/testall.py && stat=$?
        echo Launching/testing the metadata server via nginx...
        launch_test_mdserv
        
        set -x
        curl http://localhost/midas/3A1EE2F169DD3B8CE0531A570681DB5D1491 \
             > mdserv_out.txt && \
             python -c 'import sys, json; fd = open("mdserv_out.txt"); data = json.load(fd); sys.exit(0 if data["doi"]=="doi:10.18434/T4SW26" else 11)' || \
             stat=$?
        
        curl http://localhost/midas/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial1.json \
             > mdserv_out.txt && \
            python -c 'import sys, json; fd = open("mdserv_out.txt"); data = json.load(fd); sys.exit(0 if data["name"]=="tx1" else 21)' || \
            stat=$?
        set +x

        [ "$stat" != "0" ] && {
            echo "testall: One or more server tests failed (last=$stat)"
            exitopwith testall 3
        }

        echo All tests passed
        ;;
    install)
        install
        python -c 'import nistoar.pdr, jq'
        ;;
    testshell)
        libdir=`ls /dev/oar-pdr/python/build | grep lib.`
        export OAR_PYTHONPATH=/dev/oar-pdr/python/build/$libdir
        export OAR_JQ_LIB=/dev/oar-pdr/oar-metadata/jq
        export OAR_MERGE_ETC=/dev/oar-pdr/oar-metadata/etc/merge
        export PYTHONPATH=$OAR_PYTHONPATH
        exec /bin/bash
        ;;
    shell)
        exec /bin/bash
        ;;
    installshell)
        install
        exec /bin/bash
        ;;
    testmdservshell)
        install && launch_test_mdserv
        exec /bin/bash
        ;;
    *)
        echo Unknown command: $1
        echo Available commands:  testall testshell install shell installshell testmdservshell
        ;;
esac

[ $? -ne 0 ] && exitopwith $1 1
true

    
    
