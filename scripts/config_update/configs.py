import boto3
import base64
from botocore.exceptions import ClientError
import json
import sys
import argparse
import requests


def get_secret(secret_name, region_name):

#    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(e)
    else:
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret", help="Secret name")
    parser.add_argument("--region", help="AWS resion name")
    parser.add_argument("--service", help="Type of service")
    parser.add_argument("--serialnum", type=int, help="Serial number of the service")
    parser.add_argument("--database", help="Mongo secret name")
    parser.add_argument("--usePublicIP", help="Controller should use public IP, use when outside of us-east-1", action='store_true')
    parser.add_argument("--ssl", help="Run the web frontend over SSL", action='store_true')
    
    args = parser.parse_args()
    if args.secret is None:
        parser.error("Secret is required")
    if args.service is None:
        parser.error("Service is required")
    if args.region is None:
        parser.error("Region is required")

    return args


if __name__ == '__main__':
    args = parse_arguments()
    print("Will read the secrets from {0} in {1}".format(args.secret, args.region))
    secrets = get_secret(args.secret, args.region)
    with open('../licode_default_custom.js', 'U') as input_file:
        config = input_file.read()
        config = config.replace('_rabbit_url_', secrets['rabbit_url'])
        config = config.replace('_superservice_id_', secrets['superservice_id'])
        config = config.replace('_superservice_key_', secrets['superservice_key'])
        if args.service == 'controller':
            config = config.replace('_cloud_provider_', '')
            config = config.replace('_nuve_ssl_', 'false')
            if 'stun_servers' in secrets or 'turn_servers' in secrets:
                ice_servers = []
                if 'stun_servers' in secrets:
                    stun_servers = json.loads(secrets['stun_servers'])
                    if args.serialnum is not None and len(stun_servers) >= args.serialnum:
                        ice_servers.append(stun_servers.pop(args.serialnum))
                    ice_servers.extend(stun_servers)
                if 'turn_servers' in secrets:
                    turn_servers_str = secrets['turn_servers']
                    if 'coturn_user' in secrets:
                        turn_servers_str = turn_servers_str.replace('_turn_user_', secrets['coturn_user'])
                    if 'coturn_password' in secrets:
                        turn_servers_str = turn_servers_str.replace('_turn_password_', secrets['coturn_password'])
                    turn_servers = json.loads(turn_servers_str)
                    if args.serialnum is not None and len(turn_servers) >= args.serialnum:
                        ice_servers.extend(turn_servers.pop(args.serialnum))
                    for turn_server in turn_servers:
                        ice_servers.extend(turn_server)
                config = config.replace('_ice_servers_', json.dumps(ice_servers))
            else:
                config = config.replace('_ice_servers_', secrets['ice_servers'])
            if args.usePublicIP:
                public_ip_resp = requests.get("http://169.254.169.254/latest/meta-data/public-ipv4")
                print("Will use {0} as the public IP".format(public_ip_resp.text))
                config = config.replace('_controller_public_ip_', public_ip_resp.text)
            else:
                config = config.replace('_controller_public_ip_', '')
        elif args.service == 'agent':
            if 'cloud_provider' in secrets:
                config = config.replace('_cloud_provider_', secrets['cloud_provider'])
            else:
                config = config.replace('_cloud_provider_', '')
            config = config.replace('_ice_servers_', '{}')
            config = config.replace('_controller_public_ip_', '')
            config = config.replace('_nuve_ssl_', 'false')
        elif args.service == 'nuve':
            config = config.replace('_cloud_provider_', '')
            config = config.replace('_ice_servers_', '{}')
            config = config.replace('_controller_public_ip_', '')
            databaseSecret = get_secret(args.database, args.region)
            if 'username' in databaseSecret:
                config = config.replace('_mongo_connection_', '{}:{}@{}/nuvedb'.format(databaseSecret['username'], databaseSecret['password'], databaseSecret['host']))
            else:
                config = config.replace('_mongo_connection_', '{}/nuvedb'.format(databaseSecret['host']))
            if databaseSecret['ssl'] == 'true':
                config = config.replace('_database_ssl_cert_', './../rds-combined-ca-bundle.pem')
            else:
                config = config.replace('_database_ssl_cert_', '')
            if args.ssl:
                config = config.replace('_nuve_ssl_', 'true')
            else:
                config = config.replace('_nuve_ssl_', 'false')
    with open('../../licode_config.js', 'w') as output_file:
        output_file.write(config)
