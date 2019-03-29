import argparse
import subprocess
import docker_build
import docker_push
import docker_deploy
import docker_cleanup
import common_vars
import re


def get_services_paths():
    # Get the root directory of this repository
    pipe = subprocess.Popen(
        ["hg", "root"],
        stdout=subprocess.PIPE
    )

    repo_root = pipe.stdout.read().strip()

    # Find all Dockerfiles in this repository. For all Dockerfile directories, check if config.json file exists
    services_search_script = """
        find {0} -maxdepth 2 -name Dockerfile | while read -r line ; do
            echo $(dirname ${{line}}) 
        done
    """.format(repo_root)

    pipe = subprocess.Popen(
        services_search_script,
        shell=True,
        stdout=subprocess.PIPE
    )

    service_name_text = pipe.stdout.read().strip()
    service_names_arr = service_name_text.split("\n")

    # Return all directories of services that have a Dockerfile and a config.json file.
    return service_names_arr


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("action",
                        help="The action to perform after all the microservices have been detected (Build, publish, or deploy). ")
    parser.add_argument("--default_tag", help="The default tag for services built on default is required.")

    args = parser.parse_args()
    if not (args.action):
        parser.error(
            "Action to perform after microservices have been detected is required (Build, publish, or deploy) ")

    parameters = {'action': args.action}
    if (args.default_tag):
        parameters.update({"default_tag": args.default_tag})

    return parameters


def get_service_and_version_from_branch(branch_name):
    service = re.search('(?<=-)\w+(?=-)', branch_name).group()
    version = re.search('(\d+\.\d+\.\d+)', branch_name).group()
    if not service:
        print("Could not find the service name from the branch name!")
        return None, None
    elif not version:
        print("Could not find the version from the branch name!")
        return None, None
    else:
        return service, version


def get_single_service_path(service_name):
    pipe = subprocess.Popen(
        ["hg", "root"],
        stdout=subprocess.PIPE
    )

    root = pipe.stdout.read().strip()
    path = root + "/" + service_name

    return path


def execute_action_to_service(service_path, action, default_tag):
    if action == "build":
        print("Building: {0}".format(service_path))
        docker_build.main(service_path)
    elif action == "publish":
        print("Publishing: {0}".format(service_path))
        docker_push.main(service_path, default_tag)
    elif action == "deploy":
        docker_deploy.main(service_path, default_tag)
    elif action == "cleanup":
        docker_cleanup.main(service_path)
    else:
        print("Action not recognized. Please type 'build', 'publish', 'deploy', or cleanup")


def get_services_in_branch_name(service_paths):
    filtered_paths = [];
    for service_path in service_paths:
        split_path = service_path.split("/")
        service_name = split_path[-1]
        if service_name in get_branch_text().lower():
            filtered_paths.append(service_path)

    if not filtered_paths:
        print("Branch name had no services name. Building all.")
        return service_paths
    else:
        print("Branch name had service(s) names. Building those.")
        return filtered_paths


def get_branch_text():
    pipe = subprocess.Popen(["hg", "branch"], stdout=subprocess.PIPE)
    branch_text = pipe.stdout.read()
    return branch_text


def main():
    parameters = get_parameters()
    action = parameters["action"]
    branch = common_vars.get_hg_branch()

    if "default_tag" not in parameters.keys():
        default_tag = "default"
    else:
        default_tag = parameters["default_tag"]
    if "release" in branch:
        print("Release branch detected!")
        service, version = get_service_and_version_from_branch(branch)
        print("Will only do '{}' to service: '{}' with version: '{}'".format(action, service, version))
        service_path = get_single_service_path(service)
        execute_action_to_service(service_path, action, default_tag)

    else:
        service_paths = get_services_in_branch_name(get_services_paths())
        print("The following services have been detected:\n\t{0}".format('\n\t'.join(service_paths)))
        try:
            for service_path in service_paths:
                execute_action_to_service(service_path, action, default_tag)

        except subprocess.CalledProcessError as e:
            print e.output
            raise e


if __name__ == "__main__":
    main()
