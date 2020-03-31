import argparse
import os
import sys
import subprocess
import common_vars

def get_image_id(repo, unique_tag):
    fetch_id_command = """
        docker images {0} | grep {1} | head -n 1 | awk '{{print $3}}'
    """.format(repo,unique_tag)
    
    pipe = subprocess.Popen(
    fetch_id_command,
    shell=True,
    stdout = subprocess.PIPE
    )
    
    image_id = pipe.stdout.read()
    return image_id.strip()

def write_to_file(filename, text):
    f = open(filename, "w")
    f.write(text)
    f.close()


def get_build_number():
    pipe = subprocess.Popen(
    ["echo","${BUILD_NUMBER}"],
    stdout = subprocess.PIPE
    )
    branchNumber = pipe.stdout.read()
    return branchNumber.strip()

def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("service_path", help="Root directory where Dockerfile and vars.py configuration files are located.")
    args = parser.parse_args()
    
    if not (args.service_path):
       parser.error("Path to root directory of microservice required")
  
    parameters = {'service_path': args.service_path}

    return parameters

#def main(service_path, default_tag="default"):
def main(service_name, dockerfile, workingdir, artifactory_registry, ecr_registry):
    service_vars = common_vars.get_service_variables(service_name, artifactory_registry, ecr_registry)
    branch = service_vars["branch"]
    artifactory_repo = service_vars["artifactory_repo"]
    ecr_repo = service_vars["ecr_repo"]
    version = service_vars["version"]
    image_tar_file = service_vars["image_tar_file"]
    unique_tag = service_vars["unique_tag"] 
    
    #Build the docker build script
    dockerBuildScript = """
        docker build \\
        -f {0} \\
        -t {1}:latest-build \\
        -t {1}:{3} \\
        -t {1}:{4} \\    
        -t {2}:latest-build \\
        -t {2}:{3} \\
        -t {2}:{4} \\
        {5}
    """.format(dockerfile, artifactory_repo, ecr_repo, unique_tag, version, workingdir).strip()

    #Execute the script to build the image
    print("Building the service image of {0} with script: \n{1}".format(service_name ,dockerBuildScript))
    proc = subprocess.Popen(dockerBuildScript,
        shell=True, stdout=sys.stdout, stderr=sys.stderr)
    proc.wait()
    print("Finished building the docker image.")
    
    #Fetch the docker image id
    image_id = get_image_id(artifactory_repo, unique_tag)
    image_id_file = service_vars["image_id_file"]

    print("Saving the image id to file:" + image_id_file)
    write_to_file(image_id_file, image_id)

    #Save the docker image as a tar file to transfer to server.
    print("Saving the docker image as a tar file to: " + image_tar_file)
    save_image_script = "docker save -o {0} {1}:{2}".format(image_tar_file, artifactory_repo, version)
    subprocess.check_output(
    save_image_script,
    stderr=subprocess.STDOUT,
    shell=True)

    print("Save succesfull. Build and save succesfull for {0}.".format(service_name))

if  __name__ == "__main__":
    parameters = get_parameters()
    main(parameters["servicename"], parameters["dockerfile"], parameters["workingdir"], parameters["artifactoryreg"], parameters["ecrreg"])
