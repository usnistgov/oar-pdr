#!/bin/bash
# NOTE : Quote it else use array to avoid problems #
FILES="/Users/dsn1/NIST/2022/forensics-data/oar-pdr/proto/forensics-sample-data/*"
#curl -vk -H 'Authorization: Bearer LOCALAUTHKEY' --data "/Users/dsn1/NIST/2022/forensics-data/oar-pdr/proto/forensics-sample-data/24.json" https://localhost:8099/ingest/nerdm

for f in $FILES
do
   echo "Processing $f file..."
  # take action on each file. $f store current file name
  curl -vk -H 'Authorization: Bearer DEV756815' --data @"$f" https://oardev.nist.gov:8099/ingest/nerdm

  #cat "$f"
done