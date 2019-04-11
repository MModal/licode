import common_vars, subprocess, os, argparse


def read_from_file(filename):
    try:
        f = open(filename, "r")
        if f.mode == "r":
            return f.read()
        else:
            print("Could not read file. ")
            return None
    except IOError:
        print("ID file '{}' for image build did not exist.".format(filename))
        return None


def remove_image_id_file(image_id_file):
    subprocess.check_output(
        "rm {}".format(image_id_file),
        stderr=subprocess.STDOUT,
        shell=True
    )


def remove_image(repo, image_id, unique_tag):
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


def docker_prune():
    subprocess.check_output(
        "docker system prune -f",
        stderr=subprocess.STDOUT,
        shell=True
    )


def remove_tar_file(image_tar_file):
    if os.path.isfile(image_tar_file):
        subprocess.check_output(
            # "rm $(find {} -type f -name '*.tar') || true".format(root),
            "rm {}".format(image_tar_file),
            stderr=subprocess.STDOUT,
            shell=True
        )
    else:
        print("No image tar file found")


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("service_path",
                        help="Root directory where Dockerfile and vars.py configuration files are located.")
    args = parser.parse_args()

    if not args.service_path:
        parser.error("Path to root directory of microservice required")

    params = {'service_path': args.service_path}

    return params


def main(service_path, service_name):
    service_vars = common_vars.get_service_variables(service_path, service_name)
    repo = service_vars["repo"]
    image_id_file = service_vars["image_id_file"]
    unique_tag = service_vars["unique_tag"]
    image_tar_file = service_vars["image_tar_file"]
    image_id = read_from_file(image_id_file)

    if image_id:
        print("Removing all other images for service {}".format(service_name))
        remove_image(repo, image_id, unique_tag)
        print("Removing ID image file.".format(service_name))
        remove_image_id_file(image_id_file)

    print("Performing a docker prune")
    docker_prune()
    print("Removing generated tar files.")
    remove_tar_file(image_tar_file)

    print("Cleanup successful for {0}.".format(service_name))


# TODO: Implement cleanup as a standolone which would take a service to cleanup after.
if __name__ == "__main__":
    parameters = get_parameters()
    service_path_main = parameters["path"]
    main(service_path_main)
