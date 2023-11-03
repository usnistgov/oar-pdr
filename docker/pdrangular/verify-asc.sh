#! /bin/bash
#
# verify-asc.sh target target.asc keyid
#
keyservers="hkps://keys.openpgp.org hkps://keyserver.ubuntu.com hkp://keyserver.ubuntu.com hkps://keys.gnupg.net"
# set -x

export GNUPGHOME="$(mktemp -d)"
echo "disable-ipv6" >> "$GNUPGHOME/dirmngr.conf"

for keysrvr in $keyservers; do
    echo '++' gpg --batch --keyserver $keysrvr --recv-keys $3
    gpg --batch --keyserver $keysrvr --recv-keys $3 && break
done
[ $? == 0 ] || {
    echo Failed to retrieve key for id=$3
    [ -e "$GNUPGHOME" ] && rm -r "$GNUPGHOME"
    exit 1
}

echo '++' gpg --batch --verify $2 $1
gpg --batch --verify $2 $1 || {
    echo "$2": does not verify against $1
    [ -e "$GNUPGHOME" ] && rm -r "$GNUPGHOME"
    exit 2
}

sleep 1
[ -e "$GNUPGHOME" ] && { rm -r "$GNUPGHOME" || true; }
