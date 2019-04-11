import argparse
import common_vars
import subprocess
import os


def read_from_file(filename):
    f = open(filename, "r")
    if f.mode == "r":
        return f.read()
    else:
        print("Could not read file. ")


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Root directory where Dockerfile and vars.py configuration files are located.")
    args = parser.parse_args()

    if not args.path:
        parser.error("Path to root directory of microservice required")

    parameters = {'path': args.path}

    return parameters


def docker_login(user, password, registry):
    docker_login_command = "docker login -u " + user + " -p " + password + " " + registry

    print subprocess.check_output(
        docker_login_command,
        stderr=subprocess.STDOUT,
        shell=True
    )


def main(service_path, service_name):
    service_vars = common_vars.get_service_variables(service_path, service_name)
    artifactory_user = os.environ["ARTIFACTORY_USER"].strip()
    artifactory_password = os.environ["ARTIFACTORY_PASSWORD"].strip()
    registry = service_vars["registry"]
    docker_login(artifactory_user, artifactory_password, registry)

    repo = service_vars["repo"]
    image_id_file = service_vars["image_id_file"]
    unique_tag = service_vars["unique_tag"]
    image_id = read_from_file(image_id_file)

    docker_push_script = """
        docker images {0} | grep {1} | while read -r line; do
            tag=$(echo ${{line}} | awk '{{print $2}}')
            [[ "{2}" == "${{tag}}" ]] || docker push {0}:${{tag}}
        done""".format(repo, image_id, unique_tag)

    print("The docker script to run is: {0}".format(docker_push_script))
    print("Pushing the docker images.")

    print subprocess.check_output(
        docker_push_script,
        stderr=subprocess.STDOUT,
        shell=True
    )
    print("Publish successful for {0}.".format(service_name))


if __name__ == "__main__":
    parameters = get_parameters()
    service_path_main = parameters["path"]
    main(service_path_main)
