#! /bin/bash
#
# Authenticate to Docker Hub.
#
# Authenticating prevents failures due to pull request rate limits.  Authenticating should enabled via
# Docker Hub access tokens
#
set -e
[ -z "$OAR_DOCKERHUB_CRED" ] || {
    DH_USER=`echo $OAR_DOCKERHUB_CRED | sed -e 's/:.*$//'`
    DH_TOKEN=`echo $OAR_DOCKERHUB_CRED | sed -e 's/^[^:]*://'`
    echo '+' docker login --username '$DH_USER' --password '$DH_TOKEN'
    docker login --username $DH_USER --password $DH_TOKEN || {
        echo "dhsetup: docker login failed"
        false
    }
}
