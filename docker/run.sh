#! /bin/bash
#
# run.sh -- build and optionally test the software in this repo via docker
#
# type "run.sh -h" to see detailed help
#
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
codedir=`(cd $execdir/.. > /dev/null 2>&1; pwd)`

function usage {
    cat <<EOF

$prog - build and optionally test the software in this repo via docker

SYNOPSIS
  $prog [-d|--docker-build] [--dist-dir DIR] [CMD ...] [python|angular] 
        

ARGS
  python    apply remaining commands to just the python components
  angular   apply remaining commands to just the angular components

  build     build the software
  test      build the software and run the unit tests
  install   just install the prerequisites (use with shell)
  shell     start a shell in the docker container used to build and test

OPTIONS
  -d        build the required docker containers first
EOF
}

function wordin {
    word=$1
    shift

    echo "$@" | grep -qsw "$word"
}
function docker_images_built {
    for image in "$@"; do
        (docker images | grep -qs $image) || {
            return 1
        }
    done
    return 0
}

set -e

distvol=
distdir=
dodockbuild=
cmds=
comptypes=
args=()
while [ "$1" != "" ]; do
    case "$1" in
        -d|--docker-build)
            dodockbuild=1
            ;;
        --dist-dir)
            shift
            distdir="$1"
            mkdir -p $distdir
            distdir=`(cd $distdir > /dev/null 2>&1; pwd)`
            distvol="-v ${distdir}:/app/dist"
            args=(${args[@]} "--dist-dir=/app/dist")
            ;;
        --dist-dir=*)
            distdir=`echo $1 | sed -e 's/[^=]*=//'`
            mkdir -p $distdir
            distdir=`(cd $distdir > /dev/null 2>&1; pwd)`
            distvol="-v ${distdir}:/app/dist"
            args=(${args[@]} "--dist-dir=/app/dist")
            ;;
        -h|--help)
            usage
            exit
            ;;
        -*)
            args=(${args[@]} $1)
            ;;
        python|angular)
            comptypes="$comptypes $1"
            ;;
        build|install|test|shell)
            cmds="$cmds $1"
            ;;
        *)
            if [ -z "$cmds" ]; then
                echo "${prog}: unsupported command:" $1
                false
            else
                args=(${args[@]} $1)
            fi
            ;;
    esac
    shift
done

comptypes=`echo $comptypes`
cmds=`echo $cmds`
[ -n "$comptypes" ] || comptypes="python angular"
[ -n "$cmds" ] || cmds="build"

testopts="--cap-add SYS_ADMIN"
volopt="-v ${codedir}:/dev/oar-pdr"

# check to see if we need to build the docker images; this can't detect
# changes requiring re-builds.
# 
if [ -z "$dodockbuild" ]; then
    if wordin python $comptypes; then
        docker_images_built oar-pdr/pdrtest || dodockbuild=1
    fi
fi
if [ -z "$dodockbuild" ]; then
    if wordin angular $comptypes; then
        if wordin build $cmds; then
            docker_images_built oar-pdr/pdrangular || dodockbuild=1
        fi
        if wordin test $cmds; then
            docker_images_built oar-pdr/angtest || dodockbuild=1
        fi
        if wordin shell $cmds; then
            docker_images_built oar-pdr/angtest || dodockbuild=1
        fi
    fi
fi
        
[ -z "$dodockbuild" ] || {
    echo '#' Building missing docker containers...
    $execdir/dockbuild.sh
}

# handle angular building and/or testing.  If shell was requested with
# angular, open the shell in the angular test contatiner (angtest).
# 
if wordin angular $comptypes; then
    docmds=`echo $cmds | sed -re 's/shell//' -e 's/install//' -e 's/^ +$//'`
    if { wordin shell $cmds && [ "$comptypes" == "angular" ]; }; then
        docmds="$docmds shell"
    fi

    if [ "$docmds" == "build" ]; then
        # build only
        echo '+' docker run --rm $volopt $distvol oar-pdr/pdrangular build \
                       "${args[@]}"
        docker run --rm $volopt $distvol oar-pdr/pdrangular build "${args[@]}"
    elif [ -n "$docmds" ]; then
        echo '+' docker run --rm $volopt $distvol oar-pdr/angtest $docmds \
                       "${args[@]}"
        if wordin shell $docmds; then
            exec docker run -ti --rm $volopt $distvol oar-pdr/angtest $docmds\
                        $args
        else
            docker run --rm $volopt $distvol oar-pdr/angtest $docmds \
                   $args
        fi
    fi
fi

# Now handle python build and/or test
# 
if wordin python $comptypes; then
    
    if wordin build $cmds; then
        # build = makedist
        echo '+' docker run --rm $volopt $distvol oar-pdr/pdrtest makedist $args
        docker run $ti --rm $volopt $distvol oar-pdr/pdrtest makedist $args
    fi

    if wordin test $cmds; then
        # test = testall
        echo '+' docker run --rm $volopt $distvol oar-pdr/pdrtest testall $args
        docker run $ti --rm $volopt $distvol oar-pdr/pdrtest testall $args
    fi

    if wordin shell $cmds; then
        cmd="testshell"
        if wordin install $cmds; then
            cmd="installshell"
        fi
        echo '+' docker run -ti --rm $volopt $distvol oar-pdr/pdrtest $cmd $args
        exec docker run -ti --rm $volopt $distvol oar-pdr/pdrtest $cmd $args
    fi
fi

