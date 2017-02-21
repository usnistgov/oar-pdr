FROM oarpdr/ejsonschema

COPY entrypoint.sh /root/entrypoint.sh

RUN mkdir -p /dev/oar-pdr
WORKDIR /dev/oar-pdr/metadata

ENV MONGO_TESTDB_URL mongodb://localhost/testdb
ENV PYTHONPATH /dev/oar-pdr/metadata/python

ENTRYPOINT ["/root/entrypoint.sh"]
