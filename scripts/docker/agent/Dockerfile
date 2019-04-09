#Builder Stage
FROM ubuntu:16.04 as builder

#WORKDIR /opt

# Download latest version of the code and install dependencies
RUN apt-get update
RUN apt-get install -y wget curl git-all mercurial sudo

COPY . /opt/licode
#WORKDIR /opt/licode

# Clone and build licode
WORKDIR /opt/licode/scripts
RUN ./installUbuntuDeps_Agent.sh --enable-gpl --cleanup
RUN ./installErizoAgent_custom.sh -e
RUN ./installErizoAgent_custom.sh -ac

#Final Stage, leave unnecessary buildtime dependencies behind to minimize image size. 
FROM ubuntu:16.04 

LABEL maintainer="MModal"

COPY --from=builder --chown=nobody:nogroup /opt/licode /opt/licode

RUN apt-get update
RUN apt-get install vim python3-pip python3-venv rabbitmq-server libx264. libvpx. -y

WORKDIR /opt/licode/scripts/config_update
RUN ./install.sh
WORKDIR /opt/licode/scripts

USER nobody

ENTRYPOINT ["./initDockerAgent.sh"]
