#Builder Stage
FROM ubuntu:16.04 as builder

# Download latest version of the code and install dependencies
RUN apt-get update
RUN apt-get install -y curl git-all sudo

COPY . /opt/licode

# Clone and build licode
WORKDIR /opt/licode/scripts
RUN ./installUbuntuDeps_Controller.sh
RUN ./installErizoController_custom.sh -c

#Final Stage, leave unnecessary buildtime dependencies behind to minimize image size. 
FROM ubuntu:16.04 

LABEL maintainer="MModal"

COPY --from=builder /opt/licode /opt/licode

RUN apt-get update
RUN apt-get install vim python3-pip python3-venv -y

WORKDIR /opt/licode/scripts/config_update
RUN ./install.sh
WORKDIR /opt/licode

ENTRYPOINT ["./scripts/initDockerController.sh"]
