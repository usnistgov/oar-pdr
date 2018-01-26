FROM oarmeta/ejsonschema

RUN apt-get update && apt-get install -y python-yaml nginx curl less \
                                         uwsgi uwsgi-plugin-python zip p7zip-full
RUN pip install Detach

COPY entrypoint.sh /root/entrypoint.sh
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /dev/oar-pdr
WORKDIR /dev/oar-pdr

ENV PYTHONPATH /dev/oar-pdr/python/build/

ENTRYPOINT ["/root/entrypoint.sh"]
