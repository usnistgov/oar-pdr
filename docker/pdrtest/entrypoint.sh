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
    sudo service nginx stop
    echo starting uwsgi...
    workdir=$PWD/_ppmdserver-test-$$
    [ ! -e "$workdir" ] || rm -r $workdir
    mkdir -p $workdir
    uwsgi --daemonize $workdir/uwsgi.log --plugin python --enable-threads --uwsgi-socket :9090 --wsgi-file scripts/ppmdserver-uwsgi.py --pidfile $OAR_HOME/var/mdserv.pid --set-ph oar_testmode_workdir=$workdir
    echo starting nginx...
    sudo service nginx start
}

function exitopwith { 
    echo $2 > $1.exit
    exit $2
}

function diagnose {
    # spit out some outputs that will help what went wrong with service calls
    set +x
    [ -z "$1" ] || [ ! -f "$1" ] || {
        echo "============="
        echo Output:
        echo "-------------"
        cat $1
    }
    [ -z "$2" ] || [ ! -f "$2" ] || {
        echo "============="
        echo Log:
        tail "$2"
    }
    set -x
}

cmd=$1
case "$1" in
    makedist)
        shift
        scripts/makedist.python "$@"
        ;;
    testall)
        install || {
            echo "testall: Failed to install oar-pdr"
            exitopwith testall 2
        }
        shift
        scripts/testall.python "$@"; stat=$?
        echo Launching/testing the metadata server via nginx...
        launch_test_mdserv
        
        set -x
        curl http://localhost:8080/midas/3A1EE2F169DD3B8CE0531A570681DB5D1491 \
             > mdserv_out.txt && \
             python -c 'import sys, json; fd = open("mdserv_out.txt"); data = json.load(fd); sys.exit(0 if data["doi"]=="doi:10.80443/pdrut-T4SW26" else 11)' || \
             stat=$?
        
        curl http://localhost:8080/midas/3A1EE2F169DD3B8CE0531A570681DB5D1491/trial1.json \
             > mdserv_out.txt && \
            python -c 'import sys, json; fd = open("mdserv_out.txt"); data = json.load(fd); sys.exit(0 if data["name"]=="tx1" else 12)' || \
            stat=$?
        set +x

        [ "$stat" != "0" ] && {
            echo "testall: One or more server tests failed (last=$stat)"
            exitopwith testall 3
        }

        echo All python tests passed
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
        export OAR_SCHEMA_DIR=/dev/oar-pdr/oar-metadata/model
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
    testpreserveshell)
        install && launch_test_preserver
        exec /bin/bash
        ;;
    *)
        echo Unknown command: $1
        echo Available commands:  makedist testall testshell install shell installshell testmdservshell testpreserveshell
        ;;
esac

[ $? -ne 0 ] && exitopwith $cmd 1
true

    
    
