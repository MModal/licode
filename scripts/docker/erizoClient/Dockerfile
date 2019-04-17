FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y curl

COPY . /opt/licode

WORKDIR /opt/licode

ENTRYPOINT ["./scripts/erizoClient/build.sh"]
