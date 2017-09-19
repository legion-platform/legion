import os
import tempfile
import docker
import shutil
import logging
from jinja2 import Environment, PackageLoader, select_autoescape

logger = logging.getLogger('deploy')


# TODO Model version info must be embedded to image
def build_docker_image(baseimage, model_id, model_file, labels):
    tmpdir = tempfile.mkdtemp('legion-docker-build')

    (folder, model_filename) = os.path.split(model_file)

    shutil.copy2(model_file, os.path.join(tmpdir, model_filename))

    env = Environment(
        loader=PackageLoader(__name__, 'templates'),
        autoescape=select_autoescape(['tmpl'])
    )

    template = env.get_template('Dockerfile.tmpl')

    with open(os.path.join(tmpdir, 'Dockerfile'), 'w') as f:
        f.write(template.render({
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
    network_id = args.docker_network

    if network_id is None:
        logger.debug('No network provided, trying to detect an active DRun network')
        nets = client.networks.list()
        for n in nets:
            name = n.name
            if name.startswith('drun'):
                logger.info('Detected network %s', name)
                network_id = n.id
                break

    return network_id


def deploy_model(args):
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
    logger.info('Built image: %s', image)

    network_id = find_network(client, args)

    logger.info('Starting container')
    container = client.containers.run(image,
                          network=network_id,
                          stdout=True,
                          stderr=True,
                          detach=True,
                          labels=labels)
    print(container)
    return container


def undeploy_model(args):
    return
