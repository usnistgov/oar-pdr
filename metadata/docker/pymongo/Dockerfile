FROM mongo:3.2.9
# VOLUME /data
MAINTAINER Ray Plante <raymond.plante@nist.gov>
COPY mongod.conf /etc/mongod.conf
COPY mongod_ctl.sh /usr/local/bin

RUN apt-get update && apt-get install -y python python-pip python-dev
RUN pip install pymongo

