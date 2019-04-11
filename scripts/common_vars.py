import os
import subprocess
import re
import json

VERSION_REGEX = '\d+\.\d+\.\d+'
RC_REGEX = '\d+\.\d+\.\d+-rc'


def get_vcs_type():
    try:
        subprocess.check_output(
            ["git", "status"],
            stderr=subprocess.STDOUT,
            shell=False
        )
        return "git"
    except subprocess.CalledProcessError:

        try:
            subprocess.check_output(
                ["hg", "status"],
                stderr=subprocess.STDOUT,
                shell=False
            )
            return "hg"
        except subprocess.CalledProcessError:
            print("No valid VCS detected (Mercurial or Git).")
            raise


def get_dev_server():
    config_file = os.path.realpath(os.path.dirname(__file__)) + "/deploy_config_template.json"
    data = json.load(open(config_file))
    user = data["dev_server"]["user"]
    server = data["dev_server"]["server"]
    return user, server


def get_volume(config, config_file):
    data = json.load(open(config_file))
    data_config = data[config]
    if "cert_volume" in data_config:
        cert_volume = data_config["cert_volume"]
        return " -v /opt/licode/cert:{0}".format(cert_volume)
    else:
        return ""


def get_from_config_file(config_file, *config_keys):
    data = json.load(open(config_file))
    for key in config_keys:
        data = data[key]
    return data


def get_config_dict(config, config_file):
    try:
        data = json.load(open(config_file))
        return data[config]

    except (KeyError, IOError) as e:
        print("Could not find config docker_dev for this service.")
        return None


def get_flags(data_config):
    if not data_config:
        return ""
    else:
        try:
            flags = data_config["flags"]
        except KeyError:
            flags = ""

        return flags


def get_commands(data_config):
    if not data_config:
        return ""
    else:
        try:
            commands = data_config["commands"]
        except KeyError:
            commands = ""
        return commands


def get_branch_id(vcs_type):
    branch_id = ""
    if vcs_type == "hg":
        pipe = subprocess.Popen(
            ["hg", "id", "-i"],
            stdout=subprocess.PIPE
        )
        branch_id = pipe.stdout.read().replace('+', '')

    elif vcs_type == "git":
        pipe = subprocess.Popen(
            ["git", "log", "--pretty=format:'%h'", "-n", "1"],
            stdout=subprocess.PIPE
        )
        branch_id = pipe.stdout.read().replace("'", "")

    if not branch_id:
        raise IOError("Error, no branch id found for mercurial or git.")

    return branch_id.strip()


def get_branch(vcs_type):
    branch = ""

    if vcs_type == "hg":
        pipe = subprocess.Popen(
            ["hg", "branch"],
            stdout=subprocess.PIPE
        )
        branch = pipe.stdout.read().strip()

    elif vcs_type == "git":
        pipe = subprocess.Popen(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
        )
        branch = pipe.stdout.read().strip()
        if branch == "master":
            branch = "default"

    return branch


def get_version(branch):
    is_versioned = False
    if re.search(RC_REGEX, branch):
        version = re.search(RC_REGEX, branch).group()
    elif re.search(VERSION_REGEX, branch):
        version = re.search(VERSION_REGEX, branch).group()
        is_versioned = True
    else:
        version = branch
    return version, is_versioned


def get_service_variables(dockerfile_path, service_name):
    vcs_type = get_vcs_type()
    config = "docker_dev"
    key_location = "~/scribe/Scribe-Dev.pem"
    service_path = dockerfile_path.rsplit("/", 1)[0]
    registry = "artifactory-pit.mmodal-npd.com/mmodal"
    branch = get_branch(vcs_type).lower()
    version, is_versioned = get_version(branch)
    user, server = get_dev_server()
    container = service_name + "-" + version
    repo = registry + "/ffs/" + service_name
    root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    image_id_file = root + "/" + service_name + ".latest.build.id"
    branch_id = get_branch_id(vcs_type)
    build_number = ""
    try:
        build_number = os.environ['BUILD_NUMBER'].strip()
    except KeyError:
        print("No environment variable detected for Build Number, using default of 99 instead")
        build_number = 99
    try:
        run_tests_env = os.environ['RUN_TESTS'].strip()
        build_args = "--build-arg RUN_TESTS={}".format(run_tests_env)
    except KeyError:
        build_args = ""

    unique_tag = "build-{0}-{1}-{2}".format(branch, branch_id, build_number)
    image_tar_name = service_name + "-" + unique_tag + ".tar"
    image_tar_file = root + "/" + image_tar_name
    config_file = service_path + "/" + "config.json"
    config_dict = get_config_dict(config, config_file)
    flags = get_flags(config_dict)
    commands = get_commands(config_dict)
    service_variables = dict(locals())

    return service_variables
