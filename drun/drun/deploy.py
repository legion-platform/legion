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
Deploy logic for DRun
"""

import os
import shutil
import logging

import drun.utils
from drun.utils import Colors
import drun.io
import drun.grafana

import docker
from jinja2 import Environment, PackageLoader, select_autoescape

LOGGER = logging.getLogger('deploy')


def generate_docker_labels_for_image(model_file, args):
    """
    Generate docker image labels from model file
    :param model_file: str path to model file
    :param args: command arguments
    :return: dict of labels str => str
    """
    with drun.io.ModelContainer(model_file, do_not_load_model=True) as container:
        base = {
            'com.epam.drun.model.id': args.model_id,
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
    :param image: docker.models.image.Image
    :return: dict of labels str => str
    """
    return image.labels


def build_docker_image(client, base_image, model_id, model_file, labels, python_package, docker_image_tag):
    """
    Build docker image from base image and model file
    :param client: docker client
    :param base_image: name of base image
    :param model_id: model id
    :param model_file: path to model file
    :param labels: dict of image labels
    :param python_package: str path to wheel or None for install from PIP
    :param docker_image_tag: str docker image tag
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

        env = Environment(
            loader=PackageLoader(__name__, 'templates'),
            autoescape=select_autoescape(['tmpl'])
        )

        template = env.get_template('Dockerfile.tmpl')

        with open(os.path.join(temp_directory.path, 'Dockerfile'), 'w') as file:
            file.write(template.render({
                'DOCKER_BASE_IMAGE': base_image,
                'MODEL_ID': model_id,
                'MODEL_FILE': model_filename,
                'PIP_INSTALL_TARGET': install_target,
                'PIP_CUSTOM_TARGET': install_target != 'drun'
            }))

        LOGGER.info('Building docker image in folder %s' % (temp_directory.path))
        image = client.images.build(
            tag=docker_image_tag,
            nocache=True,
            path=temp_directory.path,
            rm=True,
            labels=labels
        )

        return image


def find_network(client, args):
    """
    Find DRun network on docker host
    :param client: docker.client
    :param args: args with .docker_network item
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


def build_docker_client(args):
    """
    Create docker client
    :param args: args
    :return: docker.Client
    """
    client = docker.from_env()
    return client


def build_grafana_client(args):
    """
    Build Grafana client from ENV and from command line arguments
    :param args: arguments
    :return: drun.grafana
    """
    host = os.environ.get('GRAFANA_URL', 'http://grafana:3000/')
    user = os.environ.get('GRAFANA_USER', 'admin')
    password = os.environ.get('GRAFANA_PASSWORD', 'admin')

    if args.grafana_server:
        host = args.grafana_server

    if args.grafana_user and len(args.grafana_user):
        user = args.grafana_user

    if args.grafana_password and len(args.grafana_password):
        password = args.grafana_password

    LOGGER.info('Creating Grafana client for host: %s, user: %s, password: %s' % (host, user, '*' * len(password)))
    client = drun.grafana.GrafanaClient(host, user, password)

    return client


def build_model(args):
    """
    Build model
    :param args:
    :return: docker.Image
    """
    client = build_docker_client(args)

    if not os.path.exists(args.model_file):
        raise Exception('Cannot find model file: %s' % args.model_file)

    image_labels = generate_docker_labels_for_image(args.model_file, args)

    base_docker_image = args.base_docker_image
    if not base_docker_image:
        base_docker_image = 'drun/base-python-image:latest'

    image = build_docker_image(
        client,
        base_docker_image,
        args.model_id,
        args.model_file,
        image_labels,
        args.python_package,
        args.docker_image_tag
    )

    LOGGER.info('Built image: %s with python package: %s' % (image, args.python_package))

    print('Successfully created docker image %s for model %s' % (image.short_id, args.model_id))
    return image


def deploy_model(args):
    """
    Deploy model to docker host
    :param args: args with .model_id, .model_file, .docker_network
    :return: docker.model.Container new instance
    """
    client = build_docker_client(args)
    network_id = find_network(client, args)
    grafana_client = build_grafana_client(args)

    if args.model_id and args.docker_image:
        print('Use only --model-id or --docker-image')
        exit(1)
    elif not args.model_id and not args.docker_image:
        print('Use with --model-id or --docker-image')
        exit(1)

    current_containers = get_stack_containers_and_images(client, network_id)

    if args.model_id:
        for image in current_containers['model_images']:
            model_name = image.labels.get('com.epam.drun.model.id', None)
            if model_name == args.model_id:
                image = image
                model_id = model_name
                break
        else:
            raise Exception('Cannot found image for model_id = %s' % (args.model_id,))
    elif args.docker_image:
        image = client.images.get(args.docker_image)
        model_id = image.labels.get('com.epam.drun.model.id', None)
        if not model_id:
            raise Exception('Cannot detect model_id in image')
    else:
        raise Exception('Provide model-id or docker-image')

    # Detect current existing containers with models, stop and remove them
    LOGGER.info('Founding containers with model_id=%s' % model_id)

    for container in current_containers['models']:
        model_name = container.labels.get('com.epam.drun.model.id', None)
        if model_name == model_id:
            LOGGER.info('Stopping container #%s' % container.short_id)
            container.stop()
            LOGGER.info('Removing container #%s' % container.short_id)
            container.remove()

    container_labels = generate_docker_labels_for_container(image)

    LOGGER.info('Starting container with image #%s for model %s' % (image.short_id, model_id))
    container = client.containers.run(image,
                                      network=network_id,
                                      stdout=True,
                                      stderr=True,
                                      detach=True,
                                      labels=container_labels)

    LOGGER.info('Creating Grafana dashboard for model %s' % (model_id, ))
    grafana_client.create_dashboard_for_model_by_labels(container_labels)

    print('Successfully created docker container %s for model %s' % (container.short_id, model_id))
    return container


def undeploy_model(args):
    """
    Undeploy model from Docker Host
    :param args: arguments
    :return: None
    """
    client = build_docker_client(args)
    network_id = find_network(client, args)
    grafana_client = build_grafana_client(args)

    current_containers = get_stack_containers_and_images(client, network_id)

    for container in current_containers['models']:
        model_name = container.labels.get('com.epam.drun.model.id', None)
        if model_name == args.model_id:
            target_container = container
            break
    else:
        raise Exception('Cannot found container for model_id = %s' % (args.model_id,))

    LOGGER.info('Stopping container #%s' % target_container.short_id)
    target_container.stop()
    LOGGER.info('Removing container #%s' % target_container.short_id)
    target_container.remove()
    LOGGER.info('Removing Grafana dashboard for model %s' % (args.model_id, ))
    grafana_client.remove_dashboard_for_model(args.model_id)

    print('Successfully undeployed model %s' % (args.model_id, ))


def get_stack_containers_and_images(client, network_id):
    """
    Get information about DRun containers and images
    :param client: docker.Client client
    :param network_id: docker network
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


def inspect(args):
    """
    Print information about current containers / images state
    :param args: arguments
    :return: None
    """
    client = build_docker_client(args)
    network_id = find_network(client, args)
    containers = get_stack_containers_and_images(client, network_id)

    all_required_containers_is_ok = True

    print('%sServices:%s' % (Colors.BOLD, Colors.ENDC))
    for container in containers['services']:
        is_running = container.status == 'running'
        container_name = container.labels.get('com.epam.drun.container_description', container.image.tags[0])
        container_required = container.labels.get('com.epam.drun.container_required', 'true').lower()
        container_required = container_required in ('1', 'yes', 'true')
        container_status = container.status

        if is_running:
            line_color = Colors.OKGREEN
        elif container_required:
            line_color = Colors.FAIL
            all_required_containers_is_ok = False
        else:
            line_color = Colors.WARNING

        if container.status == 'exited':
            exit_code = container.attrs['State']['ExitCode']
            container_status = 'exited with code %d' % (exit_code,)
        elif container.status == 'running':
            ports = list(container.attrs['NetworkSettings']['Ports'].values())
            ports = [item['HostPort'] for sublist in ports if sublist for item in sublist if item]

            if ports:
                container_status = 'running on ports: %s' % (', '.join(ports),)
        print('%s*%s %s #%s - %s%s%s' % (line_color, Colors.ENDC,
                                         container_name, container.short_id,
                                         line_color, container_status, Colors.ENDC))

    if not containers['services']:
        all_required_containers_is_ok = False
        print('%s-- looks like DRun stack hasn\'t been deployed --%s' % (Colors.FAIL, Colors.ENDC))

    print('%sModel instances:%s' % (Colors.BOLD, Colors.ENDC))
    for container in containers['models']:
        is_running = container.status == 'running'
        line_color = Colors.OKGREEN if is_running else Colors.FAIL
        container_status = '%s #%s' % (container.status, container.short_id)

        model_name = container.labels.get('com.epam.drun.model.id', 'Undefined model ' + ','.join(container.image.tags))
        model_image_id = container.image.short_id
        model_version = container.labels.get('com.epam.drun.model.version', '?')

        print('%s*%s %s%s%s #%s (version: %s) - %s%s%s' % (line_color, Colors.ENDC,
                                                           Colors.UNDERLINE, model_name, Colors.ENDC,
                                                           model_image_id, model_version,
                                                           line_color, container_status, Colors.ENDC))

    if not containers['models']:
        print('%s-- cannot find any model instances --%s' % (Colors.WARNING, Colors.ENDC))

    print('%sModel images:%s' % (Colors.BOLD, Colors.ENDC))
    for image in containers['model_images']:
        model_name = image.labels.get('com.epam.drun.model.id', 'Undefined model')
        model_image_id = image.short_id
        model_version = image.labels.get('com.epam.drun.model.version', '?')
        print('* %s%s%s #%s (version: %s)' % (Colors.UNDERLINE, model_name, Colors.ENDC, model_image_id, model_version))

    if not containers['model_images']:
        print('%s-- cannot find any model images --%s' % (Colors.WARNING, Colors.ENDC))

    if not all_required_containers_is_ok:
        return 2
