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
DRun k8s functions
"""
import logging
import os
import shutil

import drun
import drun.const.env
import drun.const.headers
import drun.model.io
import drun.utils

import docker
import docker.errors


LOGGER = logging.getLogger('docker')
VALID_SERVING_WORKERS = 'uwsgi', 'gunicorn'


def build_docker_client(args):
    """
    Create docker client

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.Client`
    """
    client = docker.from_env()
    return client


def build_docker_image(client, base_image, model_id, model_file, labels, python_package, docker_image_tag, serving):
    """
    Build docker image from base image and model file

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param base_image: name of base image
    :type base_image: str
    :param model_id: model id
    :type model_id: str
    :param model_file: path to model file
    :type model_file: str
    :param labels: image labels
    :type labels: dict[str, str]
    :param python_package: path to wheel or None for install from PIP
    :type python_package: str or None
    :param docker_image_tag: str docker image tag
    :type docker_image_tag: str ot None
    :param serving: serving worker, one of VALID_SERVING_WORKERS
    :type serving: str
    :return: docker.models.Image
    """
    with drun.utils.TemporaryFolder('legion-docker-build') as temp_directory:
        folder, model_filename = os.path.split(model_file)

        shutil.copy2(model_file, os.path.join(temp_directory.path, model_filename))

        install_target = 'drun'

        if python_package:
            if not os.path.exists(python_package):
                raise Exception('Python package file not found: %s' % python_package)

            install_target = os.path.basename(python_package)
            shutil.copy2(python_package, os.path.join(temp_directory.path, install_target))

        if serving not in VALID_SERVING_WORKERS:
            raise Exception('Unknown serving parameter. Should be one of %s' % (', '.join(VALID_SERVING_WORKERS), ))

        # Copy additional payload from templates / docker_files / <serving>
        additional_directory = os.path.join(
            os.path.dirname(__file__), '..', 'utils', 'templates', 'docker_files', serving)

        for file in os.listdir(additional_directory):
            path = os.path.join(additional_directory, file)
            if os.path.isfile(path) and file != 'Dockerfile':
                shutil.copy2(path, os.path.join(temp_directory.path, file))

        additional_docker_file = os.path.join(additional_directory, 'Dockerfile')
        with open(additional_docker_file, 'r') as additional_docker_file_stream:
            additional_docker_file_content = additional_docker_file_stream.read()

        docker_file_content = drun.utils.render_template('Dockerfile.tmpl', {
            'ADDITIONAL_DOCKER_CONTENT': additional_docker_file_content,
            'DOCKER_BASE_IMAGE': base_image,
            'MODEL_ID': model_id,
            'MODEL_FILE': model_filename,
            'PIP_INSTALL_TARGET': install_target,
            'PIP_CUSTOM_TARGET': install_target != 'drun'
        })

        labels = {k: str(v) if v else None for (k, v) in labels.items()}

        with open(os.path.join(temp_directory.path, 'Dockerfile'), 'w') as file:
            file.write(docker_file_content)

        LOGGER.info('Building docker image in folder %s' % (temp_directory.path))
        try:
            image = client.images.build(
                tag=docker_image_tag,
                nocache=True,
                path=temp_directory.path,
                rm=True,
                labels=labels
            )
        except docker.errors.BuildError as build_error:
            LOGGER.error('Cannot build image: %s' % (build_error))
            raise build_error

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
    with drun.model.io.ModelContainer(model_file, do_not_load_model=True) as container:
        base = {
            'com.epam.drun.model.id': model_id,
            'com.epam.drun.model.version': container.get('model.version', 'undefined'),
            'com.epam.drun.class': 'pyserve',
            'com.epam.drun.container_type': 'model'
        }
        for key, value in container.items():
            base['com.epam.' + key] = value

        return base


def generate_docker_labels_for_container(image):
    """
    Build container labels from image labels (copy)

    :param image: source Docker image
    :type image: :py:class:`docker.models.image.Image`
    :return: dict[str, str] of labels
    """
    return image.labels


def find_network(client, args):
    """
    Find DRun network on docker host

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: str id of network
    """
    network_id = args.docker_network

    if network_id is None:
        LOGGER.debug('No network provided, trying to detect an active DRun network')
        nets = client.networks.list()
        for network in nets:
            name = network.name
            if name.startswith('drun'):
                LOGGER.info('Detected network %s', name)
                network_id = network.id
                break
    else:
        if network_id not in client.networks.list():
            network_id = None

    if not network_id:
        LOGGER.error('Using empty docker network')

    return network_id


def get_stack_containers_and_images(client, network_id):
    """
    Get information about DRun containers and images

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param network_id: docker network
    :type network_id: str
    :return: dict with lists 'services', 'models' and 'model_images'
    """
    containers = client.containers.list(True)
    containers = [c
                  for c in containers
                  if 'com.epam.drun.container_type' in c.labels
                  and (not network_id
                       or network_id in (n['NetworkID'] for n in c.attrs['NetworkSettings']['Networks'].values()))]

    images = client.images.list(filters={'label': 'com.epam.drun.container_type'})

    return {
        'services': [c for c in containers if c.labels['com.epam.drun.container_type'] == 'service'],
        'models': [c for c in containers if c.labels['com.epam.drun.container_type'] == 'model'],
        'model_images': [i for i in images if i.labels['com.epam.drun.container_type'] == 'model'],
    }
