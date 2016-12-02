FROM oarpdr/jq:latest

RUN apt-get update && apt-get install -y python python-pip python-dev unzip
RUN pip install json-spec jsonschema requests

WORKDIR /root
RUN curl -L -o ejsonschema.zip \
    https://github.com/usnistgov/ejsonschema/archive/master.zip && \
    unzip ejsonschema.zip && \
    cd ejsonschema-master && \
    python setup.py install

CMD ["bash"]

