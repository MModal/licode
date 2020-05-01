import argparse
import common_vars
import subprocess
import os

def read_from_file(filename):
    f=open(filename, "r")
    if f.mode == "r":
        return f.read()
    else:
        print("Could not read file. ")

def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Root directory where Dockerfile and vars.py configuration files are located.")
    args = parser.parse_args()
    
    if not (args.path):
       parser.error("Path to root directory of microservice required")
  
    parameters = {'path': args.path}

    return parameters

def main(service_name, artifactory_registry, ecr_registry):
    service_vars = common_vars.get_service_variables(service_name, artifactory_registry, ecr_registry)
    
    artifactory_repo = service_vars["artifactory_repo"]
    ecr_repo = service_vars["ecr_repo"]
    image_id_file = service_vars["image_id_file"]
    image_id = read_from_file(image_id_file)

    #Remove all other imageswith the same id 
    print("Removing all other images for service {}".format(service_name))
    artifactory_cleanup_script = """
        docker images {0} | grep {1} | while read -r line; do
            tag=$(echo ${{line}} | awk '{{print $2}}')
            docker rmi {0}:${{tag}} || true
        done""".format(artifactory_repo, image_id)

    print("The docker cleanup script to run is: {0}".format(artifactory_cleanup_script))
    print("Removing the docker images.")
    
    subprocess.check_output(
    artifactory_cleanup_script,
    stderr=subprocess.STDOUT,
    shell=True
    )

    ecr_cleanup_script = """
        docker images {0} | grep {1} | while read -r line; do
            tag=$(echo ${{line}} | awk '{{print $2}}')
            docker rmi {0}:${{tag}} || true
        done""".format(ecr_repo, image_id)

    print("The docker cleanup script to run is: {0}".format(ecr_cleanup_script))
    print("Removing the docker images.")
    
    subprocess.check_output(
    ecr_cleanup_script,
    stderr=subprocess.STDOUT,
    shell=True
    )

    print("Cleanup succesful for {0}.".format(service_name))

if __name__ == "__main__":
    parameters = get_parameters()
    service_name = parameters["servicename"]
    artifactory_registry = parameters["artifactoryreg"]
    ecr_registry = parameters["ecrreg"]
    main(service_name, artifactory_registry)
