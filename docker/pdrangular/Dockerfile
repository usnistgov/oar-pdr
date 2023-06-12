##########################################
#
# Build container for angular components
#
# The purpose of this Docker container is produce a distribution
# bundle that can be added into the deployment container.  This
# container should build the code in an environment that sufficiently
# matches the target operational environment. 
#
##########################################

# The parent should be an ancestor image of the operational container
# 
FROM debian:buster-slim

RUN sed -e '/buster-updates/ s/^deb/#deb/' /etc/apt/sources.list \
    > /tmp/sources.list && mv /tmp/sources.list /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y --no-install-recommends zip wget ca-certificates git xz-utils \
                                               gnupg python

ARG node_ver=v14.19.0
COPY node-sha256.txt /tmp
RUN cd /tmp && wget https://nodejs.org/dist/$node_ver/node-$node_ver-linux-x64.tar.xz  \
            && sha256sum -c node-sha256.txt
RUN cd /usr/local && tar xJf /tmp/node-$node_ver-linux-x64.tar.xz \
                  && ln -s node-$node_ver-linux-x64 node          \
                  && cd bin                                     \
                  && ln -s ../node/bin/node node                \
                  && ln -s ../node/bin/npm  npm                 \
                  && ln -s ../node/bin/npx  npx            

ENV GOSU_VERSION 1.14
COPY verify-asc.sh /usr/local/bin
RUN set -ex; \
    arch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
    wget -O /usr/local/bin/gosu \
   "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$arch"; \
    wget -O /usr/local/bin/gosu.asc \
"https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$arch.asc";\
    verify-asc.sh /usr/local/bin/gosu /usr/local/bin/gosu.asc    \
                  B42F6819007F00F88E364FD4036A9C25BF357DD4;      \
    sleep 1; rm -r /usr/local/bin/gosu.asc || true; \
    chmod +x /usr/local/bin/gosu; \
    gosu nobody true

# Create the user that build/test operations should run as.  Normally,
# this is set to match identity information of the host user that is
# launching the container.
#
RUN sed --in-place -e '/CREATE_MAIL_SPOOL/ s/=yes/=no/' /etc/default/useradd
ARG devuser=developer
ARG devuid=1000
RUN grep -qs :$devuid: /etc/group || \
    groupadd --gid $devuid $devuser
RUN grep -Pqs ":$devuid:\d+:" /etc/passwd || \
    useradd -m --comment "OAR Developer" --shell /bin/bash \
            --gid $devuid --uid $devuid $devuser

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod a+rx /usr/local/bin/entrypoint.sh

VOLUME /dev/oar-pdr
VOLUME /app/dist

RUN mkdir -p /dev/oar-pdr /app && chmod a+rwx /app
WORKDIR /dev/oar-pdr

ENV CODEDIR /dev/oar-pdr
ENV DOCKERDIR /dev/oar-pdr/docker
ENV DEVUID $devuid

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
