#Builder Stage
FROM ubuntu:16.04 as builder

#WORKDIR /opt

# Download latest version of the code and install dependencies
RUN apt-get update && \
    apt-get install -y wget curl git-all mercurial sudo

COPY . /opt/licode
#WORKDIR /opt/licode

# Clone and build licode
WORKDIR /opt/licode/scripts
RUN ./installUbuntuDeps_Agent.sh --enable-gpl --cleanup && \
    ./installErizoAgent_custom.sh -e && \
    ./installErizoAgent_custom.sh -ac

#Final Stage, leave unnecessary buildtime dependencies behind to minimize image size. 
FROM ubuntu:16.04 

LABEL maintainer="MModal"

COPY --from=builder /opt/licode /opt/licode

RUN apt-get update && \
    apt-get install vim python3-pip python3-venv rabbitmq-server libglib2.0-0 libboost-regex1.58.0 libboost-thread1.58.0 libboost-system1.58.0 liblog4cxx10v5 libx264. libvpx. -y

WORKDIR /opt/licode/scripts/config_update
RUN ./install.sh
WORKDIR /opt/licode

ENTRYPOINT ["./scripts/initDockerAgent.sh"]
