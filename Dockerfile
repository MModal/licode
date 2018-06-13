#Builder Stage
FROM ubuntu:16.04 as builder

WORKDIR /opt

# Download latest version of the code and install dependencies
RUN apt-get update
RUN apt-get install -y wget
RUN apt-get install -y curl
RUN apt-get install -y git-all
RUN apt-get install -y mercurial
RUN apt-get install -y sudo

COPY . /opt/licode
WORKDIR /opt/licode

# Clone and build licode
WORKDIR /opt/licode/scripts
RUN ./installUbuntuDepsMModal.sh --enable-gpl --cleanup
RUN ./installErizo.sh -e

#Final Stage, leave unnecessary buildtime dependencies behind to minimize image size. 
FROM ubuntu:16.04 

LABEL maintainer="MModal"

COPY --from=builder --chown=nobody:nogroup /opt/licode /opt/licode
WORKDIR /opt/licode/scripts

RUN apt-get update
RUN apt-get install g++ mongodb rabbitmq-server libssl-dev libboost-thread-dev liblog4cxx10-dev libx264. libvpx. make -y
RUN apt-get install python-software-properties software-properties-common -y
RUN ./installErizo.sh -facs
RUN ../nuve/installNuve.sh

USER nobody

ENTRYPOINT ["./initDockerLicode.sh"]
