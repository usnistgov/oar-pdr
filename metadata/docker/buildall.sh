#! /bin/bash
#
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
set -ex

docker build -t oarpdr/jq $execdir/jq
docker build -t oarpdr/ejsonschema $execdir/ejsonschema
docker build -t oarpdr/mdtests $execdir/mdtests
