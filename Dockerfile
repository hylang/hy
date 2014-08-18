# Base image
#
# VERSION   0.2
FROM        python:3
MAINTAINER  Paul R. Tagliamonte <paultag@debian.org>

ADD . /opt/hylang/hy
RUN pip3 install -e /opt/hylang/hy

CMD ["hy"]
