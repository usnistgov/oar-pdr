From oarpdr/pymongo

RUN apt-get update && \
    apt-get install -y curl 

WORKDIR /root

# Download a jq binary and do a checksum check on it
COPY jq.sha256 .
RUN curl -L -o jq-linux64 \
    https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && \
    sha256sum -c jq.sha256

# install jq
RUN chmod a+x jq-linux64 && cp jq-linux64 /usr/local/bin/jq

CMD ["bash"]




