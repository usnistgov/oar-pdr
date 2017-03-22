FROM oarmeta/ejsonschema

COPY entrypoint.sh /root/entrypoint.sh

RUN mkdir -p /dev/oar-pdr
WORKDIR /dev/oar-pdr

ENV PYTHONPATH /dev/oar-pdr/python/build/

ENTRYPOINT ["/root/entrypoint.sh"]
