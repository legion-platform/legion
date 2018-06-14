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
import re

import docker
import docker.errors
import legion.exceptions
import legion.config
import legion.containers.docker
import legion.containers.headers
import legion.k8s
import legion.external.edi
import legion.external.grafana
import legion.io
import legion.utils
from legion.utils import Colors, ExternalFileReader

LOGGER = logging.getLogger(__name__)
VALID_SERVING_WORKERS = legion.containers.docker.VALID_SERVING_WORKERS

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


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
            raise legion.exceptions.CannotFindModelBinary(path=external_reader.path)

        with legion.io.ModelContainer(external_reader.path, do_not_load_model=True) as container:
            model_id = container.get('model.id', None)
            if args.model_id:
                model_id = args.model_id

        if not model_id:
            raise legion.exceptions.ModelIdIsMissedInModelBinary()

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

        legion.utils.send_header_to_stderr(legion.containers.headers.IMAGE_TAG_LOCAL, image.id)

        if args.push_to_registry:
            external_image_name = args.push_to_registry
            docker_registry = external_image_name
            version = None

            registry_delimiter = docker_registry.find('/')
            if registry_delimiter < 0:
                raise legion.exceptions.InvalidRegistryFormat()

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

            legion.utils.send_header_to_stderr(legion.containers.headers.IMAGE_TAG_EXTERNAL, image_and_registry)

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

    data = []

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

        data.append({
            'deployment': deployment,
            'errors': errors,
            'line_color': line_color
        })

    if args.format == INSPECT_FORMAT_COLORIZED:
        if data:
            print('%sModel deployments:%s' % (Colors.BOLD, Colors.ENDC))

            for item in data:
                arguments = (
                    item['line_color'], Colors.ENDC,
                    Colors.UNDERLINE, item['deployment'].model, Colors.ENDC,
                    item['deployment'].image, item['deployment'].version,
                    item['line_color'], item['deployment'].ready_replicas, item['deployment'].scale, item['errors'],
                    Colors.ENDC
                )
                print('%s*%s %s%s%s %s (version: %s) - %s%s / %d pods ready %s%s' % arguments)

        if not model_deployments:
            print('%s-- cannot find any model deployments --%s' % (Colors.WARNING, Colors.ENDC))

        if not data and model_deployments:
            print('%s-- cannot find any model deployments after filtering --%s' % (Colors.WARNING, Colors.ENDC))
    elif args.format == INSPECT_FORMAT_TABULAR:
        headers = 'Model ID', 'Image', 'Version', 'Ready', 'Scale', 'Errors'
        items = [[
            item['deployment'].model,
            item['deployment'].image,
            item['deployment'].version,
            str(item['deployment'].ready_replicas),
            str(item['deployment'].scale),
            item['errors'],
        ] for item in data]

        if data:
            columns_width = [max(len(val[col_idx]) for val in items) for col_idx, column in enumerate(headers)]
            columns_width = [max(columns_width[col_idx], len(column)) for col_idx, column in enumerate(headers)]

            print('|'. join('{name:{width}} '.format(name=column, width=columns_width[col_idx])
                            for col_idx, column in enumerate(headers)))
            for item in items:
                print('|'.join('{name:{width}} '.format(name=column, width=columns_width[col_idx])
                               for col_idx, column in enumerate(item)))


def undeploy_kubernetes(args):
    """
    Undeploy model to kubernetes

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    # Firstly try to inspect current models
    try:
        edi_client.undeploy(args.model_id, args.grace_period, args.model_version)
    except Exception as exception:
        if 'No one model can be found' in str(exception) and args.ignore_not_found:
            print('Cannot find any deployment - ignoring')
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
    edi_client.scale(args.model_id, args.scale, args.model_version)


def deploy_kubernetes(args):
    """
    Deploy kubernetes model

    :param args: command arguments with .model_id, .namespace and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    edi_client.deploy(args.image, args.scale)

    # Start waiting of readiness of all PODs
    if not args.no_wait:
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > args.wait_timeout and args.wait_timeout != 0:
                break

            information = [info for info in edi_client.inspect() if info.image == args.image]

            if not information:
                raise legion.exceptions.CannotFindModelDeploymentAfterDeploy(args.image)

            deployment = information[0]

            if deployment.ready_replicas >= deployment.scale and deployment.model_api_ok:
                break

            time.sleep(1)



