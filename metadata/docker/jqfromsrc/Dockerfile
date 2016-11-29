From ubuntu:15.04

RUN apt-get update && \
    apt-get install -y libonig-dev curl build-essential libtool zip \
                       unzip autoconf git

WORKDIR /root
RUN curl -L -o jq-1.5.zip https://github.com/stedolan/jq/archive/jq-1.5-branch.zip && \
    unzip jq-1.5.zip && \
    cd jq-jq-1.5-branch && \
    autoreconf -i && \
    ./configure --disable-maintainer-mode && \
    make -j8 && \
    make check && \
    make install

CMD ["bash"]




