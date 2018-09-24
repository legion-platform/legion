#
#    Copyright 2017 EPAM Systems
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
legion k8s functions
"""
import logging
import os
import json

import docker
import docker.errors

import legion
import legion.model
import legion.pymodel
import legion.config
import legion.containers.headers
import legion.utils

LOGGER = logging.getLogger(__name__)


def build_docker_client(args=None):
    """
    Create docker client

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace` or None
    :return: :py:class:`docker.Client`
    """
    client = docker.from_env()
    return client


def get_docker_container_id_from_cgroup_line(line):
    """
    Get docker container id from proc cgroups line

    :argument line: line from /proc/<pid>/cgroup
    :type line: str
    :return: str -- container ID
    """
    parts = line.split('/')

    try:
        if 'docker' in parts:
            docker_pos = parts.index('docker')
            return parts[docker_pos + 1]
        elif 'kubepods' in parts:
            kubepods_pos = parts.index('kubepods')
            return parts[kubepods_pos + 3]
        else:
            raise Exception('Cannot find docker or kubepods tag in cgroups')
    except Exception as container_detection_error:
        raise Exception('Cannot find container ID in line {}: {}'.format(line, container_detection_error))


def get_current_docker_container_id():
    """
    Get ID of current docker container using proc cgroups

    :return: str -- current container id
    """
    with open('/proc/self/cgroup') as f:
        lines = [line.strip('\n') for line in f]
        longest_line = max(lines, key=len)
        return get_docker_container_id_from_cgroup_line(longest_line)


def commit_image(client, container_id=None):
    """
    Commit container and return image sha commit id

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param container_id: (Optional) id of target container. Current if None
    :type container_id: str
    :return: str -- docker image id
    """
    if not container_id:
        container_id = get_current_docker_container_id()

    container = client.containers.get(container_id)
    image = container.commit()

    return image.id


def get_docker_log_line_content(log_line):
    """
    Get string from Docker log line object

    :param log_line: docker log line object
    :type log_line: str or dict
    :return: str -- log line
    """
    str_line = ''
    if isinstance(log_line, str):
        str_line = log_line
    elif isinstance(log_line, dict):
        if 'stream' in log_line and isinstance(log_line['stream'], str):
            str_line = log_line['stream']
        else:
            str_line = repr(log_line)

    return str_line.rstrip('\n')


def build_docker_image(client, model_id, model_file, labels,
                       docker_image_tag):
    """
    Build docker image from current image with addition files

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param model_id: model id
    :type model_id: str
    :param model_file: path to model file (in the temporary directory)
    :type model_file: str
    :param labels: image labels
    :type labels: dict[str, str]
    :param docker_image_tag: str docker image tag
    :type docker_image_tag: str ot None
    :return: docker.models.Image
    """
    with legion.utils.TemporaryFolder('legion-docker-build') as temp_directory:
        # Copy Jenkins workspace from mounted volume to persistent container directory
        target_workspace = '/app'
        target_model_file = os.path.join(target_workspace, model_id)

        try:
            LOGGER.info('Copying model binary from {!r} to {!r}'
                        .format(model_file, target_model_file))
            legion.utils.copy_file(model_file, target_model_file)
        except Exception as model_binary_copy_exception:
            LOGGER.exception('Unable to move model binary to persistent location',
                             exc_info=model_binary_copy_exception)
            raise

        try:
            workspace_path = os.getcwd()
            LOGGER.info('Copying model workspace from {!r} to {!r}'.format(workspace_path, target_workspace))
            legion.utils.copy_directory_contents(workspace_path, target_workspace)
        except Exception as model_workspace_copy_exception:
            LOGGER.exception('Unable to move model workspace to persistent location',
                             exc_info=model_workspace_copy_exception)
            raise

        # Copy additional files for docker build
        additional_directory = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            '..', 'templates', 'docker_files'
        ))
        legion.utils.copy_directory_contents(additional_directory, temp_directory.path)

        # ALL Filesystem modification below next line would be ignored
        captured_image_id = commit_image(client)
        LOGGER.info('Image {} has been captured'.format(captured_image_id))

        if workspace_path.count(os.path.sep) > 1:
            symlink_holder = os.path.abspath(os.path.join(workspace_path, os.path.pardir))
        else:
            symlink_holder = '/'

        # Remove old workspace (if exists), create path to old workspace's parent, create symlink
        symlink_create_command = 'rm -rf "{}" && mkdir -p "{}" && ln -s "{}" "{}"'.format(
            workspace_path,
            symlink_holder,
            target_workspace,
            workspace_path
        )

        print('Executing {!r}'.format(symlink_create_command))

        docker_file_content = legion.utils.render_template('Dockerfile.tmpl', {
            'MODEL_PORT': legion.config.LEGION_PORT[1],
            'DOCKER_BASE_IMAGE_ID': captured_image_id,
            'MODEL_ID': model_id,
            'MODEL_FILE': target_model_file,
            'CREATE_SYMLINK_COMMAND': symlink_create_command
        })

        labels = {k: str(v) if v else None
                  for (k, v) in labels.items()}

        with open(os.path.join(temp_directory.path, 'Dockerfile'), 'w') as file:
            file.write(docker_file_content)

        LOGGER.info('Building docker image in folder {}'.format(temp_directory.path))
        logs = None
        try:
            image, logs = client.images.build(
                tag=docker_image_tag,
                nocache=True,
                path=temp_directory.path,
                rm=True,
                labels=labels
            )
        except docker.errors.BuildError as build_error:
            LOGGER.error('Cannot build image: {}. Build logs: '.format(build_error))
            for log_line in build_error.build_log:
                LOGGER.error(get_docker_log_line_content(log_line))
            raise

        return image


def generate_docker_labels_for_image(model_file, model_id, args):
    """
    Generate docker image labels from model file

    :param model_file: path to model file
    :type model_file: str
    :param model_id: model id
    :type model_id: str
    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: dict[str, str] of labels
    """
    container = legion.pymodel.Model.load(model_file)

    base = {
        legion.containers.headers.DOMAIN_MODEL_ID: model_id,
        legion.containers.headers.DOMAIN_MODEL_VERSION: container.model_version,
        legion.containers.headers.DOMAIN_CLASS: 'pyserve',
        legion.containers.headers.DOMAIN_CONTAINER_TYPE: 'model',
        legion.containers.headers.DOMAIN_MODEL_PROPERTY_VALUES: container.properties.serialize_data_to_string()
    }

    for key, value in container.meta_information.items():
        if hasattr(value, '__iter__') and not isinstance(value, str):
            formatted_value = ', '.join(item for item in value)
        else:
            formatted_value = str(value)

        base[legion.containers.headers.DOMAIN_PREFIX + key] = formatted_value

    return base


def generate_docker_labels_for_container(image):
    """
    Build container labels from image labels (copy)

    :param image: source Docker image
    :type image: :py:class:`docker.models.image.Image`
    :return: dict[str, str] of labels
    """
    return image.labels


def push_image_to_registry(client, image, external_image_name):
    """
    Push docker image to registry

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param image: Docker image
    :type image: :py:class:`docker.models.images.Image`
    :param external_image_name: target Docker image name (with repository)
    :type external_image_name: str
    :return: None
    """
    docker_registry = external_image_name
    version = None

    registry_delimiter = docker_registry.find('/')
    if registry_delimiter < 0:
        raise Exception('Invalid registry format')

    registry = docker_registry[:registry_delimiter]
    image_name = docker_registry[registry_delimiter + 1:]

    version_delimiter = image_name.find(':')
    if version_delimiter > 0:
        version = image_name[version_delimiter + 1:]
        image_name = image_name[:version_delimiter]

    docker_registry_user = os.getenv(*legion.config.DOCKER_REGISTRY_USER)
    docker_registry_password = os.getenv(*legion.config.DOCKER_REGISTRY_PASSWORD)
    auth_config = None

    if docker_registry_user and docker_registry_password:
        auth_config = {
            'username': docker_registry_user,
            'password': docker_registry_password
        }

    image_and_registry = '{}/{}'.format(registry, image_name)

    image.tag(image_and_registry, version)
    LOGGER.info('Pushing {}:{} to {}'.format(image_and_registry, version, registry))

    client.images.push(image_and_registry, tag=version, auth_config=auth_config)
    LOGGER.info('Successfully pushed image {}:{}'.format(image_and_registry, version))

    image_with_version = '{}/{}:{}'.format(registry, image_name, version)
    legion.utils.send_header_to_stderr(legion.containers.headers.IMAGE_TAG_EXTERNAL, image_with_version)
