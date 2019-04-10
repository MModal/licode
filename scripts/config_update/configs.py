import boto3
import base64
from botocore.exceptions import ClientError
import json
import sys


def get_secret(secret_name):

    region_name = "us-east-1"

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

if __name__ == '__main__':
    secret_name = sys.argv[0] 
    print("Will read the secrets from {0}".format(secret_name))
    secrets = get_secret(secret_name)
    with open('../licode_default_custom.js', 'U') as input_file:
        config = input_file.read()
        config = config.replace('_rabbit_url_', secrets['rabbit_url'])
        config = config.replace('_superservice_id_', secrets['superservice_id'])
        config = config.replace('_superservice_key_', secrets['superservice_key'])
        config = config.replace('_ice_servers_', secrets['ice_servers'])
    with open('../licode_config.js', 'w') as output_file:
        output_file.write(config)
    
        