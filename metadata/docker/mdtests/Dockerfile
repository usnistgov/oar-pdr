FROM oarpdr/ejsonschema

COPY entrypoint.sh /root/entrypoint.sh

RUN mkdir -p /dev/oar-pdr
WORKDIR /dev/oar-pdr/metadata

ENTRYPOINT ["/root/entrypoint.sh"]
