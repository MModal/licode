import argparse
import os
import subprocess
import common_vars
import json
import collections
from docker_cleanup import remove_tar_file


def execute_ssh_command(credentials_dictionary, server, command):
    server_dict = credentials_dictionary[server]
    user = server_dict["user"]

    user_server = user + "@" + server
    ssh_command = "ssh {} {} \"{}\"".format(server_dict["public_key"], user_server, command)
    print subprocess.check_output(
        ssh_command,
        shell=True,
        stderr=subprocess.STDOUT
    )


def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Root directory where Dockerfile and vars.py configuration files are located.")
    parser.add_argument("tar_file", help="Location of the tar file docker image that will be deployed.")
    args = parser.parse_args()

    if not args.path:
        parser.error("Path to root directory of microservice required")
    if not args.tar_file:
        parser.error("Location of the tar file docker image required.")

    parameters = {'path': args.path, "tar_file": args.tar_file}
    return parameters


def display_options(services):
    print("{:*^110}".format(" Scribe Docker Images Deploy Script "))
    print("""The target services that you will be deploying are:\n{0:<25}{1:>25}{2:>35}{3:>25}""").format("SERVER",
                                                                                                          "SERVICE",
                                                                                                          "VERSION",
                                                                                                          "ENABLED")
    for server in services.keys():
        print("""{0:<25}""".format(server))
        for service in services[server]:
            service_name = service["service_name"]
            version = service["version"]
            enable = "True"
            if service["enable"] == "false":
                enable = "False"
            print("""{0:>50}{1:>35}{2:>25}""".format(service_name, version, enable))




def filter_servers(config_file):
    copy_dict = {}
    for server_ip in config_file:
        service_array = []
        for service in config_file[server_ip]:
            if service["enable"] == "true":
                service_array.append(service)
        if len(service_array) > 0:
            copy_dict[server_ip] = service_array
    return copy_dict

def ask_for_approval():
    response = "N"
    while response.lower() != "y":
        response = raw_input("Does this look okay? Type 'y' to continue or 'q' to exit\n")
        if response.lower() == 'q':
            exit(0)

    return

def fetch_credentials(config_file, global_creds):
    credentials_dictionary = {}
    previous_user = ""
    previous_public_key = ""

    for server in config_file.keys():
        server_dictionary = {}
        if global_creds:
            server_dictionary.update({"user": global_creds["user"]})
            key = "-i " + global_creds["ssh_key"]
            server_dictionary.update({"public_key": key})
        else:
            user = raw_input(
                "\nWhat user will you be using to deploy to {}? (Leave empty if same as previous user):\n".format(
                    server))
            if not user:
                user = previous_user
            else:
                previous_user = user

            server_dictionary.update({"user": user})

            public_key = raw_input(
                "What is the location of the public key for {}?(Leave empty if same as previous key): \n".format(
                    server))
            if not public_key:
                public_key = previous_public_key
            if os.path.isfile(public_key):
                previous_public_key = public_key
                flag_key = "-i " + public_key
                server_dictionary.update({"public_key": flag_key})
            else:
                raise IOError("Public key '{}' not found.".format(public_key))

        credentials_dictionary.update({server: server_dictionary})
        print("Testing authentication for {}".format(server))
        execute_ssh_command(credentials_dictionary, server, "echo Authentication succesfull for {}".format(server))

    return (credentials_dictionary)


def get_remove_script(repo):
    remote_script = """FLAG=0;
                      sudo docker image ls {} -q | while read -r line; do   
                          if [ $FLAG -eq 0 ]; then 
                              FLAG=1;   
                          else   
                              sudo docker rmi ${{line}} ;   
                              echo Removed image: ${{line}};   
                          fi 
                      done""".format(repo)
    return remote_script


def remove_remote_image(user, public_key, server, remote_image):
    remote_script = "rm {}".format(remote_image)

    ssh_command = "ssh -i {} {}@{} '{}'".format(public_key, user, server, remote_script)

    print subprocess.check_output(
        ssh_command,
        stderr=subprocess.STDOUT,
        shell=True
    )


def remove_other_images(user, public_key, server, repo):
    remote_script = get_remove_script(repo)

    ssh_command = "ssh -i {} {}@{} '{}'".format(public_key, user, server, remote_script)

    print subprocess.check_output(
        ssh_command,
        stderr=subprocess.STDOUT,
        shell=True
    )


def scp_image(user, public_key, image_tar_file, server, remote_location):
    scp_script = """ scp {0} {1} {2}@{3}:{4} """.format(public_key, image_tar_file, user, server, remote_location)
    print subprocess.check_output(
        scp_script,
        stderr=subprocess.STDOUT,
        shell=True,
    )


def restart_remote_syslog(credentials_dict, server):
    user = credentials_dict["user"]
    public_key = credentials_dict["public_key"]
    user_server = user + "@" + server
    sudo_ssh_command = "ssh {} {} 'sudo sh -c \"service syslog restart\"'".format(public_key, user_server)

    print subprocess.check_output(
        sudo_ssh_command,
        shell=True,
        stderr=subprocess.STDOUT
    )


def check_remote_tar(user, key, server, remote_file):
    script = 'ssh {} {}@{} [[ -f {} ]] && printf "True" || printf "False";'.format(key, user, server, remote_file)
    pipe = subprocess.Popen(script, shell=True, stdout=subprocess.PIPE)
    output = pipe.stdout.readline() == "False"
    return output


def deploy_prod():
    config_file_original = json.load(open("deploy_config.json"), object_pairs_hook=collections.OrderedDict)
    config_file = collections.OrderedDict(config_file_original)
    del config_file["dev_server"]
    global_creds = ""
    try:
        global_creds = config_file["credentials"]
        del config_file["credentials"]
    except:
        pass

    repo = "artifactory-pit.mmodal-npd.com/mmodal/ffs/"
    root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    remote_location = "/tmp/"
    display_options(config_file)
    ask_for_approval()
    config_file = filter_servers(config_file)
    credentials_dict = fetch_credentials(config_file, global_creds)

    for server in config_file.keys():
        print("Beginning deploy process for {}".format(server))
        print("Adding necessary syslog rules to {}".format(server))
        credentials = credentials_dict[server]
        add_syslog_rule(credentials, server, "scribe-operations")
        for index in range(0, len(config_file[server])):
            if "alias" in config_file[server][index].keys():
                service_name = config_file[server][index]["alias"]
            else:
                service_name = config_file[server][index]["service_name"]
            add_syslog_rule(credentials, server, service_name)
        print("Restarting syslog remotely")
        restart_remote_syslog(credentials, server)
        deployed_services = []

        for service in config_file[server]:
            service_name = service["service_name"]
            alias = service["alias"] if "alias" in service else service["service_name"]
            print("Deploying service:'{}' to server:'{}'".format(service_name, server))
            version = service["version"]
            flags = service["flags"]
            user = credentials_dict[server]["user"]
            public_key = credentials_dict[server]["public_key"]
            commands = service["commands"]
            image_tar_name = service_name + "-" + version + ".tar"
            remote_tar_location = "/tmp/" + image_tar_name
            image_tar_file = root + "/" + image_tar_name
            repo_service = repo + service_name
            container = service_name + "-" + version

            if repo_service not in deployed_services:
                # Pull Docker image
                print("\nPulling the docker image for: {}".format(service_name + ":" + version))
                pull_docker_image(repo, service_name, version)

                # Save Docker Image as tar
                print("Saving the docker image for: {} as a tar file".format(service_name + ":" + version))
                if os.path.isfile(image_tar_file):
                    print("Tar file already existed. Will not create it again.")
                else:
                    save_image(repo, service_name, version, image_tar_file)

                if check_remote_tar(user, credentials["public_key"], server, remote_tar_location):
                    # Transfer the docker image over scp
                    print("Image did not exist on remote, transferring the docker image to remote over scp...")
                    scp_image(user, credentials["public_key"], image_tar_file, server, remote_location)
                else:
                    print("Image did exist on remote, wont transfer it.")

                # Log the name of the user that is trying to deploy
                log_message_script = "logger -t {0} User {1} will try to replace the version: \$EXISTING_VERSION of service: {2} with version: {3};".format(
                    "scribe-operations", user, service_name, version)

                # Get the name of the current running service with the same name and log it.
                fetch_running_services_script = "EXISTING_VERSION=\$(sudo docker ps -a | grep {} | awk '{{print \$2}}' | sed 's/.*\://');".format(
                    service_name)

                print("Deploying the container for: {}.".format(service_name))

                print("Logging the existing version of the service to be replaced")
                execute_ssh_command(credentials_dict, server, fetch_running_services_script + log_message_script)

                print("Stopping the remote instances of {}".format(service_name))
                execute_ssh_command(credentials_dict, server, docker_stop(repo_service))

                print("Removing other images of this services except for the last one")
                execute_ssh_command(credentials_dict, server, get_remove_script(repo))

                print("Loading the docker image to be deployed.")
                execute_ssh_command(credentials_dict, server, docker_load(remote_tar_location))

                print("Removing the remote tar file for {}".format(image_tar_file))
                execute_ssh_command(credentials_dict, server, "rm {}".format(remote_tar_location))

                deployed_services.append(repo_service)

            print("Running the new instance of {}".format(service_name))
            execute_ssh_command(credentials_dict, server, docker_run(alias, flags, repo_service, version, commands))

            print("Removing generated tar file from local")
            remove_tar_file(image_tar_file)

            print("Deployment succesfull!")


def pull_docker_image(repo, service, version):
    print subprocess.check_output(
        "docker pull {}{}:{}".format(repo, service, version),
        shell=True,
        stderr=subprocess.STDOUT
    )


def save_image(repo, service, version, location):
    print subprocess.check_output(
        "docker save -o {0} {1}{2}:{3}".format(location, repo, service, version),
        shell=True,
        stderr=subprocess.STDOUT
    )


def docker_stop(container):
    docker_stop_script = """sudo docker ps -a | grep {0} | while read -r line; do
        SERVICE_ID=\$( echo \${{line}} | awk '{{print \$1}}');
        sudo docker stop \"\${{SERVICE_ID}}\" || true;
        sudo docker rm -f \"\${{SERVICE_ID}}\" || true;
        done
    """.format(container)

    return docker_stop_script


def docker_load(image_tar_file):
    docker_load_script = "sudo docker load -i {0};".format(image_tar_file)

    return docker_load_script


def docker_run(container, flags, repo, tag, commands=""):
    docker_run_script = """sudo docker run -d \
    --log-driver \"syslog\" --log-opt tag=\"{0}/{{{{.ID}}}}\" \
    --name {0} \
    {1} \
    {2}:{3} {4}""".format(container, flags, repo, tag, commands)

    return docker_run_script.strip()


def add_syslog_rule(credentials_dict, server, service_name):
    # Write rsyslog rule for this service if it doesn't exist
    syslog_filename = "10-scribe-docker-{0}.conf".format(service_name)
    syslog_filepath_string = "/etc/rsyslog.d/{0}".format(syslog_filename)
    user = credentials_dict["user"]
    user_server = user + "@" + server
    public_key = credentials_dict["public_key"]

    ssh_payload = """ ssh {} {} "bash -s" < syslogScript.sh {}
    """.format(public_key, user_server, service_name)

    print subprocess.check_output(
        ssh_payload,
        shell=True,
        stderr=subprocess.STDOUT
    )

    print("Created new syslog rule for this service(if not there): {0}".format(service_name))


def main(service_path, default_tag="default"):
    service_vars = common_vars.get_service_variables(service_path)

    key_location = "~/scribe/Scribe-Dev.pem"
    server = service_vars["server"]
    remote_location = "/tmp/"
    container = service_vars["container"]
    version = service_vars["version"]
    image_tar_name = service_vars["image_tar_name"]
    image_tar_file = service_vars["image_tar_file"]
    remote_image = remote_location + image_tar_name
    repo = service_vars["repo"]
    service_name = service_vars["service_name"]
    commands = service_vars["commands"]
    flags = service_vars["flags"]
    user = service_vars["user"]
    credentials = {"user": user, "public_key": "-i " + key_location, "server": server}

    print("Deploying: {0}, with tar_file in: {1}".format(service_path, image_tar_file))

    print("Checking if image exists on remote")
    if check_remote_tar(user, credentials["public_key"], server, remote_image):
        # Transfer the docker image over scp
        print("Image did not exist, transferring the docker image to remote over scp...")
        scp_image(user, credentials["public_key"], image_tar_file, server, remote_location)
    else:
        print("Image did exist, wont transfer it.")

    # Add syslog confs needed for the service
    print("Adding the necessary syslog conf rules")
    add_syslog_rule(credentials, server, service_name)
    restart_remote_syslog(credentials, server)

    print("Remove other images except the previous one for {}".format(repo))
    remove_other_images(user, key_location, server, repo)

    # Build the docker script to execute over ssh
    container_startup_script = docker_stop(repo) + docker_load(remote_image) + docker_run(container, flags, repo,
                                                                                          version, commands)
    ssh_script = "ssh -i {0} {1} \"{2}\"".format(key_location, user + "@" + server, container_startup_script)

    # Execute the script over ssh
    print("Remotely starting docker container with script: \n" + ssh_script)
    print subprocess.check_output(
        ssh_script,
        stderr=subprocess.STDOUT,
        shell=True)

    print("Removing the remote tar file for {}".format(image_tar_file))
    remove_remote_image(user, key_location, server, remote_image)

    print("End of script. Deploy succesfull for {0}.".format(service_name))


if __name__ == "__main__":
    deploy_prod()
