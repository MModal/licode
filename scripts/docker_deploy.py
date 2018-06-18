import argparse
import os
import subprocess
import common_vars 
import json
import getpass
import syslog
import errno

def execute_ssh_command(credentials_dictionary, server, command):
    user = credentials_dictionary["user"]
    public_key = credentials_dictionary["public_key"]
    user_server = user + "@" + server

    ssh_command = "ssh {} {} \"{}\"".format(public_key, user_server, command)
    
    common_vars.subprocess_with_print(ssh_command)
    
def get_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Root directory where Dockerfile and vars.py configuration files are located.")
    parser.add_argument("tar_file", help = "Location of the tar file docker image that will be deployed.")
    args = parser.parse_args()

    if not args.path:
       parser.error("Path to root directory of microservice required")
    if not args.tar_file:
       parser.error("Location of the tar file docker image required.")

    parameters = {'path': args.path, "tar_file": args.tar_file}
    return parameters

def display_options(services):
    print("{:*^85}".format(" Scribe Docker Images Deploy Script "))
    print("""The target services that you will be deploying are:\n{0:<25}{1:>25}{2:>35}""").format("SERVER","SERVICE", "VERSION")
    credentials_dictionary = {}
    for server in services.keys():
        print("""{0:<25}""".format(server)) 
        for service in services[server].keys():
            version = services[server][service]["version"]
            print("""{0:>50}{1:>35}""".format(service, version))
    
    previous_user = ""
    previous_public_key = ""
    for server in services.keys():
        server_dictionary = {}
        user = raw_input("\nWhat user will you be using to deploy to {}? (Leave empty if same as previous user):\n".format(server)) 
        if not user:
            user = previous_user;
        else:
            previous_user = user;

        server_dictionary.update({"user":user})
        
        public_key = raw_input("What is the location of the public key for {}?(Leave empty if same as previous key): \n".format(server))
        if not public_key:
            public_key = previous_public_key;
        if os.path.isfile(public_key):
            previous_public_key = public_key;
            public_key = "-i " + public_key 
            server_dictionary.update({"public_key":public_key})
        else:
            raise IOError("Public key '{}' not found.".format(public_key))
        
        credentials_dictionary.update({server:server_dictionary})
        execute_ssh_command(server_dictionary, server,"echo test")

        print("Authentication succesfull for server {}".format(server))

    return (credentials_dictionary)

def scp_image(user, public_key, image_tar_file, server, remote_location):
    scp_script = """ scp {0} {1} {2}@{3}:{4} """.format(public_key, image_tar_file, user,server,  remote_location)
    common_vars.subprocess_with_print(scp_script)

def restart_remote_syslog(credentials_dict, server):
    user = credentials_dict["user"]
    public_key = credentials_dict["public_key"]
    user_server = user + "@" + server
    sudo_ssh_command = "ssh {} {} 'sudo sh -c \"service syslog restart\"'".format(public_key,user_server)

    print subprocess.check_output(
    sudo_ssh_command,
    shell = True,
    stderr = subprocess.STDOUT
    )

def check_remote_tar(user, key, server, remote_file):
    remote_file = image_tar_file
    script = 'ssh {} {}@{} [[ -f {} ]] && printf 'True' || printf 'False';'.format(key, user, server, remote_file)
    pipe = subprocess.Popen(script, shell=True, stdout = subprocess.PIPE)  
    output = pipe.stdout.readline() == "True"
    print(output)
    return output

def deploy_prod():
    config_file_original = json.load(open("deploy_config.json"))
    config_file = dict(config_file_original)
    del config_file["dev_server"]

    repo = "artifactory-pit.mmodal-npd.com/mmodal/ffs/"
    root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    remote_location = "/tmp/"
    credentials_dict = display_options(config_file)

    for server in config_file.keys():
         print("Adding necessary syslog rules to {}".format(server))
         credentials = credentials_dict[server]
         add_syslog_rule(credentials, server, "scribe-operations")
         for service in config_file[server].keys():
            add_syslog_rule(credentials, server, service)
         print("Restarting syslog remotely")
         restart_remote_syslog(credentials, server)

    for server in config_file.keys():
         print("Beginning deploy process for {}".format(server))
         for service in config_file[server].keys():
             version = config_file[server][service]["version"]
             flags = config_file[server][service]["flags"]
             user = credentials_dict[server]["user"]
             public_key = credentials_dict[server]["public_key"]
             image_tar_name = service + "-" + version + ".tar"
             remote_tar_location = "/tmp/" + image_tar_name
             image_tar_file = root + "/" + image_tar_name 
             repo_service = repo + service
             container = service + "-" + version

             #Pull Docker image
             print("\nPulling the docker image for: {}".format(service+":"+version))
             pull_docker_image(repo,service, version)

             #Save Docker Image as tar
             print("Saving the docker image for: {} as a tar file".format(service+":"+version))
             if os.path.isfile(image_tar_file):
                 print("Tar file already existed. Will not create it again.")
             else:
                 save_image(repo, service, version, image_tar_file)

             remote_file_exists = check_remote_tar(user, credentials["public_key"], server, remote_tar_location)
             if remote_file_exists
               #Transfer the docker image over scp
               print("Image did not exist on remote, transferring the docker image to remote over scp...")
               scp_image(user, credentials["public_key"], image_tar_file, server, remote_location)
             else:
               print("Image did exist on remote, wont transfer it.")
            
             #Log the name of the user that is trying to deploy
             log_message_script = "logger -t {0} User {1} will try to replace the version: \$EXISTING_VERSION of service: {2} with version: {3};".format("scribe-operations",user,service, version)

             #Get the name of the current running service with the same name and log it.
             fetch_running_services_script = "EXISTING_VERSION=\$(sudo docker ps -a | grep {} | awk '{{print \$2}}' | sed 's/.*\://');".format(service)
              
             #Build the entire script.
             #TODO: Break this apart into separate ssh call for better management
             print("Deploying the container for: {}.".format(service))
             ssh_payload = fetch_running_services_script + log_message_script + docker_load(remote_tar_location) + docker_stop(repo_service) + docker_run(container, flags, repo_service, version)
             ssh_script = """ssh {0} {1} \"{2}\" """.format(public_key, user + "@" + server, ssh_payload)

             #Execute it over ssh
             print subprocess.check_output(
                     ssh_script,
                     stderr = subprocess.STDOUT,
                     shell=True)
             print("Deployment succesfull!")
    
def pull_docker_image(repo, service, version):
    print subprocess.check_output(
    "docker pull {}{}:{}".format(repo,service, version),
    shell=True,
    stderr = subprocess.STDOUT
    )

def save_image(repo,service, version,location):
    print subprocess.check_output(
    "docker save -o {0} {1}{2}:{3}".format(location, repo, service, version),
    shell=True,
    stderr = subprocess.STDOUT
    )

def docker_stop(container):
    
    docker_stop_script = """sudo docker ps -a | grep {0} | while read -r line; do
        SERVICE_ID=\$( echo \${{line}} | awk '{{print \$1}}');
        sudo docker stop \"\${{SERVICE_ID}}\" || true;
        sudo docker rm \"\${{SERVICE_ID}}\" || true;
        done
    """.format(container)
 
    return docker_stop_script

def docker_load(image_tar_file):
    docker_load_script = "sudo docker load -i {0};".format(image_tar_file)

    return docker_load_script 

def docker_run(container, flags, repo, tag, commands=""):
    docker_run_script = """sudo docker run -d \
    --log-driver \"syslog\" --log-opt tag=\"{0}/{{{{.ID}}}}\" \
    {1} \
    --name={0} {2}\
    {3}:{4}""".format(container, flags, commands, repo, tag)

    return docker_run_script.strip()

def add_syslog_rule(credentials_dict, server, service_name):
    
    #Write rsyslog rule for this service if it doesn't exist
    syslog_filename = "10-scribe-docker-{0}.conf".format(service_name)
    syslog_filepath_string = "/etc/rsyslog.d/{0}".format(syslog_filename)
    user = credentials_dict["user"]
    user_server = user + "@" + server
    public_key = credentials_dict["public_key"]

    ssh_payload = """ ssh {} {} "bash -s" < syslogScript.sh {}
    """.format( public_key, user_server, service_name)
    
    print subprocess.check_output(
    ssh_payload,
    shell=True,
    stderr = subprocess.STDOUT
    )

    print("Created new syslog rule for this service(if not there): {0}".format(service_name))
 
def main(service_path, tar_file):
    
    service_vars = common_vars.get_service_variables(service_path) 
   
    key_location= "~/scribe/Scribe-Dev.pem"
    server = service_vars["server"]
    remote_location = "/tmp/"
    container = service_vars["container"]
    config = service_vars["config"]
    network = service_vars["network"]
    version = service_vars["version"]
    image_tar_name = service_vars["image_tar_name"]
    image_tar_file = service_vars["image_tar_file"] 
    remote_image = remote_location + image_tar_name
    repo = service_vars["repo"]
    service_name = service_vars["service_name"]
    volume = service_vars["volume"]
    flags = service_vars["flags"] 
    user = service_vars["user"] 
    credentials = {"user":user, "public_key": "-i " + key_location}

    
    print("Checking if image exists on remote")
    if check_remote_tar(user, credentials["public_key"], server, remote_image):
      #Transfer the docker image over scp
      print("Image did not exist, transferring the docker image to remote over scp...")
      scp_image(user, credentials["public_key"], image_tar_file, server, remote_location)
    else:
      print("Image did exist, wont transfer it.")

    #Add syslog confs needed for the service
    print("Adding the necessary syslog conf rules")
    add_syslog_rule(credentials, server, service_name)
    restart_remote_syslog(credentials, server)

    #Stop the remote docker containers
    print("Stopping the remote docker container:")
    execute_ssh_command(credentials, server, docker_stop(repo))

    #Load the docker image 
    print("Remotely loading the image to docker:")
    execute_ssh_command(credentials, server, docker_load(remote_image))

    #Start the new docker container
    print("Starting the remote instance:")
    execute_ssh_command(credentials, server, docker_run(container, flags, repo, version))
    
    #Delete the tar file that got transferred
    print("Deleting the tar file that got transferred")
    execute_ssh_command(credentials, server, "rm {}".format(remote_image))
     
    #For automatic deployments, delete all of the previous images.
    execute_ssh_command(credentials,server,"sudo docker image prune -f")

    print("End of script. Deploy succesfull for {0}.".format(service_name))

if  __name__ == "__main__":
    deploy_prod()
