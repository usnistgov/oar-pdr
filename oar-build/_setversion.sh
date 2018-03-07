#! /bin/bash
#
# Processes command line arguments for setversion.sh and defines functions it
# can use.
#
set -e
true ${prog:=_setversion.sh}

function get_reponame {
    if [ -n "$GIT_COMMIT" ]; then
        remotes=(`git remote show -n`)
        repo=`git remote show -n ${remotes[0]} | grep Fetch | sed -e 's/^.*://'`
        basename $repo .git
    elif [ -n "$PACKAGE_DIR" ]; then
        if [ -f "$PACKAGE_DIR/VERSION" ]; then
            awk '{print $1}' "$PACKAGE_DIR/VERSION"
        else
            basename $PACKAGE_DIR | sed -re '/^oar-[^\-]+-/ s/-[^\-]+$//'
        fi
    else
        echo ${prog}: Not a git repository; unable to determine package name
        false
    fi
}

function get_branchname {
    if [ -n "$GIT_COMMIT" ]; then
        branch=`git rev-parse --abbrev-ref HEAD`
        echo $branch
    elif (basename "$PACKAGE_DIR" | grep -sqP '^oar-[^\-]+-'); then
        basename "$PACKAGE_DIR" | sed -re 's/^.*-//'
    else
        echo "(unknown)"
    fi
}

function get_commit {
    git rev-parse HEAD 2> /dev/null || true
}

function get_tag {
    if [ -n "$GIT_COMMIT" ]; then
        opts=--tags
        #opts=
        errfile=/tmp/git-describe-$$_err.txt
        git describe $opts 2> $errfile || {
            grep -qs 'No names found' $errfile || {
                echo setversion: git describe failed: 1>&2
                cat $errfile 1>&2
                rm $errfile
                false
            }
            rm $errfile
        }
    fi
}

# return a string that represents a version of software.  If the last
# commit has an associated tag, that is returned.  Otherwise, one is
# constructed from a the current branch and commit.  
function determine_version {
    out=`get_tag`
    [ -z "$out" ] && {
        out=`get_branchname`
        commit=`get_commit`
        [ -n "$commit" ] && out="${out}-${commit:0:8}"
    }
    echo $out
}

function write_VERSION {
    if [ -z "$PACKAGE_DIR" ]; then
        echo ${prog}: state error: PACKAGE_DIR not set
        false
    else
        echo $1 $2 > $PACKAGE_DIR/VERSION
    fi
}

function set_pkg_version {
    pkg=$1; shift
    vers=$1; shift
    [ -z "$vers" ] && vers=`determine_version`
    [ -z "$pkg" ] && pkg=`get_reponame`
    write_VERSION $pkg $vers
}

GIT_COMMIT=`get_commit`
[ -n "$PACKAGE_NAME" ] || PACKAGE_NAME=$(get_reponame)

