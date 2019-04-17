import argparse
import os
import sys
import subprocess
import common_vars

def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("service_path", help="Root directory where Dockerfile and vars.py configuration files are located.")
    args = parser.parse_args()
    
    if not (args.service_path):
       parser.error("Path to root directory of microservice required")
  
    parameters = {'service_path': args.service_path}

    return parameters

def main(service_name, default_tag="default"):
    service_vars = common_vars.get_service_variables(service_name, default_tag)
    repo = service_vars["repo"]
    version = service_vars["version"]
    container = service_vars["container"]
    
    docker_run_script = """docker run --rm \
    --log-opt tag=\"{0}/{{{{.ID}}}}\" \
    --name={0} \
    {1}:{2}""".format(container, repo, version).strip()

    #Execute the script to build the image
    print("Running the docker container of {0} with script: \n{1}".format(service_name, docker_run_script))
    proc = subprocess.Popen(docker_run_script,
        shell=True, stdout=sys.stdout, stderr=sys.stderr)
    proc.wait()
    print("Finished Running the docker container.")


if  __name__ == "__main__":
    parameters = get_parameters()
    main(parameters["servicename"])
