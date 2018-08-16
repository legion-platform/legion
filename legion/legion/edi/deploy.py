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
import legion.config
import legion.containers.docker
import legion.containers.headers
import legion.k8s
import legion.external.edi
import legion.external.grafana
import legion.pymodel
import legion.model
import legion.utils
from legion.utils import Colors, ExternalFileReader

LOGGER = logging.getLogger(__name__)

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
            raise Exception('Cannot find model binary {}'.format(external_reader.path))

        container = legion.pymodel.Model.load(external_reader.path)
        model_id = container.model_id

        image_labels = legion.containers.docker.generate_docker_labels_for_image(external_reader.path, model_id, args)

        LOGGER.info('Building docker image...')
        image = legion.containers.docker.build_docker_image(
            client,
            model_id,
            external_reader.path,
            image_labels,
            args.docker_image_tag
        )

        LOGGER.info('Image has been built: {}'.format(image))

        legion.utils.send_header_to_stderr(legion.containers.headers.IMAGE_TAG_LOCAL, image.id)

        if args.push_to_registry:
            legion.containers.docker.push_image_to_registry(client, image, args.push_to_registry)

        return image


def inspect_kubernetes(args):
    """
    Inspect kubernetes

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = legion.external.edi.build_client(args)
    model_deployments = edi_client.inspect(args.model_id, args.model_version)

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
    model_deployments = edi_client.inspect(args.model_id, args.model_version)

    if not model_deployments:
        if args.ignore_not_found:
            print('Cannot find any deployment - ignoring')
            return
        else:
            raise Exception('Cannot find any deployment')

    if len(model_deployments) > 1:
        raise Exception('Founded more then one deployment')

    target_deployment = model_deployments[0]

    edi_client.undeploy(args.model_id, args.grace_period, args.model_version)

    if not args.no_wait:
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > args.wait_timeout and args.wait_timeout != 0:
                raise Exception('Time out: model has not been undeployed')

            information = [info
                           for info in edi_client.inspect()
                           if info.model == target_deployment.model and info.version == target_deployment.version]

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
                raise Exception('Cannot find model deployment after deploy for image {}'.format(args.image))

            deployment = information[0]

            if deployment.ready_replicas >= deployment.scale and deployment.model_api_ok:
                break

            time.sleep(1)
