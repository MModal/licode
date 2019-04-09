import os
import subprocess
import re
import json

vcs_type = ""


def subprocess_with_print(command):
    print subprocess.check_output(
       command,
       shell = True,
       )

def get_vcs_type():

    try:
        subprocess.check_output(
        ["git","status"],
        stderr = subprocess.STDOUT,
        shell = False
        )
        return "git"
    except subprocess.CalledProcessError:

         try:
             subprocess.check_output(
             ["hg","status"],
             stderr = subprocess.STDOUT,
             shell = False
             )
             return "hg"
         except subprocess.CalledProcessError:
             print("No valid VCS detected (Mercurial or Git).")
             raise
        
def get_from_config_file(config_file, *config_keys):
    data = json.load(open(config_file))
    for key in config_keys:
       data = data[key]
    return data


def get_dev_server():

    config_file= os.path.realpath(os.path.dirname(__file__)) + "/deploy_config.json"
    data = json.load(open(config_file)) 
    user = data["dev_server"]["user"]
    server = data["dev_server"]["server"]
    return user,server

        
def get_volume(config, config_file):
    data = json.load(open(config_file))
    data_config = data[config]
    if "cert_volume" in data_config:
        cert_volume = data_config["cert_volume"]
        return " -v /opt/licode/cert:{0}".format(cert_volume)
    else:
        return ""

def get_network(config, config_file):
    data = json.load(open(config_file))
    data_config = data[config]
    if "host_port" in data_config and "container_port" in data_config:
        host_port = data_config["host_port"]
        container_port = data_config["container_port"]
        return "-p {0}:{1}".format(host_port, container_port)
    elif "network" in data_config:
        return "--net={0}".format(data_config["network"])
    else:
        return ""

def get_branch_id():
    branch_id = ""
    if vcs_type == "hg":
         pipe = subprocess.Popen(
         ["hg","id","-i"],
         stdout = subprocess.PIPE
         )   
         branch_id = pipe.stdout.read().replace('+','')

    elif vcs_type == "git":
        pipe = subprocess.Popen(
        ["git","log","--pretty=format:'%h'","-n","1"],
        stdout = subprocess.PIPE
        )
        branch_id = pipe.stdout.read().replace("'","")
    
    if not branch_id:
        raise IOError("Error, no branch id found for mercurial or git.")

    return branch_id.strip()
 

def get_branch():
    branch = ""

    if vcs_type == "hg":
         pipe = subprocess.Popen(
         ["hg","branch"],
         stdout = subprocess.PIPE 
         )
         branch = pipe.stdout.read().strip()

    elif vcs_type == "git":
        pipe = subprocess.Popen(
        ["git","rev-parse","--abbrev-ref","HEAD"], 
        stdout = subprocess.PIPE,
        )
        branch = pipe.stdout.read().strip()
        if branch == "master":
            branch = "default"

    return branch

def get_version( service, default_tag, branch):
    version = ""
    is_versioned = False    
    if branch == "default":
         #Get the last tag.
         if vcs_type == "hg":
             pipe = subprocess.Popen(
             "hg log -r \".\" --template \"{latesttag}\n\"",
             shell=True,
             stdout=subprocess.PIPE
             )   
             latest_tag = pipe.stdout.read()

         elif vcs_type == "git":
            pipe = subprocess.Popen(
            ["git","describe","tags"],
            shell = False,
            stdout = subprcocess.PIPE
            )
            latest_tag = pipe.stdout.read()

         #Try to find a version from the tag, and if it matches the service name use it. 
         service_and_version = re.findall('(\w+-\d+\.\d+\.\d+(?!-))', latest_tag)

         if service_and_version:
             for match in service_and_version:
                 service_name = re.search('\w+(?=-)',match).group()
                 if service_name == service:
                     found_version = re.search('\d+\.\d+\.\d+', match).group()
                     version = found_version
                     is_versioned = True
                     return version, is_versioned 
         
         #Check if the tag is a release candidate, and if it matches the service name use it.
         version = search_for_RC(latest_tag, service)

         if not version:
            version = default_tag 
    else:
        version = branch
    return version, is_versioned

def search_for_RC(latest_tag, service):
   version = ""
   service_and_version = re.findall(' \w+-\d+\.\d+\.\d+-RC',latest_tag)
   for match in service_and_version:
       found_version = re.search('\d+\.\d+\.\d+-\w+',service_and_version).group()
       service_name = re.search('\w+(?=-)',service_and_version).group()
       if service_name == service:
           version = found_version

def get_service_variables(service_name, default_tag="default"):

    global vcs_type
    vcs_type = get_vcs_type()
#    config = "docker_dev"
    key_location = "~/scribe/Scribe-Dev.pem"
    registry = "artifactory-pit.mmodal-npd.com/mmodal"
    branch = get_branch().lower()
    version, is_versioned = get_version(service_name, default_tag, branch)
    user,server = get_dev_server()
    container = service_name 
    repo = registry + "/ffs/" + service_name
    image_tar_name = service_name + "-latest-build.tar"
    root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    image_tar_file = root + "/" + image_tar_name
    image_id_file = root + "/" + service_name + ".latest.build.id"
    branch_id = get_branch_id()
    build_number = "";
    try:
        build_number = os.environ['BUILD_NUMBER'].strip();
    except KeyError:
        print("No environment variable detected for Build Number, using default of 99 instead")
        build_number = 99;
    unique_tag = "build-{0}-{1}-{2}".format(branch, branch_id, build_number)
#    network = get_network(config, config_path)
#    volume = get_volume(config, config_path) 
#    flags = get_from_config_file(config_path, config, "flags")
    
    service_variables = dict(locals())
    return service_variables
