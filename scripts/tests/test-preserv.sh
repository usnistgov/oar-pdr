#! /bin/bash
#
#  test-preserv.sh -- launch a pubserver service and send it some preservation requests
#
#  This is tests the midas3 conventions for MIDAS preservation.
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "." ] && execdir=$PWD

function help {
    echo ${prog} -- launch a pubserver server and send it to some test requests
    cat <<EOF

Usage: $prog [OPTION ...] [PODFILE ...]

Options:
   --change-dir | -C DIR    change into DIR before launch service.  All path 
                            option arguments are by default relative to this directory.
   --oar-home | -H DIR      assume DIR to be where the OAR system is installed.  
   --config-file | -c FILE  use contents of FILE as the configuration data for the server
   --working-dir | -w DIR   write output files to this directory; if it doesn't exist it 
                            will be created.
   --pid-file | -p FILE     use this file as the server's PID file
   --midas-data-dir | -m DIR  use DIR as the parent directory containing MIDAS review and 
                            upload directories
   --with-mdserver | -M     launch and test an accompanying metadata server
   --pause | -P SECS        sleep SECS seconds between processing each POD
   --quiet | -q             suppress most status messages 
   --verbose | -v           print extra messages about internals
   --help                   print this help message

Arguments:
   PODFILE                  path to a pod file to test against the service

EOF
}

quiet=
verbose=
noclean=
withmdserver=
pausebetween=
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
          noclean=1
          ;;
      --midas-data-dir|-m)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          midasdir=$1
          ;;
      --with-mdserver|-M)
          withmdserver=1
          ;;
      --pause|-P)
          [ $# -lt 2 ] && { echo Missing argument to $1 option; false; }
          shift
          pausebetween=$1
          ;;
      --quiet|-q)
          quiet=1
          ;;
      --verbose|-v)
          verbose=1
          ;;
      --no-clean)
          noclean=1
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

[ -n "$server_config" ] || {
    if [ -f etc/preserv-test-config.yml ]; then
        server_config=etc/preserv-test-config.yml
    else 
        [ -n "$OAR_ETC_DIR" ] || {
            [ -n "$OAR_HOME" ] || {
                echo ${prog}: OAR_HOME nor OAR_ETC_DIR not set 1>&2
                false
            }
            OAR_ETC_DIR=$OAR_HOME/etc
        }
        server_config=$OAR_ETC_DIR/preserv-test-config.yml
    fi
}
[ -f "$server_config" ] || {
    echo ${prog}: server config file does not exist as file: $server_config 1>&2
    false
}

[ -n "$uwsgi_script" ] || {
    if [ -f scripts/pubserver-uwsgi.py ]; then
        uwsgi_script=scripts/pubserver-uwsgi.py
    else
        [ -n "$OAR_HOME" ] || {
            echo ${prog}: OAR_HOME not set 1>&2
            false
        }
        uwsgi_script=$OAR_HOME/bin/pubserver-uwsgi.py
    fi
}
[ -f "$uwsgi_script" ] || {
    echo ${prog}: server uwsgi file does not exist as file: $uwsgi_script 1>&2
    false
}

[ -n "$midasdir" ] || midasdir=$PWD/python/tests/nistoar/pdr/preserv/data/midassip
[ -d "$midasdir" ] || {
    echo ${prog}: midas data directory does not exist "(as a directory)" 1>&2
    false
}
[ -n "$pods" ] || {
    pods=($midasdir/review/7223/pod2.json $midasdir/review/7223/pod3.json )
}

[ -n "$workdir" ] || {
    workdir=`echo $prog | sed -e 's/\.[bash]+//'`
    workdir="_${workdir}-$$"
}
[ -d "$workdir" ] || mkdir $workdir
[ -z "$withmdserver" ] || mkdir $workdir/mdarchive

[ -n "$server_pid_file" ] || server_pid_file=$workdir/pubserver.pid
[ -n "$mdserver_uwsgi" ] || mdserver_uwsgi=python/tests/nistoar/pdr/describe/sim_describe_svc.py
[ -n "$mdserver_archdir" ] || mdserver_archdir=$workdir/mdarchive
[ -n "$mdserver_pid_file" ] || mdserver_pid_file=$workdir/mdserver.pid

function launch_test_server {
    tell starting uwsgi for pubserver...
    [ -n "$quiet" -o -z "$verbose" ] || set -x
    mdsopt=""
    [ -z "$withmdserver" ] || mdsopt="--set-ph oar_testmode_repo_access=http://localhost:9092/"
    export OAR_LOG_DIR=$workdir
    uwsgi --daemonize $workdir/uwsgi.log --plugin python --enable-threads --close-on-exec \
          --http-socket :9090 --wsgi-file $uwsgi_script --pidfile $server_pid_file \
          --set-ph oar_testmode_workdir=$workdir --set-ph oar_testmode_midas_parent=$midasdir \
          --set-ph oar_config_file=$server_config $mdsopt
    set +x
}

function stop_test_server {
    tell stopping uwsgi for pubserver...
    uwsgi --stop $server_pid_file
}

function launch_mdserver {
    tell starting uwsgi for metadata server...
    [ -n "$quiet" -o -z "$verbose" ] || set -x
    uwsgi --daemonize $workdir/mdserver-uwsgi.log --plugin python \
          --http-socket :9092 --wsgi-file $mdserver_uwsgi --pidfile $mdserver_pid_file \
          --set-ph archive_dir=$mdserver_archdir
    set +x
}
    
function stop_mdserver {
    tell stopping uwsgi for metadata server...
    uwsgi --stop $mdserver_pid_file && rm $mdserver_pid_file
}

function launch_servers {
    launch_test_server
    [ -z "$withmdserver" ] || launch_mdserver
}

function stop_servers {
    set +e
    stop_test_server
    [ -f "$mdserver_pid_file" ] && stop_mdserver
    set -e
}

function tell {
    [ -n "$quiet" ] || echo "$@"
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

# if sys.argv[1] == 'identifier':
#     val = re.sub(r'ark:/\d+/','',val)
print(val)
EOF

function property_in_pod {
    python $workdir/get_pod_prop.py "$@"
}

echo Testing preservation through pubserver via curl...

launch_servers
trap stop_servers SIGKILL SIGINT

set +e
totfailures=0
totcount=0
failures=0
count=3

tell Testing that service is configured properly and working
curlcmd=(curl -o /dev/null -s -w '%{http_code}\n' http://localhost:9090/preserve/midas)
respcode=`"${curlcmd[@]}"`
[ "$respcode" == "401" ] || {
    tell '---------------------------------------'
    tell FAILED
    tell "${curlcmd[@]}"
    tell "Lack of auth token does not produce 401 response:" $respcode
    ((failures += 1))
}

curlcmd=(curl -o /dev/null -s -w '%{http_code}\n' -H 'Authorization: Bearer secret' http://localhost:9090/preserve/midas)
respcode=`"${curlcmd[@]}"`
[ "$respcode" == "200" ] || {
    tell '---------------------------------------'
    tell FAILED
    tell "${curlcmd[@]}"
    tell "Health check does not produce 200 response:" $respcode
    ((failures += 1))
}

curlcmd=(curl -o /dev/null -s -w '%{http_code}\n' -H 'Authorization: Bearer secret' -X PUT http://localhost:9090/preserve/midas/goober)
respcode=`"${curlcmd[@]}"`
[ "$respcode" == "404" ] || {
    tell '---------------------------------------'
    tell FAILED
    tell "${curlcmd[@]}"
    tell "Non-existent record does not produce 404 response:" $respcode
    ((failures += 1))
}

(( passed = count - failures ))
tell '###########################################'
tell  service health
tell  $count tests, $failures failures, $passed successes
tell '###########################################'
(( totfailures += failures ))
(( totcount += count ))

# run the tests against the server
declare -A idcount
for pod in "${pods[@]}"; do
    failures=0
    count=0

    # sleep between file processing as requested
    [ $count -eq 0 -o -z "$pausebetween" ] || {
        [ -n "$quiet" ] || echo "Resting for $pausebetween seconds..."
        sleep $pausebetween
    }

    id=`property_in_pod identifier $pod`
    localid=`echo $id | perl -pe 's/^ark:\/\d+\///;'`
    oldtitle=`property_in_pod title $pod`
    [ -n "$id" ] || {
        tell ${prog}: identifier not found in $pod
        exit 1
    }
    tell Processing `basename $pod` "POD with identifier =" $id
    [ -n "${idcount[$id]}" ] || idcount[$id]=0

    curlcmd=(curl -o /dev/null -s -w '%{http_code}\n' -H 'Content-type: application/json' -H 'Authorization: Bearer secret' --data @$pod http://localhost:9090/pod/latest)
    respcode=`"${curlcmd[@]}"`
    ((count += 1))
    if [ "$respcode" != "201" ]; then
        tell '---------------------------------------'
        tell FAILED
        tell "${curlcmd[@]}"
        tell "Unexpected response to post to latest:" $respcode
        ((failures += 1))
        continue
    elif [ -n "$verbose" ]; then
        tell "${curlcmd[@]}"
    fi
    sleep 1

    if [ ${idcount[$id]} -gt 0 ]; then
        curlcmd=(curl -o /dev/null -s -w '%{http_code}\n' -X PATCH -H 'Authorization: Bearer secret' http://localhost:9090/preserve/midas/$id)
        respcode=`"${curlcmd[@]}"`
        if [ "$respcode" != "200" -a "$respcode" != "202" ]; then
            tell '---------------------------------------'
            tell FAILED
            tell "${curlcmd[@]}"
            tell "Unexpected response to PATCH to preserve:" $respcode
            ((failures += 1))
        elif [ -n "$verbose" ]; then
            tell "${curlcmd[@]}"
        fi            
        ((count += 1))
        [ "$respcode" == "200" ] || sleep 1

        [ -f "$workdir/store/$localid.1_${idcount[$id]}_0.mbag0_4-${idcount[$id]}.zip" ] || {
            tell '---------------------------------------'
            tell FAILED
            tell "Failed to find zipped bag resulting from preservation: " \
                 $workdir/store/$localid.1_${idcount[$id]}_0.mbag0_4-${idcount[$id]}.zip
            ((failures += 1))
        }
        ((count += 1))
        ((idcount[$id] += 1))
    else
        curlcmd=(curl -o /dev/null -s -w '%{http_code}\n' -X PUT -H 'Authorization: Bearer secret' http://localhost:9090/preserve/midas/$id)
        respcode=`"${curlcmd[@]}"`
        if [ "$respcode" != "201" -a "$respcode" != "202" ]; then
            tell '---------------------------------------'
            tell FAILED
            tell "${curlcmd[@]}"
            tell "Unexpected response to PUT to preserve:" $respcode
            ((failures += 1))
        elif [ -n "$verbose" ]; then
            tell "${curlcmd[@]}"
        fi
        ((count += 1))
        [ "$respcode" == "201" ] || sleep 2

        [ -f "$workdir/store/$localid.1_0_0.mbag0_4-0.zip" ] || {
            tell '---------------------------------------'
            tell FAILED
            tell "Failed to find zipped bag resulting from preservation: " \
                 $workdir/store/$localid.1_0_0.mbag0_4-0.zip
            ((failures += 1))
        }
        ((count += 1))
        ((idcount[$id] += 1))
    fi
    

    (( passed = count - failures ))
    tell '###########################################'
    tell  ${pod}:
    tell  $count tests, $failures failures, $passed successes
    tell '###########################################'
    (( totfailures += failures ))
    (( totcount += count ))
done





trap - ERR
stop_servers

(( passed = totcount - totfailures ))
echo '###########################################'
echo  All files:
echo  $totcount tests, $totfailures failures, $passed successes
echo '###########################################'

if [ -z "$noclean" ]; then
    [ -z "$verbose" ] || tell Cleaning up workdir \(`basename $workdir`\)
    rm -rf $workdir
else
    echo Will not clean-up workdir: $workdir
fi

exit $totfailures
