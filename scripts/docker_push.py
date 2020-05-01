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

def artifactory_login(user, password, registry):
    
    docker_login_command = "docker login -u " + user + " -p " + password + " " + registry

    subprocess.check_output(
    docker_login_command,
    stderr=subprocess.STDOUT,
    shell=True
    )

def aws_login():
    aws_login_command = "$(aws ecr get-login --no-include-email --region us-east-1)"

    subprocess.check_output(
        aws_login_command,
        stderr=subprocess.STDOUT,
        shell=True
    )

def main(service_name, artifactory_registry, ecr_registry):
    service_vars = common_vars.get_service_variables(service_name, artifactory_registry, ecr_registry)
    artifactory_user = os.environ["ARTIFACTORY_USER"].strip()
    artifactory_password = os.environ["ARTIFACTORY_PASSWORD"].strip()
    artifactory_login(artifactory_user, artifactory_password, artifactory_registry)
    
    artifactory_repo = service_vars["artifactory_repo"]
    ecr_repo = service_vars["ecr_repo"]
    image_id_file = service_vars["image_id_file"]
    unique_tag = service_vars["unique_tag"]
    image_id = read_from_file(image_id_file)

    artifactory_push_script = """
        docker images {0} | grep {1} | while read -r line; do
            tag=$(echo ${{line}} | awk '{{print $2}}')
            [[ "{2}" == "${{tag}}" ]] || docker push {0}:${{tag}}
        done""".format(artifactory_repo, image_id, unique_tag)

    print("The docker script for artifactory is: {0}".format(artifactory_push_script))
    print("Pushing the docker images to artifactory.")
    
    subprocess.check_output(
    artifactory_push_script,
    stderr=subprocess.STDOUT,
    shell=True
    )
    print("Publish to artifactory command ran for {0}.".format(service_name))

    aws_login()
    ecr_push_script = """
        docker images {0} | grep {1} | while read -r line; do
            tag=$(echo ${{line}} | awk '{{print $2}}')
            [[ "{2}" == "${{tag}}" ]] || docker push {0}:${{tag}}
        done""".format(ecr_repo, image_id, unique_tag)
    
    print("The docker script for ECR is: {0}".format(ecr_push_script))
    print("Pushing the docker images to ECR.")
    
    subprocess.check_output(
        ecr_push_script,
        stderr=subprocess.STDOUT,
        shell=True
    )
    print("Push to ECR command ran for {0}.".format(service_name))

if __name__ == "__main__":
    parameters = get_parameters()
    service_name = parameters["servicename"]
    artifactory_registry = parameters["artifactoryreg"]
    ecr_registry = parameters["ecrreg"]
    main(service_name, artifactory_registry, ecr_registry)
