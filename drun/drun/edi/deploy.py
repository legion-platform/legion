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
import logging

import drun.utils
from drun.utils import Colors, ExternalFileReader, normalize_name_to_dns_1123
import drun.model.io
import drun.const.env
import drun.const.headers
import drun.external.grafana
import drun.containers.docker
import drun.containers.k8s

import docker
import docker.errors
from kubernetes import client

LOGGER = logging.getLogger('deploy')
VALID_SERVING_WORKERS = drun.containers.docker.VALID_SERVING_WORKERS


def build_grafana_client(args):
    """
    Build Grafana client from ENV and from command line arguments

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`drun.grafana.GrafanaClient`
    """
    host = os.environ.get(*drun.const.env.GRAFANA_URL)
    user = os.environ.get(*drun.const.env.GRAFANA_USER)
    password = os.environ.get(*drun.const.env.GRAFANA_PASSWORD)

    if args.grafana_server:
        host = args.grafana_server

    if args.grafana_user and len(args.grafana_user):
        user = args.grafana_user

    if args.grafana_password and len(args.grafana_password):
        password = args.grafana_password

    LOGGER.info('Creating Grafana client for host: %s, user: %s, password: %s' % (host, user, '*' * len(password)))
    client = drun.external.grafana.GrafanaClient(host, user, password)

    return client


def build_model(args):
    """
    Build model

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Image` docker image
    """
    client = drun.containers.docker.build_docker_client(args)

    with ExternalFileReader(args.model_file) as external_reader:
        if not os.path.exists(external_reader.path):
            raise Exception('Cannot find model file: %s' % external_reader.path)

        with drun.model.io.ModelContainer(external_reader.path, do_not_load_model=True) as container:
            model_id = container.get('model.id', None)
            if args.model_id:
                model_id = args.model_id

        if not model_id:
            raise Exception('Cannot get model id (not setted in container and not setted in arguments)')

        image_labels = drun.containers.docker.generate_docker_labels_for_image(external_reader.path, model_id, args)

        base_docker_image = args.base_docker_image
        if not base_docker_image:
            base_docker_image = 'drun/base-python-image:latest'

        image = drun.containers.docker.build_docker_image(
            client,
            base_docker_image,
            model_id,
            external_reader.path,
            image_labels,
            args.python_package,
            args.docker_image_tag,
            args.serving
        )

        LOGGER.info('Built image: %s with python package: %s' % (image, args.python_package))

        print('Successfully created docker image %s for model %s' % (image.short_id, model_id))

        if args.push_to_registry:
            uri = args.push_to_registry  # type: str
            tag_start_position = uri.rfind(':')
            slash_latest_position = uri.rfind('/')

            if 0 < tag_start_position < slash_latest_position and slash_latest_position > 0:
                repository = uri
                tag = 'latest'

            print('Tagging image %s for model %s as %s' % (image.short_id, model_id, args.push_to_registry))
            image.tag(args.push_to_registry)
            print('Successfully tagged image %s for model %s as %s' % (image.short_id, model_id, args.push_to_registry))
            client.images.push(args.push_to_registry)
            print('Successfully pushed image %s for model %s to %s' % (image.short_id, model_id, args.push_to_registry))

        return image


def inspect_kubernetes(args):
    """
    Inspect kubernetes

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    deployments = drun.containers.k8s.find_all_models_deployments(args.namespace)
    print('%sModel deployments:%s' % (Colors.BOLD, Colors.ENDC))
    for deployment in deployments:
        ready_replicas = deployment.status.ready_replicas
        replicas = deployment.status.replicas
        line_color = Colors.OKGREEN

        if not ready_replicas or ready_replicas == 0:
            line_color = Colors.FAIL
        elif replicas > ready_replicas > 0:
            line_color = Colors.WARNING

        container_image = deployment.spec.template.spec.containers[0].image

        model_name = deployment.metadata.labels.get(
            normalize_name_to_dns_1123(drun.const.headers.DOMAIN_MODEL_ID), '?'
        )
        model_version = deployment.metadata.labels.get(
            normalize_name_to_dns_1123(drun.const.headers.DOMAIN_MODEL_VERSION), '?'
        )

        print('%s*%s %s%s%s %s (version: %s) - %s%s / %d pods ready%s' % (line_color, Colors.ENDC,
                                                                          Colors.UNDERLINE, model_name, Colors.ENDC,
                                                                          container_image, model_version,
                                                                          line_color, ready_replicas, replicas,
                                                                          Colors.ENDC))

    if not deployments:
        print('%s-- cannot find any model deployments --%s' % (Colors.WARNING, Colors.ENDC))


def undeploy_kubernetes(args):
    """
    Undeploy model to kubernetes

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    deployment = drun.containers.k8s.find_model_deployment(args.model_id, args.namespace)
    if not deployment:
        print('Cannot find deployment for model %s in namespace %s' % (args.model_id, args.namespace))
    else:
        drun.containers.k8s.remove_deployment(deployment, args.namespace, args.grace_period)


def scale_kubernetes(args):
    """
    Scale model instances

    :param args: command arguments with .model_id, .namespace and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    deployment = drun.containers.k8s.find_model_deployment(args.model_id, args.namespace)
    if not deployment:
        print('Cannot find deployment for model %s in namespace %s' % (args.model_id, args.namespace))
    else:
        drun.containers.k8s.scale_deployment(deployment, args.scale, args.namespace)


def get_kubernetes_meta_from_docker_image(args):
    """
    Build meta fields for kubernetes from docker image. Docker image will be pulled automatically.

    :param args: command arguments with .image
    :type args: :py:class:`argparse.Namespace`
    :return: tuple[str, dict[str, str]] -- deployment name and labels in DNS-1123 format
    """
    docker_client = drun.containers.docker.build_docker_client(args)
    try:
        docker_image = docker_client.images.get(args.image)
    except docker.errors.ImageNotFound:
        docker_image = docker_client.images.pull(args.image)

    required_headers = [
        drun.const.headers.DOMAIN_MODEL_ID,
        drun.const.headers.DOMAIN_MODEL_VERSION,
        drun.const.headers.DOMAIN_CONTAINER_TYPE
    ]

    if any(header not in docker_image.labels for header in required_headers):
        raise Exception('Missed on of %s labels. Available labels: %s' % (
            ', '.join(required_headers),
            ', '.join(tuple(docker_image.labels.keys()))
        ))

    deployment_name = "model.%s.%s.deployment" % (
        normalize_name_to_dns_1123(docker_image.labels[drun.const.headers.DOMAIN_MODEL_ID]),
        normalize_name_to_dns_1123(docker_image.labels[drun.const.headers.DOMAIN_MODEL_VERSION])
    )

    compatible_labels = {
        normalize_name_to_dns_1123(k): normalize_name_to_dns_1123(v)
        for k, v in
        docker_image.labels.items()
    }

    return deployment_name, compatible_labels


def deploy_kubernetes(args):
    """
    Deploy model to kubernetes

    :param args: command arguments with .docker_image, .scale, .text-output, .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Container` new instance
    """
    docker_client = drun.containers.docker.build_docker_client(args)
    # grafana_client = build_grafana_client(args)

    graphite_service = drun.containers.k8s.find_service('graphite', args.deployment, args.namespace)
    graphite_endpoint = drun.containers.k8s.get_service_url(graphite_service, 'statsd').split(':')

    grafana_service = drun.containers.k8s.find_service('grafana', args.deployment, args.namespace)
    grafana_endpoint = drun.containers.k8s.get_service_url(grafana_service, 'http')

    consul_service = drun.containers.k8s.find_service('consul', args.deployment, args.namespace)
    consul_endpoint = drun.containers.k8s.get_service_url(consul_service, 'http').split(':')

    # TODO: Question. What do?
    drun.containers.k8s.build_client()

    if args.image_for_k8s:
        kubernetes_image = args.image_for_k8s
    else:
        kubernetes_image = args.image

    deployment_name, compatible_labels = get_kubernetes_meta_from_docker_image(args)

    container_env_variables = {
        drun.const.env.STATSD_HOST[0]: graphite_endpoint[0],
        drun.const.env.STATSD_PORT[0]: graphite_endpoint[1],
        drun.const.env.GRAFANA_URL[0]: 'http://%s' % grafana_endpoint,
        drun.const.env.CONSUL_ADDR[0]: consul_endpoint[0],
        drun.const.env.CONSUL_PORT[0]: consul_endpoint[1],
    }

    container = client.V1Container(
        name='model',
        image=kubernetes_image,
        image_pull_policy='Always',
        env=[
            client.V1EnvVar(name=k, value=v)
            for k, v in container_env_variables.items()
        ],
        ports=[client.V1ContainerPort(container_port=5000, name='api', protocol='TCP')])

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=compatible_labels),
        spec=client.V1PodSpec(containers=[container]))

    deployment_spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=args.scale,
        template=template)

    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name, labels=compatible_labels),
        spec=deployment_spec)

    extensions_v1beta1 = client.ExtensionsV1beta1Api()

    # TODO: Add text output
    if args.text_output:
        data_dict = deployment.to_dict()
        # yaml.dump(data_dict, sys.stdout, default_flow_style=False)
        print(data_dict)
    else:
        api_response = extensions_v1beta1.create_namespaced_deployment(
            body=deployment,
            namespace=args.namespace)

        return api_response


def deploy_model(args):
    """
    Deploy model to docker host

    :param args: command arguments with .model_id, .model_file, .docker_network
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`docker.model.Container` new instance
    """
    client = drun.containers.docker.build_docker_client(args)
    network_id = drun.containers.docker.find_network(client, args)
    grafana_client = build_grafana_client(args)

    if args.model_id and args.docker_image:
        print('Use only --model-id or --docker-image')
        exit(1)
    elif not args.model_id and not args.docker_image:
        print('Use with --model-id or --docker-image')
        exit(1)

    current_containers = drun.containers.docker.get_stack_containers_and_images(client, network_id)

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
        try:
            image = client.images.get(args.docker_image)
        except docker.errors.ImageNotFound:
            print('Cannot find %s locally. Pulling' % args.docker_image)
            image = client.images.pull(args.docker_image)

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

    container_labels = drun.containers.docker.generate_docker_labels_for_container(image)

    ports = {}
    if args.expose_model_port:
        exposing_port = args.expose_model_port
        ports['%d/tcp' % os.getenv(*drun.const.env.LEGION_PORT)] = exposing_port

    LOGGER.info('Starting container with image #%s for model %s' % (image.short_id, model_id))
    container = client.containers.run(image,
                                      network=network_id,
                                      stdout=True,
                                      stderr=True,
                                      detach=True,
                                      ports=ports,
                                      labels=container_labels)

    LOGGER.info('Creating Grafana dashboard for model %s' % (model_id,))
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
    client = drun.containers.docker.build_docker_client(args)
    network_id = drun.containers.docker.find_network(client, args)
    grafana_client = build_grafana_client(args)

    current_containers = drun.containers.docker.get_stack_containers_and_images(client, network_id)

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
    LOGGER.info('Removing Grafana dashboard for model %s' % (args.model_id,))
    grafana_client.remove_dashboard_for_model(args.model_id)

    print('Successfully undeployed model %s' % (args.model_id,))


def inspect(args):
    """
    Print information about current containers / images state

    :param args: command arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    client = drun.containers.docker.build_docker_client(args)
    network_id = drun.containers.docker.find_network(client, args)
    containers = drun.containers.docker.get_stack_containers_and_images(client, network_id)

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
