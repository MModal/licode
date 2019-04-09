import argparse
import os
import subprocess
import common_vars 
import docker_build
import docker_push
import docker_deploy
import docker_cleanup
import sys

#def get_services_paths(vcs_type):
#    
#    #Get the root directory of this repository
#    get_vcs_root = ""; 
#    if(vcs_type == "hg"):
#        get_vcs_root = ["hg","root"]
#    elif(vcs_type == "git"):
#        get_vcs_root = ["git","rev-parse","--show-toplevel"]
#   
#    pipe = subprocess.Popen(
#    get_vcs_root,
#    stdout = subprocess.PIPE
#    )
#
#    repo_root = pipe.stdout.read().strip()
#    #Find all Dockerfiles in this repository. For all Dockerfile directories, check if config.json file exists
#
#    services_search_script = """
#        find {0} -name Dockerfile | while read -r line ; do
#            echo $(dirname ${{line}}) | while read -r directory ; do
#                find ${{directory}} -name {1} | while read -r service ; do
#                    echo $(dirname ${{service}})
#                done
#            done
#        done
#    """.format(repo_root, "config.json")
#
#    pipe = subprocess.Popen(
#    services_search_script,
#    shell = True,
#    stdout = subprocess.PIPE
#    )
#   
#    service_name_text = pipe.stdout.read().strip()
#    if not service_name_text:
#        sys.stderr.write("ERROR, no services were detected\n")
#        exit()
#
#    service_names_arr = service_name_text.split("\n")
#     #Return all directories of services that have a Dockerfile and a config.json file.
#    return service_names_arr

def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="The action to perform after all the microservices have been detected (Build, publish, or deploy). ")
    parser.add_argument("--dockerfile", help="Path of the docker file")
    parser.add_argument("--servicename", help="Name of the service")
    parser.add_argument("--workingdir", help="Path of the working directory")
    parser.add_argument("--default_tag", help="The default tag for services built on default is required.")
    
    args = parser.parse_args()
    if not (args.action):
       parser.error("Action to perform after microservices have been detected is required (Build, publish, or deploy) ")
    if not (args.servicename):
       parser.error("Service name is required")

    parameters = {'action': args.action, 'servicename': args.servicename}
    if (args.default_tag):
        parameters.update({"default_tag": args.default_tag})
    if (args.dockerfile):
        parameters.update({"dockerfile": args.dockerfile})
    if (args.workingdir):
        parameters.update({"workingdir": args.workingdir})

    return parameters

def main():
    parameters = get_parameters()
    vcs_type = common_vars.get_vcs_type()
    action = parameters["action"]
    service_name = parameters["servicename"]
   
    if "default_tag" not in parameters.keys():
        default_tag = "default"
    else:
        default_tag = parameters["default_tag"]

#    service_paths = get_services_paths(vcs_type)
#    print("The following services have been detected:\n\t{0}".format('\n\t'.join(service_paths)))

    try:
        if action == "build":
            print("Building: {0}".format(service_name))
            docker_build.main(service_name, parameters["dockerfile"], parameters["workingdir"], default_tag)
        elif action == "publish":
            print("Publishing: {0}".format(service_path))
            docker_push.main(service_path)
        elif action == "deploy":
            image_tar_file = common_vars.get_service_variables(service_path)["image_tar_file"]
            print("Deploying: {0}, with tar_file in: {1}".format(service_path, image_tar_file))
            docker_deploy.main(service_path, image_tar_file)
        elif action == "cleanup":
            docker_cleanup.main(service_path)
        else:
            print("Action not recognized. Please type 'build', 'publish', 'deploy', or cleanup")
#        for service_path in service_paths:
#            if action == "build":
#                print("Building: {0}".format(service_path))
#                docker_build.main(service_path, default_tag)
#            elif action == "publish":
#                print("Publishing: {0}".format(service_path))
#                docker_push.main(service_path)
#            elif action == "deploy":
#                image_tar_file = common_vars.get_service_variables(service_path)["image_tar_file"]
#                print("Deploying: {0}, with tar_file in: {1}".format(service_path, image_tar_file))
#                docker_deploy.main(service_path, image_tar_file)
#            elif action == "cleanup":
#                docker_cleanup.main(service_path)
#            else:
#                print("Action not recognized. Please type 'build', 'publish', 'deploy', or cleanup")

    except subprocess.CalledProcessError as e:
        print e.output;
        raise e;

if  __name__ == "__main__":
    main()
