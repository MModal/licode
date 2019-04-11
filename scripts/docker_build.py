import argparse
import subprocess
import common_vars


def get_image_id(repo, unique_tag):
    fetch_id_command = """
        docker images {0} | grep {1} | head -n 1 | awk '{{print $3}}'
    """.format(repo, unique_tag)

    pipe = subprocess.Popen(
        fetch_id_command,
        shell=True,
        stdout=subprocess.PIPE
    )

    image_id = pipe.stdout.read()
    return image_id.strip()


def write_to_file(filename, text):
    f = open(filename, "w")
    f.write(text)
    f.close()


def get_build_number():
    pipe = subprocess.Popen(
        ["echo", "${BUILD_NUMBER}"],
        stdout=subprocess.PIPE
    )
    branchNumber = pipe.stdout.read()
    return branchNumber.strip()


def get_branch_id():
    pipe = subprocess.Popen(
        ["hg", "id", "-i"],
        stdout=subprocess.PIPE
    )

    branch_id = pipe.stdout.read().replace('+', '')
    return branch_id.strip()


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("service_path",
                        help="Root directory where Dockerfile and vars.py configuration files are located.")
    args = parser.parse_args()

    if not args.service_path:
        parser.error("Path to root directory of microservice required")

    params = {'service_path': args.service_path}

    return params


def main(dockerfile_path, service_name):
    service_vars = common_vars.get_service_variables(dockerfile_path, service_name)
    repo = service_vars["repo"]
    version = service_vars["version"]
    is_versioned = service_vars["is_versioned"]
    image_tar_file = service_vars["image_tar_file"]
    unique_tag = service_vars["unique_tag"]
    build_args = service_vars["build_args"]
    service_path = service_vars["service_path"]
    # Build the docker build script
    dockerBuildScript = """
        docker build \\
        --no-cache \\
        -f {0} \\
        -t {1}:latest-build \\
        -t {1}:{2} \\
        {3} {4}
    """.format(dockerfile_path, repo, unique_tag, service_path, build_args).strip()

    # Execute the script to build the image
    print("Building the service image of {0} with script: \n{1}".format(service_name, dockerBuildScript))
    print subprocess.check_output(
        dockerBuildScript,
        stderr=subprocess.STDOUT,
        shell=True)

    print("Finished building the docker image.")

    # Fetch the docker image id
    image_id = get_image_id(repo, unique_tag)
    image_id_file = service_vars["image_id_file"]

    print("Saving the image id to file:" + image_id_file)
    write_to_file(image_id_file, image_id)

    # Tag the image appropriately per version
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

    print("Tagging the docker image with version: %s " % version)
    print subprocess.check_output(
        version_tag_script,
        stderr=subprocess.STDOUT,
        shell=True)

    # Save the docker image as a tar file to transfer to server.
    print("Saving the docker image as a tar file to: " + image_tar_file)
    save_image_script = "docker save -o {0} {1}:{2}".format(image_tar_file, repo, version)
    print subprocess.check_output(
        save_image_script,
        stderr=subprocess.STDOUT,
        shell=True)

    print("Save successful. Build and save successful for {0}.".format(service_name))

    if __name__ == "__main__":
        parameters = get_parameters()
        main(parameters["service_path"])
