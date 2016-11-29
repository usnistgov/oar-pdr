From ubuntu:15.04

RUN apt-get update && \
    apt-get install -y curl 

WORKDIR /root
COPY jq-sha256sum.txt .
RUN curl -L \
    https://raw.githubusercontent.com/stedolan/jq/master/sig/v1.5/sha256sum.txt |\
    grep jq-linux64 | sha256sum | \
    sed -e 's/\-/jq-sha256sum.txt/'> jq-sum-txt.sum && \
    sha256sum -c jq-sum-txt.sum
RUN curl -L -o jq-linux64 \
    https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && \
    sha256sum -c jq-sha256sum.txt
RUN chmod a+x jq-linux64 && cp jq-linux64 /usr/local/bin/jq

CMD ["bash"]




