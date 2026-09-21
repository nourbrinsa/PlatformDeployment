FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y openssh-server sudo \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd

RUN useradd -m -s /bin/bash student

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
