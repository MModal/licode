#Builder Stage
FROM ubuntu:16.04 as builder

# Download latest version of the code and install dependencies
RUN apt-get update && \
    apt-get install -y curl git-all sudo wget

COPY . /opt/licode

# Clone and build licode
WORKDIR /opt/licode/scripts
RUN ./installUbuntuDeps_Nuve.sh
WORKDIR /opt/licode/nuve
RUN ./installNuve_custom.sh && \
    wget https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem

#Final Stage, leave unnecessary buildtime dependencies behind to minimize image size. 
FROM ubuntu:16.04 

LABEL maintainer="MModal"

RUN set -eux; \
    groupadd --gid 991 --system nuve; \
    useradd --uid 991 --system --gid nuve nuve; \
    mkdir -p /opt/licode; \
    chown -fR nuve:nuve /opt/licode; \
    apt-get update; \
    apt-get install python3 python3-pip python3-venv -y

COPY --from=builder --chown=nuve:nuve /opt/licode /opt/licode

USER nuve:nuve

WORKDIR /opt/licode/scripts/config_update
RUN ./install.sh
WORKDIR /opt/licode

EXPOSE 3000

ENTRYPOINT ["./scripts/initDockerNuve.sh"]
