FROM oarmeta/ejsonschema

RUN apt-get update && apt-get install -y python-yaml uwsgi

COPY entrypoint.sh /root/entrypoint.sh

RUN mkdir -p /dev/oar-pdr
WORKDIR /dev/oar-pdr

ENV PYTHONPATH /dev/oar-pdr/python/build/

ENTRYPOINT ["/root/entrypoint.sh"]
