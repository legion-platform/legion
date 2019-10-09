#
#    Copyright 2019 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import base64
import logging
import re
import typing
from typing import NamedTuple

from boto3 import session
from botocore.exceptions import ClientError
from legion.sdk.models import ConnectionSpec

# Find the regular expression here https://github.com/awslabs/amazon-ecr-credential-helper/blob/c689f646af7fc73f3e4cea0a8dd4671eeeb6884e/ecr-login/api/client.go#L34  # pylint: disable=C0301
ECR_URL = re.compile(
    r'(^[a-zA-Z0-9][a-zA-Z0-9-_]*)\.dkr\.ecr(\-fips)?\.([a-zA-Z0-9][a-zA-Z0-9-_]*)\.amazonaws\.com(\.cn)?\/?(.*):.*$')
ECR_CONNECTION_TYPE = 'ecr'


class ECRRegistry(NamedTuple):
    id: str
    repository_name: str


def get_ecr_credentials(conn_spec: ConnectionSpec, image_docker_url: str) -> typing.Tuple[str, str]:
    """
    The function generates docker credentials for the ECR registry.
    It creates a repository for an image if there is not it.
    :param conn_spec: Connection Spec
    :param image_docker_url: full docker image URI
    :return:
    """
    if conn_spec.type != ECR_CONNECTION_TYPE:
        raise ValueError(f'Unexpected connection type: {conn_spec.type}')

    ecr_client = session.Session(
        aws_access_key_id=conn_spec.key_id,
        aws_secret_access_key=conn_spec.key_secret,
        region_name=conn_spec.region).client('ecr')

    ecr_registry = extract_repository_from_ecr_url(image_docker_url)

    try:
        ecr_client.create_repository(repositoryName=ecr_registry.repository_name,
                                     imageTagMutability='MUTABLE')

        logging.info(f'Repository {ecr_registry.repository_name} was created')
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryAlreadyExistsException':
            logging.info(f'Repository {ecr_registry.repository_name} has already existed')
        else:
            raise e

    response = ecr_client.get_authorization_token(registryIds=[ecr_registry.id])
    token = response["authorizationData"][0]["authorizationToken"]

    return base64.b64decode(token).decode().split(':')


def extract_repository_from_ecr_url(image_url: str) -> ECRRegistry:
    """
    Retrieve repository information from ecr URL
    :param image_url: full docker image URI
    :return: repository information
    """
    match = ECR_URL.search(image_url)
    if match is None:
        raise ValueError(f'{image_url} is invalid ecr image')

    groups = match.groups()

    if len(groups) != 5:
        raise ValueError(f'{image_url} is not a valid repository URI for Amazon Elastic Container Registry.')

    return ECRRegistry(id=groups[0], repository_name=groups[4])
