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
"""
Docker image builder
"""
import json
import logging
import os
import typing

import docker
from legion.packager.rest.extensions.ecr import ECR_CONNECTION_TYPE, get_ecr_credentials
from legion.packager.rest.io_proc_utils import run
from legion.sdk.models import Connection

BUILDAH_BIN = os.getenv('BUILDAH_BIN', 'buildah')
LOGGER = logging.getLogger(__name__)


def extract_docker_login_credentials(
        connection: Connection,
        docker_image_url: typing.Optional[str] = None) -> typing.Tuple[str, str, str]:
    """
    Extract docker login credentials from connection

    :param docker_image_url:
    :param connection: connection
    :return: registry, login, password
    """
    if connection.spec.type == ECR_CONNECTION_TYPE and docker_image_url:
        user, password = get_ecr_credentials(connection.spec, docker_image_url)

        return connection.spec.uri, user, password

    return connection.spec.uri, connection.spec.username, connection.spec.password


def test_is_buildah_available():
    """
    Check is buildah is available

    :return: bool -- is buildah available
    """
    try:
        run(BUILDAH_BIN, '--version')
        logging.info('buildah is detected')
        return True
    except Exception:
        logging.info('buildah is not detected')
        return False


def _extract_buildah_credentials(connection: typing.Optional[Connection] = None,
                                 docker_image_url: typing.Optional[str] = None) -> typing.List[str]:
    """
    Extract argument for buildah

    :param connection: connection
    :return: typing.List[str]
    """
    if not connection:
        return []

    _, login, password = extract_docker_login_credentials(connection, docker_image_url)

    logging.info('Using password %r for user %r',
                 '*' * len(password), login)

    return [
        '--creds',
        f'{login}:{password}'
    ]


def build_docker_image_buildah(context,
                               docker_file,
                               external_docker_name,
                               push_connection: Connection,
                               pull_connection: typing.Optional[Connection] = None):
    """
    Build and push docker image

    :param context: docker build context
    :param docker_file: Dockerfile name (relative to docker build context)
    :param external_docker_name: external docker image target name, without host
    :param push_connection: connection for pushing Docker images to
    :param pull_connection: (Optional) connection for pulling Docker image during build from
    :return: None
    """
    remote_tag = f'{push_connection.spec.uri}/{external_docker_name}'

    logging.info('Starting building of new image')
    build_args = [
        BUILDAH_BIN, 'build-using-dockerfile',
        *_extract_buildah_credentials(pull_connection),
        '--file', docker_file,
        '--format', 'docker',
        '--compress',
        '--tag', remote_tag,
        context
    ]
    run(*build_args)

    logging.info('Starting pushing of image')
    push_args = [
        BUILDAH_BIN, 'push',
        *_extract_buildah_credentials(push_connection, remote_tag),
        remote_tag
    ]
    run(*push_args)


def _authorize_docker(client: docker.DockerClient, connection: Connection):
    """
    Authorize docker api on external registry

    :param client: docker API
    :type client: docker.DockerClient
    :param connection: connection credentials
    :return: None
    """
    registry, login, password = extract_docker_login_credentials(connection)

    logging.info('Trying to authorize %r on %r using password %r',
                 login, registry,
                 '*' * len(connection.spec.password))
    client.login(username=login,
                 password=password,
                 registry=registry,
                 reauth=True)


def build_docker_image_docker(context,
                              docker_file,
                              external_docker_name,
                              push_connection: Connection,
                              pull_connection: typing.Optional[Connection] = None):
    """
    Build and push docker image

    :param context: docker build context
    :param docker_file: Dockerfile name (relative to docker build context)
    :param external_docker_name: external docker image target name, without host
    :param push_connection: connection for pushing Docker images to
    :param pull_connection: (Optional) connection for pulling Docker image during build from
    :return:
    """
    logging.debug('Building docker client from ENV variables')
    client = docker.from_env()
    # Authorize for pull
    if pull_connection:
        logging.debug('Trying to authorize user fo pulling sources')
        _authorize_docker(client, pull_connection)

    # Build image
    streamer = client.api.build(path=context,
                                rm=True,
                                dockerfile=docker_file,
                                tag=external_docker_name)

    for chunk in streamer:
        if isinstance(chunk, bytes):
            chunk = chunk.decode('utf-8')

        try:
            chunk_json = json.loads(chunk)

            if 'stream' in chunk_json:
                for line in chunk_json['stream'].splitlines():
                    LOGGER.info(line.strip())

        except json.JSONDecodeError:
            LOGGER.info(chunk)

    # Tag for pushing
    remote_tag = f'{push_connection.spec.uri}/{external_docker_name}'
    local_built = client.images.get(external_docker_name)
    local_built.tag(remote_tag)

    # Push
    log_generator = client.images.push(repository=remote_tag,
                                       stream=True,
                                       auth_config={
                                           'username': push_connection.spec.username,
                                           'password': push_connection.spec.password
                                       })

    for line in log_generator:
        if isinstance(line, bytes):
            line = line.decode('utf-8')
        LOGGER.info(line)

    client.images.remove(remote_tag)
    client.images.remove(external_docker_name)


def build_docker_image(context,
                       docker_file,
                       external_docker_name,
                       push_connection: Connection,
                       pull_connection: typing.Optional[Connection] = None):
    """
    Build and push docker image

    :param context: docker build context (folder name)
    :type context: str
    :param docker_file: Dockerfile name (relative to docker build context)
    :type docker_file: str
    :param external_docker_name: external docker image target name, without host
    :type external_docker_name: str
    :param push_connection: connection for pushing Docker images to
    :param pull_connection: (Optional) connection for pulling Docker image during build from
    :type pull_connection: typing.Optional[PackagingResourceConnection]
    :return: None
    """
    if test_is_buildah_available():
        build_docker_image_buildah(context, docker_file, external_docker_name, push_connection, pull_connection)
    else:
        build_docker_image_docker(context, docker_file, external_docker_name, push_connection, pull_connection)
