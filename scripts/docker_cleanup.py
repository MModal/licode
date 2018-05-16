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

def main(service_path):
    service_vars = common_vars.get_service_variables(service_path)
    registry = service_vars["registry"]
    root = service_vars["root"]
    
    repo = service_vars["repo"]
    service_name = service_vars["service_name"]
    image_id_file = service_vars["image_id_file"]
    unique_tag = service_vars["unique_tag"]
    image_id = read_from_file(image_id_file)

    #Remove all other imageswith the same id 
    print("Removing all other images for service {}".format(service_name))
    docker_cleanup_script = """
        docker images {0} | grep {1} | while read -r line; do
            tag=$(echo ${{line}} | awk '{{print $2}}')
            docker rmi {0}:${{tag}} || true
        done""".format(repo, image_id, unique_tag)

    print("The docker cleanup script to run is: {0}".format(docker_cleanup_script))
    print("Removing the docker images.")
    
    subprocess.check_output(
    docker_cleanup_script,
    stderr=subprocess.STDOUT,
    shell=True
    )
    print("Cleanup succesfull for {0}.".format(service_name))

if __name__ == "__main__":
    parameters = get_parameters()
    service_path = parameters["path"]
    main(service_path)
