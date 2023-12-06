#! /bin/bash
#
# install_ca_certs.sh -- copy the specified CA certificates into this source so that they can be used
#                        to build the software via docker.
#
# usage: install_ca_certs.sh CA_CERT_FILE...
#
#   where CA_CERT_FILE is a file path to a CA certificate to install
#
# This script helps address the problem with docker-based builds when run within a firewall that
# replaces external site certificates with ones signed by a non-standard CA, causing the retrieval
# of software dependencies to fail.  This script is used by oar-docker's localbuild script to receive 
# extra CA certificates that addresses such failures.  Because localdeploy makes no assumptions about 
# how this source code repository builds using docker, this script encapsulates that knowledge on 
# behalf of localbuild.
#
# Note: if this repository does not require/support use of non-standard CA certificates, remove (or
# rename) this script.
#
set -e
prog=`basename $0`
execdir=`dirname $0`
[ "$execdir" = "" -o "$execdir" = "." ] && execdir=$PWD
basedir=`dirname $execdir`

cacertdir="$basedir/docker/cacerts"
[ -d "$cacertdir" ] || exit 0         # I guess we don't need the certs

crts=`echo $@ | sed -e 's/^ *//' -e 's/ *$//'`
[ -n "$crts" ] || {
    print "${prog}: Missing cert file argument"
    false
}

echo '+' cp $crts $cacertdir
cp $crts $cacertdir

