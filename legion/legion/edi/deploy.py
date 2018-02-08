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
Deploy logic for legion
"""

import logging
import os
import time

import docker
import docker.errors
import legion.config
import legion.containers.docker
import legion.containers.headers
import legion.containers.k8s
import legion.external.edi
import legion.external.grafana
import legion.io
import legion.utils
from legion.utils import Colors, ExternalFileReader

LOGGER = logging.getLogger('deploy')
VALID_SERVING_WORKERS = legion.containers.docker.VALID_SERVING_WORKERS


def build_model(args):
    """
    Build model

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Image` docker image
    """
    client = legion.containers.docker.build_docker_client(args)

    with ExternalFileReader(args.model_file) as external_reader:
        if not os.path.exists(external_reader.path):
            raise Exception('Cannot find model file: %s' % external_reader.path)

        with legion.io.ModelContainer(external_reader.path, do_not_load_model=True) as container:
            model_id = container.get('model.id', None)
            if args.model_id:
                model_id = args.model_id

        if not model_id:
            raise Exception('Cannot get model id (not setted in container and not setted in arguments)')

        image_labels = legion.containers.docker.generate_docker_labels_for_image(external_reader.path, model_id, args)

        base_docker_image = args.base_docker_image
        if not base_docker_image:
            base_docker_image = 'legion/base-python-image:latest'

        print('Building docker image...')
        image = legion.containers.docker.build_docker_image(
            client,
            base_docker_image,
            model_id,
            external_reader.path,
            image_labels,
            args.python_package,
            args.python_package_version,
            args.python_repository,
            args.docker_image_tag,
            args.serving
        )

        LOGGER.info('Built image: %s with python package: %s', image, args.python_package)
        print('Built image: %s with python package: %s for model %s' % (image, args.python_package, model_id))

        if args.push_to_registry:
            external_image_name = args.push_to_registry
            docker_registry = external_image_name
            version = None

            registry_delimiter = docker_registry.find('/')
            if registry_delimiter < 0:
                raise Exception('Invalid registry format. Valid format: host:port/repository/image:tag')

            registry = docker_registry[:registry_delimiter]
            image_name = docker_registry[registry_delimiter+1:]

            version_delimiter = image_name.find(':')
            if version_delimiter > 0:
                version = image_name[version_delimiter+1:]
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

            print('Tagging image %s v %s for model %s as %s' % (image.short_id, version, model_id, image_and_registry))
            image.tag(image_and_registry, version)
            print('Pushing %s:%s to %s' % (image_and_registry, version, registry))
            client.images.push(image_and_registry, tag=version, auth_config=auth_config)
            print('Successfully pushed image %s:%s' % (image_and_registry, version))

        return image


def inspect_kubernetes(args):
    """
    Inspect kubernetes

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    model_deployments = edi_client.inspect()

    print('%sModel deployments:%s' % (Colors.BOLD, Colors.ENDC))

    for deployment in model_deployments:
        if deployment.status == 'ok' and deployment.model_api_ok:
            line_color = Colors.OKGREEN
        elif deployment.status == 'warning':
            line_color = Colors.WARNING
        else:
            line_color = Colors.FAIL

        errors = ''

        if not deployment.model_api_ok:
            errors = 'MODEL API DOES NOT RESPOND'

        if errors:
            errors = 'ERROR: {}'.format(errors)

        arguments = (
            line_color, Colors.ENDC,
            Colors.UNDERLINE, deployment.model, Colors.ENDC,
            deployment.image, deployment.version,
            line_color, deployment.ready_replicas, deployment.scale, errors,
            Colors.ENDC
        )
        print('%s*%s %s%s%s %s (version: %s) - %s%s / %d pods ready %s%s' % arguments)

    if not model_deployments:
        print('%s-- cannot find any model deployments --%s' % (Colors.WARNING, Colors.ENDC))


def undeploy_kubernetes(args):
    """
    Undeploy model to kubernetes

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    try:
        edi_client.undeploy(args.model_id, args.grace_period)
    except Exception as exception:
        if 'Cannot find deployment' in str(exception) and args.ignore_not_found:
            print('Cannot find deployment - ignoring')
            return
        else:
            raise exception

    while True:
        information = [info for info in edi_client.inspect() if info.model == args.model_id]

        if not information:
            break

        time.sleep(1)


def scale_kubernetes(args):
    """
    Scale model instances

    :param args: command arguments with .model_id, .namespace and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    edi_client.scale(args.model_id, args.scale)


def deploy_kubernetes(args):
    """
    Deploy kubernetes model

    :param args: command arguments with .model_id, .namespace and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    edi_client.deploy(args.image, args.scale, args.image_for_k8s)

    if not args.no_wait:
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > args.wait_timeout and args.wait_timeout != 0:
                break

            information = [info for info in edi_client.inspect() if info.image == args.image]

            if not information:
                raise Exception('Cannot found deployment with image = {}'.format(args.image))

            if len(information) > 1:
                raise Exception('Founded too many deployments with image = {}'.format(args.image))

            deployment = information[0]

            if deployment.ready_replicas >= deployment.scale and deployment.model_api_ok:
                break

            time.sleep(1)


def deploy_model(args):
    """
    Deploy model to docker host

    :param args: command arguments with .model_id, .model_file, .docker_network
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Container` new instance
    """
    client = legion.containers.docker.build_docker_client(args)
    network_id = legion.containers.docker.find_network(client, args)

    if args.model_id and args.docker_image:
        print('Use only --model-id or --docker-image')
        exit(1)
    elif not args.model_id and not args.docker_image:
        print('Use with --model-id or --docker-image')
        exit(1)

    current_containers = legion.containers.docker.get_stack_containers_and_images(client, network_id)

    if args.model_id:
        for image in current_containers['model_images']:
            model_name = image.labels.get('com.epam.legion.model.id', None)
            if model_name == args.model_id:
                image = image
                model_id = model_name
                break
        else:
            raise Exception('Cannot found image for model_id = %s' % (args.model_id,))
    elif args.docker_image:
        try:
            image = client.images.get(args.docker_image)
        except docker.errors.ImageNotFound:
            print('Cannot find %s locally. Pulling' % args.docker_image)
            image = client.images.pull(args.docker_image)

        model_id = image.labels.get('com.epam.legion.model.id', None)
        if not model_id:
            raise Exception('Cannot detect model_id in image')
    else:
        raise Exception('Provide model-id or docker-image')

    # Detect current existing containers with models, stop and remove them
    LOGGER.info('Founding containers with model_id=%s', model_id)

    for container in current_containers['models']:
        model_name = container.labels.get('com.epam.legion.model.id', None)
        if model_name == model_id:
            LOGGER.info('Stopping container #%s', container.short_id)
            container.stop()
            LOGGER.info('Removing container #%s', container.short_id)
            container.remove()

    container_labels = legion.containers.docker.generate_docker_labels_for_container(image)

    ports = {}
    if args.expose_model_port is not None:
        exposing_port = args.expose_model_port
        ports['%d/tcp' % os.getenv(*legion.config.LEGION_PORT)] = exposing_port

    environment = {}
    envs_to_copy_in_new_container = (
        legion.config.REGISTER_ON_CONSUL[0],
    )

    for env in envs_to_copy_in_new_container:
        if env in os.environ:
            environment[env] = os.environ.get(env)

    LOGGER.info('Starting container with image #%s for model %s', image.short_id, model_id)
    container = client.containers.run(image,
                                      network=network_id,
                                      stdout=True,
                                      stderr=True,
                                      detach=True,
                                      environment=environment,
                                      ports=ports,
                                      labels=container_labels)

    if legion.utils.string_to_bool(os.getenv(*legion.config.REGISTER_ON_GRAFANA)):
        LOGGER.info('Creating Grafana dashboard for model %s' % (model_id,))
        grafana_client = legion.external.grafana.build_client(args)
        grafana_client.create_dashboard_for_model_by_labels(container_labels)

    print('Successfully created docker container %s for model %s' % (container.short_id, model_id))
    return container


def undeploy_model(args):
    """
    Undeploy model from Docker Host

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    client = legion.containers.docker.build_docker_client(args)
    network_id = legion.containers.docker.find_network(client, args)
    grafana_client = legion.external.grafana.build_client(args)

    current_containers = legion.containers.docker.get_stack_containers_and_images(client, network_id)

    for container in current_containers['models']:
        model_name = container.labels.get('com.epam.legion.model.id', None)
        if model_name == args.model_id:
            target_container = container
            break
    else:
        raise Exception('Cannot found container for model_id = %s' % (args.model_id,))

    LOGGER.info('Stopping container #%s', target_container.short_id)
    target_container.stop()
    LOGGER.info('Removing container #%s', target_container.short_id)
    target_container.remove()
    LOGGER.info('Removing Grafana dashboard for model %s', args.model_id)
    grafana_client.remove_dashboard_for_model(args.model_id)

    print('Successfully undeployed model %s' % (args.model_id,))


def inspect(args):
    """
    Print information about current containers / images state

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    client = legion.containers.docker.build_docker_client(args)
    network_id = legion.containers.docker.find_network(client, args)
    containers = legion.containers.docker.get_stack_containers_and_images(client, network_id)

    all_required_containers_is_ok = True

    print('%sServices:%s' % (Colors.BOLD, Colors.ENDC))
    for container in containers['services']:
        is_running = container.status == 'running'
        container_name = container.labels.get('com.epam.legion.container_description', container.image.tags[0])
        container_required = container.labels.get('com.epam.legion.container_required', 'true').lower()
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
        print('%s-- looks like legion stack hasn\'t been deployed --%s' % (Colors.FAIL, Colors.ENDC))

    print('%sModel instances:%s' % (Colors.BOLD, Colors.ENDC))
    for container in containers['models']:
        is_running = container.status == 'running'
        line_color = Colors.OKGREEN if is_running else Colors.FAIL
        container_status = '%s #%s' % (container.status, container.short_id)

        model_name = container.labels.get('com.epam.legion.model.id',
                                          'Undefined model ' + ','.join(container.image.tags))
        model_image_id = container.image.short_id
        model_version = container.labels.get('com.epam.legion.model.version', '?')

        print('%s*%s %s%s%s #%s (version: %s) - %s%s%s' % (line_color, Colors.ENDC,
                                                           Colors.UNDERLINE, model_name, Colors.ENDC,
                                                           model_image_id, model_version,
                                                           line_color, container_status, Colors.ENDC))

    if not containers['models']:
        print('%s-- cannot find any model instances --%s' % (Colors.WARNING, Colors.ENDC))

    print('%sModel images:%s' % (Colors.BOLD, Colors.ENDC))
    for image in containers['model_images']:
        model_name = image.labels.get('com.epam.legion.model.id', 'Undefined model')
        model_image_id = image.short_id
        model_version = image.labels.get('com.epam.legion.model.version', '?')
        print('* %s%s%s #%s (version: %s)' % (Colors.UNDERLINE, model_name, Colors.ENDC, model_image_id, model_version))

    if not containers['model_images']:
        print('%s-- cannot find any model images --%s' % (Colors.WARNING, Colors.ENDC))

    if not all_required_containers_is_ok:
        return 2
