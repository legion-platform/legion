"""
Deploy logic for DRun
"""

import os
import tempfile
import shutil
import logging

import docker
from jinja2 import Environment, PackageLoader, select_autoescape

LOGGER = logging.getLogger('deploy')


# TODO Model version info must be embedded to image
def build_docker_image(baseimage, model_id, model_file, labels):
    """
    Build docker image from base image and model file
    :param baseimage: name of base image
    :param model_id: model id
    :param model_file: path to model file
    :param labels: dict of image labels
    :return: docker.models.Image
    """
    tmpdir = tempfile.mkdtemp('legion-docker-build')

    (folder, model_filename) = os.path.split(model_file)

    shutil.copy2(model_file, os.path.join(tmpdir, model_filename))

    env = Environment(
        loader=PackageLoader(__name__, 'templates'),
        autoescape=select_autoescape(['tmpl'])
    )

    template = env.get_template('Dockerfile.tmpl')

    with open(os.path.join(tmpdir, 'Dockerfile'), 'w') as file:
        file.write(template.render({
            'DOCKER_BASE_IMAGE': baseimage,
            'MODEL_ID': model_id,
            'MODEL_FILE': model_filename
        }))

    client = docker.from_env()
    image = client.images.build(
        nocache=True,
        path=tmpdir,
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

    return network_id


def deploy_model(args):
    """
    Deploy model to docker host
    :param args: args with .model_id, .model_file, .docker_network
    :return: docker.model.Container new instance
    """
    client = docker.from_env()

    labels = {
        "com.epam.drun.model_id": args.model_id,
        "com.epam.drun.model_version": "TODO",
        "com.epam.drun.class": "pyserve"
    }

    image = build_docker_image(
        'drun/base-python-image:latest',
        args.model_id,
        args.model_file,
        labels
    )
    LOGGER.info('Built image: %s', image)

    network_id = find_network(client, args)

    LOGGER.info('Starting container')
    container = client.containers.run(image,
                                      network=network_id,
                                      stdout=True,
                                      stderr=True,
                                      detach=True,
                                      labels=labels)
    print(container)
    return container


# TODO Model undeploy
def undeploy_model(args):
    """
    Undeploy model from Docker Host
    :param args: arguments
    :return: None
    """
    return
