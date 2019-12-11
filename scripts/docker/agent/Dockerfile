#Builder Stage
FROM ubuntu:16.04 as builder

# Download latest version of the code and install dependencies
RUN set -eux; \
    apt-get update; \
    apt-get install -y wget curl git-all mercurial sudo

COPY . /opt/licode

# Clone and build licode
WORKDIR /opt/licode/scripts
RUN set -eux; \
    ./installUbuntuDeps_Agent.sh --enable-gpl --cleanup; \
    ./installErizoAgent_custom.sh -e; \
    ./installErizoAgent_custom.sh -ac

#Final Stage, leave unnecessary buildtime dependencies behind to minimize image size. 
FROM ubuntu:16.04 

LABEL maintainer="MModal"

RUN set -eux; \
    groupadd --gid 990 --system licodeag; \
    useradd --uid 990 --system --gid licodeag licodeag; \
    mkdir -p /opt/licode; \
    chown -fR licodeag:licodeag /opt/licode; \
    apt-get update; \
    apt-get install vim python3-pip python3-venv libglib2.0-0 libboost-regex1.58.0 libboost-thread1.58.0 libboost-system1.58.0 liblog4cxx10v5 libx264. libvpx. -y

COPY --from=builder --chown=licodeag:licodeag /opt/licode /opt/licode

USER licodeag:licodeag
    
WORKDIR /opt/licode/scripts/config_update
RUN ./install.sh
WORKDIR /opt/licode

ENTRYPOINT ["./scripts/initDockerAgent.sh"]
