# Base image
#
# VERSION   0.1
FROM        debian:unstable
MAINTAINER  Paul R. Tagliamonte <paultag@debian.org>

RUN apt-get update && apt-get install -y python3.4 python3-pip
ADD . /opt/hylang/hy
RUN python3.4 /usr/bin/pip3 install -e /opt/hylang/hy

CMD ["hy"]
