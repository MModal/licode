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
def main(service_name, dockerfile, workingdir, default_tag="default"):
    service_vars = common_vars.get_service_variables(service_name, default_tag)
    root = service_vars["root"]
    branch = service_vars["branch"]
    registry = service_vars["registry"]
    repo = service_vars["repo"]
    version = service_vars["version"]
    is_versioned = service_vars["is_versioned"]
    image_tar_name = service_vars["image_tar_name"]
    image_tar_file = service_vars["image_tar_file"]
    branch_id = service_vars["branch_id"] 
    build_number = service_vars["build_number"]
    unique_tag = service_vars["unique_tag"] 
    
    #Build the docker build script
    dockerBuildScript = """
        docker build \\
        -f {0} \\
        -t {1}:latest-build \\
        -t {1}:{2} \\
        {3}
    """.format(dockerfile, repo, unique_tag, workingdir).strip()

    #Execute the script to build the image
    print("Building the service image of {0} with script: \n{1}".format(service_name ,dockerBuildScript))
    proc = subprocess.Popen(dockerBuildScript,
        shell=True, stdout=sys.stdout, stderr=sys.stderr)
    proc.wait()
    print("Finished building the docker image.")
    
    #Fetch the docker image id
    image_id = get_image_id(repo, unique_tag)
    image_id_file = service_vars["image_id_file"]

    print("Saving the image id to file:" + image_id_file)
    write_to_file(image_id_file, image_id)

    #Tag the image appropriately per version
    version_tag_script = ""
    if(branch == "default"):
        print("Branch is default. Tagging the docker image with its version if found")
        if is_versioned: 
             major = version
             minor = version[:version.rfind(".")]
             patch = version[:version.find(".")]
             version_tag_script = """
                 docker tag {0} {1}:{2}
                 docker tag {0} {1}:{3}
                 docker tag {0} {1}:{4}
                 docker tag {0} {1}:latest
             """.format(image_id, repo, major, minor, patch)

        else:
           version_tag_script = "docker tag {0} {1}:{2}".format(image_id, repo, version)
    else:
        version_tag_script = "docker tag {0} {1}:{2}".format(image_id, repo, version)
    
    print("Tagging the docker image with version: %s " % version)
    subprocess.check_output(
        version_tag_script,
        stderr=subprocess.STDOUT,
        shell=True)

    #Save the docker image as a tar file to transfer to server.
    print("Saving the docker image as a tar file to: " + image_tar_file)
    save_image_script = "docker save -o {0} {1}:{2}".format(image_tar_file, repo, version)
    subprocess.check_output(
    save_image_script,
    stderr=subprocess.STDOUT,
    shell=True)

    print("Save succesfull. Build and save succesfull for {0}.".format(service_name))

if  __name__ == "__main__":
    parameters = get_parameters()
    main(parameters["servicename"], parameters["dockerfile"], parameters["workingdir"])
