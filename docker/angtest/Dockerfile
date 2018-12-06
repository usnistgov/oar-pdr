FROM oar-pdr/pdrangular

# Install Chrome

RUN set -ex; \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" \
        >> /etc/apt/sources.list; \
    wget https://dl-ssl.google.com/linux/linux_signing_key.pub; \
    apt-key add linux_signing_key.pub; \
    apt-get update; \
    apt-get install -y --no-install-recommends google-chrome-stable less; \
    ln -s /usr/bin/google-chrome-stable /usr/bin/chrome

ENTRYPOINT ["docker/angtest/entrypoint.sh"]
