#! /bin/bash
#
#  test-pubserver.sh -- launch a pubserver service and send it some test requests
#
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "." ] && execdir=$PWD

function help {
    echo ${prog} -- launch a pubserver server and send it to some test requests
    cat <<EOF

Usage: $prog [OPTION ...]

Options:
   --change-dir | -C DIR    change into DIR before launch service.  All path 
                            option arguments are by default relative to this directory.
   --oar-home | -H DIR      assume DIR to be where the OAR system is installed.  
   --config-file | -c FILE  use contents of FILE as the configuration data for the server
   --working-dir | -w DIR   write output files to tihs directory; if it doesn't exist it 
                            will be created.
   --pid-file | -p FILE     use this file as the server's PID file
EOF
}

pods=()
while [ "$1" != "" ]; do
  case "$1" in
      --change-dir|-C)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          echo "${prog}: changing working directory to $1" 1>&2
          cd $1
          ;;
      --oar-home|-H)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          export OAR_HOME=$1
          ;;
      --config-file|-c)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          server_config=$1
          ;;
      --pid-file|-p)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          server_pid_file=$1
          ;;
      --working-dir|-w)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          workdir=$1
          ;;
      --midas-data-dir|-m)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          midasdir=$1
          ;;
      --custserv-url|-U)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          cust_service=$1
          ;;
      --custserv-secret|-T)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          cust_secret=$1
          ;;
      --help|-h)
          help
          exit
          ;;
      --*)
          echo ${prog}: unsupported option: $1 1>&2
          false
          ;;
      *)
          pods=("${pods[@]}" "$1")
          ;;
  esac
  shift
done

[ "$execdir" = "" ] && execdir=$PWD

[ -n "$server_config" ] || {
    if [ -f etc/pubservice-test-config.yml ]; then
        server_config=etc/pubservice-test-config.yml
    else 
        [ -n "$OAR_ETC_DIR" ] || {
            [ -n "$OAR_HOME" ] || {
                echo ${prog}: OAR_HOME nor OAR_ETC_DIR not set 1&>2
                false
            }
            OAR_ETC_DIR=$OAR_HOME/etc
        }
        server_config=$OAR_ETC_DIR/pubservice-test-config.yml
    fi
}
[ -f "$server_config" ] || {
    echo ${prog}: server config file does not exist as file: $server_config 1&>2
    false
}

[ -n "$uwsgi_script" ] || {
    if [ -f scripts/pubserver-uwsgi.py ]; then
        uwsgi_script=scripts/pubserver-uwsgi.py
    else
        [ -n "$OAR_HOME" ] || {
            echo ${prog}: OAR_HOME not set 1&>2
            false
        }
        uwsgi_script=$OAR_HOME/bin/pubserver-uwsgi.py
    fi
}
[ -f "$uwsgi_script" ] || {
    echo ${prog}: server uwsgi file does not exist as file: $uwsgi_script 1&>2
    false
}

[ -n "$midasdir" ] || midasdir=$PWD/python/tests/nistoar/pdr/preserv/data/midassip
[ -d "$midasdir" ] || {
    echo ${prog}: midas data directory does not exist "(as a directory)" 1&>2
    false
}
[ -n "$pods" ] || {
    pods=($midasdir/review/1491/_pod.json $midasdir/upload/1491/_pod.json)
    unit_test="1491"
}

[ -n "$workdir" ] || {
    workdir=`echo $prog | sed -e 's/\.[bash]+//'`
    workdir="_${workdir}-$$"
}
mkdir $workdir

[ -n "$server_pid_file" ] || server_pid_file=$workdir/pubserver.pid
[ -n "$cust_pid_file" ] || cust_pid_file=$workdir/simcustom.pid
[ -n "$cust_uwsgi" ] || cust_uwsgi=python/tests/nistoar/pdr/publish/midas3/sim_cust_srv.py
[ -n "$custserv_secret" ] || custserv_secret=secret
custser_url=

function launch_test_server {
    custcfg="--set-ph oar_custom_serv_url=http://localhost:9091/draft/"
    [ -z "$custserv_url" ] || {
        custcfg="--set-ph oar_custom_serv_url=$custserv_url"
    }
    echo starting uwsgi for pubserver...
    set -x
    uwsgi --daemonize $workdir/uwsgi.log --plugin python --enable-threads \
          --http-socket :9090 --wsgi-file $uwsgi_script --pidfile $server_pid_file \
          --set-ph oar_testmode_workdir=$workdir --set-ph oar_testmode_midas_parent=$midasdir \
          --set-ph oar_config_file=$server_config --set-ph oar_custom_serv_key=$custserv_secret\
           $custcfg
    set +x
}

function stop_test_server {
    echo stopping uwsgi for pubserver...
    uwsgi --stop $server_pid_file
}

function launch_simcust_server {
    echo starting uwsgi for simulated customization server "(with key=$custserv_secret)"...
    set -x
    uwsgi --daemonize $workdir/cust-uwsgi.log --plugin python \
          --http-socket :9091 --wsgi-file $cust_uwsgi --pidfile $cust_pid_file \
          --set-ph auth_key=$custserv_secret
    set +x
}

function stop_simcust_server {
    echo stopping uwsgi for simulated customization server...
    uwsgi --stop $cust_pid_file && rm $cust_pid_file
}

function launch_servers {
    launch_test_server
    [ -n "$custserv_url" ] || launch_simcust_server
}

function stop_servers {
    set +e
    stop_test_server
    [ -f "$cust_pid_file" ] && stop_simcust_server
    set -e
}    

function exitopwith { 
    echo $2 > $1.exit
    exit $2
}

function diagnose {
    # spit out some outputs that will help what went wrong with service calls
    # set +x
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
    # set -x
}

cat > $workdir/get_pod_prop.py <<EOF
from __future__ import print_function
import sys, json, re
if len(sys.argv) < 2:
   print("get_pod_prop: Missing property name and POD file name", file=sys.stderr)
   sys.exit(1)
if len(sys.argv) < 3:
   print("get_pod_prop: Missing POD file name", file=sys.stderr)
   sys.exit(1)

try:
    with open(sys.argv[2]) as fd:
        pod = json.load(fd)
    val = pod[sys.argv[1]]
except (ValueError, TypeError) as ex:
    print("JSON parse error of input file: "+str(ex), file=sys.stderr)
    sys.exit(2)
except KeyError as ex:
    print("Property not found: "+str(ex), file=sys.stderr)
    sys.exit(3)
except Exception as ex:
    print("Unexpected error: "+str(ex), file=sys.stderr)
    sys.exit(4)

if sys.argv[1] == 'identifier':
    val = re.sub(r'ark:/\d+/','',val)
print(val)
EOF

function property_in_pod {
    python $workdir/get_pod_prop.py "$@"
}

launch_servers
trap stop_servers SIGKILL SIGINT

set +e
#set -x
curlcmd=(curl -s -w '%{http_code}\n' -H 'Authorization: Bearer secret' http://localhost:9090/pod/latest/mds2-1000)
respcode=`"${curlcmd[@]}"`
[ "$respcode" == "404" ] || {
    echo '---------------------------------------'
    echo FAILED
    echo "${curlcmd[@]}"
    echo "Non-existent record does not produce 404 response:" $respcode
}

# run the tests against the server
totfailures=0
for pod in "${pods[@]}"; do
    failures=0

    id=`property_in_pod identifier $pod`
    oldtitle=`property_in_pod title $pod`
    [ -n "$id" ] || {
        echo ${prog}: identifier not found in $pod
        exit 1
    }
    echo "Processing POD with identifier =" $id

    curlcmd=(curl -s -w '%{http_code}\n' -H 'Content-type: application/json' -H 'Authorization: Bearer secret' --data @$pod http://localhost:9090/pod/latest)
    respcode=`"${curlcmd[@]}"`
    [ "$respcode" == "201" ] || {
        echo '---------------------------------------'
        echo FAILED
        echo "${curlcmd[@]}"
        echo "Unexpected response to post to latest:" $respcode
        ((failures += 1))
    }

    curlcmd=(curl -s -H 'Authorization: Bearer secret' http://localhost:9090/pod/latest/$id)
    "${curlcmd[@]}" > $workdir/pod.json
    if [ $? -ne 0 ]; then
        echo '---------------------------------------'
        echo FAILED
        echo "${curlcmd[@]}"
        echo `basename $pod`: "Failed to retrieve POD posted to latest"
        ((failures += 1))
    else 
        newid=`property_in_pod identifier $workdir/pod.json`
        [ "$id" == "$newid" ] || {
            echo '---------------------------------------'
            echo FAILED
            echo "${curlcmd[@]}"
            echo `basename $pod`: "Unexpected identifier returned from latest:" $newid
            ((failures += 1))
        }
    fi

    curlcmd=(curl -s -w '%{http_code}\n' -H 'Content-type: application/json' -H 'Authorization: Bearer secret' -X PUT --data @$pod http://localhost:9090/pod/draft/$id)
    respcode=`"${curlcmd[@]}"`
    [ "$respcode" == "201" ] || {
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo "Unexpected response to post to draft:" $respcode
        ((failures += 1))
    }

    curlcmd=(curl -s -H 'Authorization: Bearer secret' http://localhost:9090/pod/draft/$id)
    "${curlcmd[@]}" > $workdir/pod.json
    if [ $? -ne 0 ]; then
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo `basename $pod`: "Failed to retrieve POD posted to draft"
    else
        newid=`property_in_pod identifier $workdir/pod.json`
        [ "$id" == "$newid" ] || {
            echo '---------------------------------------'
            echo FAILED
            echo ${curlcmd[@]}
            echo `basename $pod`: "Unexpected identifier returned from draft:" $newid
            ((failures += 1))
        }
    fi
        
    newtitle=`property_in_pod title $pod`
    [ "$oldtitle" == "$newtitle" ] || {
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo `basename $pod`: "Unexpected title returned from draft:" $newtitle
        ((failures += 1))
    }

    sleep 1
    [ -f "$workdir/mdbags/$id/metadata/nerdm.json" ] || {
        echo '---------------------------------------'
        echo FAILED
        echo `basename $pod`: "No generated NERDm record found at " \
             "$workdir/mdbags/$id/metadata/nerdm.json"
        ((failures += 1))
    }

    curl -H "Authorization: Bearer $custserv_secret" -X PATCH -H 'Content-type: application/json' \
         --data '{ "title": "Star Wars", "_editStatus": "done" }' \
         http://localhost:9091/draft/$id || \
    {
        echo '---------------------------------------'
        echo WARNING: Back door PATCH to draft failed
    }

    curlcmd=(curl -s -H 'Authorization: Bearer secret' http://localhost:9090/pod/draft/$id)
    "${curlcmd[@]}" > $workdir/pod.json
    if [ $? -ne 0 ]; then
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo `basename $pod`: "Failed to retrieve POD posted to draft"
    else
        newtitle=`property_in_pod title $workdir/pod.json`
        [ "$newtitle" == "Star Wars" ] || {
            echo '---------------------------------------'
            echo FAILED
            echo ${curlcmd[@]}
            echo `basename $pod`: "Title from draft failed to get updated:" $newtitle
            ((failures += 1))
        }
    fi
    
    curlcmd=(curl -s -w '%{http_code}\n' -H 'Authorization: Bearer secret' -X DELETE http://localhost:9090/pod/draft/$id)
    respcode=`"${curlcmd[@]}"`
    [ "$respcode" == "200" ] || {
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo "Unexpected response to delete of draft:" $respcode
        ((failures += 1))
    }

    curlcmd=(curl -s -H 'Authorization: Bearer secret' http://localhost:9090/pod/latest/$id)
    "${curlcmd[@]}" > $workdir/pod.json
    if [ $? -ne 0 ]; then
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo `basename $pod`: "Failed to retrieve POD posted to latest"
    else
        newid=`property_in_pod identifier $workdir/pod.json`
        [ "$id" == "$newid" ] || {
            echo '---------------------------------------'
            echo FAILED
            echo ${curlcmd[@]}
            echo `basename $pod`: "Unexpected identifier returned from latest:" $newid
            ((failures += 1))
        }
    fi
    [ "$newtitle" == "Star Wars" ] || {
        echo '---------------------------------------'
        echo FAILED
        echo ${curlcmd[@]}
        echo `basename $pod`: "Failed to commit updated title:" $newtitle
        ((failures += 1))
    }

    (( passed = 10 - failures ))
    echo '###########################################'
    echo  ${pod}:
    echo  10 tests, $failures failures, $passed successes
    echo '###########################################'
    (( totfailures += failures ))
done

trap - ERR
stop_servers

echo workdir=$workdir
tottests=$(( 10 * ${#pods[@]} ))
(( passed = tottests - totfailures ))
echo '###########################################'
echo  All files:
echo  $tottests tests, $totfailures failures, $passed successes
echo '###########################################'

exit $totfailures

