import argparse
import subprocess
import docker_build
import docker_push
import docker_deploy
import docker_cleanup
import common_vars
import re
import traceback
import json


def get_services(vcs_type, service_list_file):
    # Get the root directory of this repository
    get_vcs_root = "";
    if (vcs_type == "hg"):
        get_vcs_root = ["hg", "root"]
    elif (vcs_type == "git"):
        get_vcs_root = ["git", "rev-parse", "--show-toplevel"]

    pipe = subprocess.Popen(
        get_vcs_root,
        stdout=subprocess.PIPE
    )

    repo_root = pipe.stdout.read().strip()
    # Find all Dockerfiles in this repository. For all Dockerfile directories, check if config.json file exists

    try:
        service_list = json.load(open(service_list_file))
    except Exception as e:
        print("Could not find ".format(service_list_file))
        exit()

    for service in service_list:
        service["path"] = repo_root + service["path"]

    # Return all directories of services that have a Dockerfile
    return service_list


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


def get_single_service_path(service_name, service_list):
    for service in service_list:
        if service["name"] == service_name:
            return service

    print("Error: service from branch name not found!")
    exit()


def execute_action_to_service(service_path, action, service_name, default_tag):
    if action == "build":
        print("Building: {0}".format(service_path))
        docker_build.main(service_path, service_name)
    elif action == "publish":
        print("Publishing: {0}".format(service_path))
        docker_push.main(service_path, service_name)
    elif action == "deploy":
        docker_deploy.main(service_path, service_name)
    elif action == "cleanup":
        docker_cleanup.main(service_path, service_name)
    else:
        print("Action not recognized. Please type 'build', 'publish', 'deploy', or cleanup")


def get_services_in_branch_name(service_list, vcs_type):
    filtered_paths = []
    branch_text = get_branch_text(vcs_type).lower()
    for service in service_list:
        service_name = service["name"]
        if service_name in branch_text:
            filtered_paths.append(service_list)
    if not filtered_paths:
        print("Branch name had no services name. Building all.")
        return service_list
    else:
        print("Branch name had service(s) names. Building those.")
        return filtered_paths


def get_branch_text(vcs_type):
    if vcs_type == "git":
        pipe = subprocess.Popen(["git", "rev-parse", "--abrev-ref", "HEAD"], stdout=subprocess.PIPE)
        branch_text = pipe.stdout.read()
    else:
        pipe = subprocess.Popen(["hg", "branch"], stdout=subprocess.PIPE)
        branch_text = pipe.stdout.read()
    return branch_text


def filter_for_name(service_dict):
    return_list = list()
    for service in service_dict:
        return_list.append(service["name"])
    return return_list


def main():
    SERVICE_LIST_FILE = "service_list.json"
    parameters = get_parameters()
    action = parameters["action"]
    vcs_type = common_vars.get_vcs_type()
    branch = common_vars.get_branch(vcs_type)

    if "default_tag" not in parameters.keys():
        default_tag = "default"
    else:
        default_tag = parameters["default_tag"]
    if "release" in branch:
        print("Release branch detected!")
        service_found, version = get_service_and_version_from_branch(branch)
        print("Will only do '{}' to service: '{}' with version: '{}'".format(action, service_found, version))
        services = get_services(vcs_type, SERVICE_LIST_FILE)
        service = get_single_service_path(service_found, services)
        execute_action_to_service(service["path"], action, service["name"], default_tag)

    else:
        services = get_services(vcs_type, SERVICE_LIST_FILE)
        filtered_paths = get_services_in_branch_name(services, vcs_type)
        filtered_names = filter_for_name(filtered_paths)
        print("The following services have been detected:\n\t{0}".format('\n\t'.join(filtered_names)))
        try:
            for service in filtered_paths:
                execute_action_to_service(service["path"], action, service["name"], default_tag)

        except subprocess.CalledProcessError as e:
            traceback.print_exc()
            print "Subprocess Error:"
            print e.output
            exit()


if __name__ == "__main__":
    main()
