FROM maven:3.5-jdk-8-alpine

RUN  apk update && apk upgrade && apk add netcat-openbsd zip git less \
                                          gnupg shadow python perl wget

# ENV GOSU_VERSION 1.10
# RUN set -ex; arch=amd64; \
#     wget -O /usr/local/bin/gosu \
#    "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$arch"; \
#     wget -O /usr/local/bin/gosu.asc \
# "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$arch.asc";\
#     export GNUPGHOME="$(mktemp -d)"; \
#     gpg --keyserver ha.pool.sks-keyservers.net \
#          --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
#     gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
#     sleep 1; rm -r /usr/local/bin/gosu.asc "$GNUPGHOME" || true; \
#     chmod +x /usr/local/bin/gosu; \
#     gosu nobody true

# Create the user that build/test operations should run as.  Normally,
# this is set to match identity information of the host user that is
# launching the container.
#
RUN apk --no-cache add ca-certificates
RUN wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub

RUN wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.29-r0/glibc-2.29-r0.apk
RUN wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.29-r0/glibc-bin-2.29-r0.apk

RUN apk add glibc-2.29-r0.apk glibc-bin-2.29-r0.apk

RUN wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.29-r0/glibc-i18n-2.29-r0.apk
RUN apk add glibc-bin-2.29-r0.apk glibc-i18n-2.29-r0.apk
RUN /usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8
RUN sed --in-place -e '/CREATE_MAIL_SPOOL/ s/=yes/=no/' /etc/default/useradd
ARG devuser=developer
ARG devuid=1000
RUN grep -qs :${devuid}: /etc/group || \
    groupadd --gid $devuid $devuser
RUN grep -qs ":${devuid}:[[:digit:]]+:" /etc/passwd || \
    useradd -m --comment "OAR Developer" --shell /bin/bash \
            --gid $devuid --uid $devuid $devuser
RUN mkdir /home/$devuser/.m2

VOLUME /dev/oar-pdr
VOLUME /app/dist
COPY settings.xml /app/mvn-user-settings.xml
COPY settings.xml /home/$devuser/.m2/settings.xml
RUN chown $devuser:$devuser /home/$devuser/.m2/settings.xml && \
    chmod a+r /home/$devuser/.m2/settings.xml
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod a+rx /app/entrypoint.sh

WORKDIR /dev/oar-pdr
USER $devuser
ENTRYPOINT [ "/app/entrypoint.sh" ]


