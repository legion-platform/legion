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
EDI commands for legion cli
"""
import argparse
import logging
import time

from legion.cli.parsers import security
from legion.sdk import config
from legion.sdk.clients import edi
from legion.sdk.containers import definitions as containers_def
from legion.sdk.utils import Colors

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def inspect(args):
    """
    Inspect models on remote cluster or local machine

    :param args: command arguments with .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = edi.build_client(args)
    LOGGER.info('Sending inspect request to {!r}'.format(edi_client))
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
            print('{}Model deployments:{}'.format(Colors.BOLD, Colors.ENDC))

            for item in data:
                deploy_mode = item['deployment'].deploy_mode
                if deploy_mode == containers_def.ModelDeploymentDescription.MODE_LOCAL:
                    api_url = '{}:{}'.format(config.LOCAL_DEPLOY_HOSTNAME,
                                             item['deployment'].local_port)
                    print('{}* [LOCAL]{} {}{}{} (ver. {}) container: {} api: {} image: {} {}{}{}'.format(
                        item['line_color'], Colors.ENDC,
                        Colors.UNDERLINE, item['deployment'].model, Colors.ENDC, item['deployment'].version,
                        item['deployment'].container_id, api_url,
                        item['deployment'].image,
                        item['line_color'], item['errors'],
                        Colors.ENDC
                    ))
                elif deploy_mode == containers_def.ModelDeploymentDescription.MODE_CLUSTER:
                    print('{}* [CLUSTER]{} {}{}{} (ver. {}) image: {} {}{}/{} pods ready {}{}'.format(
                        item['line_color'], Colors.ENDC,
                        Colors.UNDERLINE, item['deployment'].model, Colors.ENDC, item['deployment'].version,
                        item['deployment'].image,
                        item['line_color'], item['deployment'].ready_replicas, item['deployment'].scale, item['errors'],
                        Colors.ENDC
                    ))
                else:
                    print('Unknown deployment mode {}'.format(deploy_mode))

        if not model_deployments:
            print('{}-- cannot find any model deployments --{}'.format(Colors.WARNING, Colors.ENDC))

        if not data and model_deployments:
            print('{}-- cannot find any model deployments after filtering --{}'.format(Colors.WARNING, Colors.ENDC))
    elif args.format == INSPECT_FORMAT_TABULAR:
        headers = 'Model ID', 'Version', 'Deploy Mode', 'Container', 'Local Port', 'Image', 'Ready', 'Scale', 'Errors'
        items = [[
            item['deployment'].model,
            item['deployment'].version,
            item['deployment'].deploy_mode,
            item['deployment'].container_id,
            item['deployment'].local_port,
            item['deployment'].image,
            str(item['deployment'].ready_replicas),
            str(item['deployment'].scale),
            item['errors'],
        ] for item in data]

        if data:
            output_table(headers, items)


def output_table(headers, rows):
    """
    Output table to console

    :param headers: list of header names
    :type headers: list[str]
    :param rows: list of rows
    :type rows: list[list[any]]
    :return: None
    """
    columns_width = [max(len(str(row[col_idx])) for row in rows) for col_idx, column in enumerate(headers)]
    columns_width = [max(columns_width[col_idx], len(column)) for col_idx, column in enumerate(headers)]

    print('|'.join('{name:{width}} '.format(name=column, width=columns_width[col_idx])
                   for col_idx, column in enumerate(headers)))
    for row in rows:
        print('|'.join('{name:{width}} '.format(name=str(column_value), width=columns_width[col_idx])
                       for col_idx, column_value in enumerate(row)))


def undeploy(args):
    """
    Undeploy model from remote cluster or on local machine

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = edi.build_client(args)
    LOGGER.info('Sending undeploy request to {!r}'.format(edi_client))
    model_deployments = edi_client.undeploy(args.model_id,
                                            args.grace_period,
                                            args.model_version,
                                            args.ignore_not_found)
    LOGGER.info('Server returned list of affected deployments: {!r}'.format(model_deployments))

    wait_operation_finish(args, edi_client,
                          model_deployments,
                          lambda affected_deployments_status: not affected_deployments_status)


def wait_operation_finish(args, edi_client, model_deployments, wait_callback):
    """
    Wait operation to finish according command line arguments. Uses wait_callback for checking status

    :param args: command arguments with .model_id, .namespace
    :type args: :py:class:`argparse.Namespace`
    :param edi_client: EDI client instance
    :type edi_client: :py:class:`legion.external.edi.EdiClient`
    :param model_deployments: models that have been affected during operation call
    :type model_deployments: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
    :param wait_callback: function that will be called to ensure that operation completed (should return True)
    :type wait_callback: py:class:`Callable[[list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]],
                                            typing.Optional[bool]]`
    :return: None
    """
    if not args.no_wait:
        start = time.time()
        if args.timeout <= 0:
            raise Exception('Invalid --timeout argument: should be positive integer')

        LOGGER.debug('Starting checking cycle limited to {} s.'.format(args.timeout))

        while True:
            elapsed = time.time() - start
            if elapsed > args.timeout:
                raise Exception('Time out: operation has not been confirmed')

            LOGGER.info('Requesting actual status of affected deployments')
            affected_deployments_status = get_related_model_deployments(edi_client, model_deployments)
            LOGGER.debug('Server returned list of actual affected deployment statuses: {!r}'
                         .format(affected_deployments_status))

            result = wait_callback(affected_deployments_status)
            if result:
                LOGGER.info('Callback have confirmed completion of the operation')
                break
            else:
                LOGGER.info('Callback have not confirmed completion of the operation')

            LOGGER.debug('Sleep before next request')
            time.sleep(1)


def get_related_model_deployments(client, affected_deployments):
    """
    Get actual status of model deployments

    :param client: EDI client
    :type client: :py:class:`legion.external.edi.EdiClient`
    :param affected_deployments: affected by main operation (e.g. deploy) model deployments
    :type affected_deployments: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
    :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`] -- actual status of model deployments
    """
    affected_deployment_ids = {
        deployment.id_and_version
        for deployment
        in affected_deployments
    }
    actual_deployments_status = client.inspect()
    LOGGER.debug('Filtering all models using affected deployment list')
    return [deployment
            for deployment in actual_deployments_status
            if deployment.id_and_version in affected_deployment_ids]


def scale(args):
    """
    Scale model instances on remote cluster

    :param args: command arguments with .model_id, .namespace and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = edi.build_client(args)
    LOGGER.info('Sending scale request to {!r}'.format(edi_client))
    model_deployments = edi_client.scale(args.model_id, args.scale, args.model_version)
    LOGGER.info('Server returned list of affected deployments: {!r}'.format(model_deployments))

    wait_operation_finish(args, edi_client,
                          model_deployments,
                          lambda affected_deployments_status: check_all_scaled(affected_deployments_status,
                                                                               args.scale,
                                                                               len(model_deployments)))


def check_all_scaled(deployments_status, expected_scale, expected_count):
    """
    Check that all model finished scale process and now are OK

    :param deployments_status: actual deployment status
    :type deployments_status: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
    :param expected_scale: expected scale
    :type expected_scale: int
    :param expected_count: expected count of models
    :type expected_count: int
    :return: bool -- result of validation
    """
    # Get fully deployed models
    finally_deployed_models = [deployment
                               for deployment in deployments_status
                               if deployment.ready_replicas == expected_scale and deployment.model_api_ok]

    # Wait until all modes will be scaled
    return len(finally_deployed_models) == expected_count


def deploy(args):
    """
    Deploy model on remote cluster or on local machine

    :param args: command arguments with .model_id, .namespace, .livenesstimeout, .readinesstimeout, .model_iam_role,
                 .port, .memory, .cpu and .scale
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    edi_client = edi.build_client(args)
    LOGGER.info('Sending deploy request to {!r}'.format(edi_client))
    model_deployments = edi_client.deploy(args.image, model_iam_role=args.model_iam_role, count=args.scale,
                                          livenesstimeout=args.livenesstimeout, readinesstimeout=args.readinesstimeout,
                                          local_port=args.port, memory=args.memory, cpu=args.cpu)
    LOGGER.info('Server returned list of affected deployments: {!r}'.format(model_deployments))

    wait_operation_finish(args, edi_client,
                          model_deployments,
                          lambda affected_deployments_status: check_all_scaled(affected_deployments_status,
                                                                               args.scale,
                                                                               len(model_deployments)))


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    deploy_parser = main_subparser.add_parser('deploy',
                                              description='deploys a model into a kubernetes cluster')
    deploy_parser.add_argument('image',
                               type=str, help='docker image')
    deploy_parser.add_argument('--local',
                               action='store_true',
                               help='deploy model locally. Incompatible with other arguments')
    deploy_parser.add_argument('--port',
                               default=0,
                               type=int, help='port to listen on. Only for --local mode')
    deploy_parser.add_argument('--model-iam-role',
                               type=str, help='IAM role to be used at model pod')
    deploy_parser.add_argument('--scale',
                               default=1,
                               type=int, help='count of instances')
    deploy_parser.add_argument('--livenesstimeout',
                               default=2,
                               type=int, help='model startup timeout for liveness probe')
    deploy_parser.add_argument('--readinesstimeout',
                               default=2,
                               type=int, help='model startup timeout for readiness probe')
    deploy_parser.add_argument('--memory', default=None, type=str, help='limit memory for model deployment')
    deploy_parser.add_argument('--cpu', default=None, type=str, help='limit cpu for model deployment')
    edi.add_arguments_for_wait_operation(deploy_parser)
    security.add_edi_arguments(deploy_parser)
    deploy_parser.set_defaults(func=deploy)

    inspect_parser = main_subparser.add_parser('inspect',
                                               description='get information about currently deployed models')
    inspect_parser.add_argument('--model-id',
                                type=str, help='model ID')
    inspect_parser.add_argument('--model-version',
                                type=str, help='model version')
    inspect_parser.add_argument('--format',
                                default=VALID_INSPECT_FORMATS[0],
                                choices=VALID_INSPECT_FORMATS, help='output format')
    inspect_parser.add_argument('--local',
                                action='store_true',
                                help='analyze local deployed models')
    security.add_edi_arguments(inspect_parser)
    inspect_parser.set_defaults(func=inspect)

    scale_parser = main_subparser.add_parser('scale',
                                             description='change count of model pods')
    scale_parser.add_argument('model_id',
                              type=str, help='model ID')
    scale_parser.add_argument('scale',
                              type=int, help='new count of replicas')
    scale_parser.add_argument('--model-version',
                              type=str, help='model version')
    edi.add_arguments_for_wait_operation(scale_parser)
    security.add_edi_arguments(scale_parser)
    scale_parser.set_defaults(func=scale)

    undeploy_parser = main_subparser.add_parser('undeploy',
                                                description='undeploy model deployment')
    undeploy_parser.add_argument('model_id',
                                 type=str, help='model ID')
    undeploy_parser.add_argument('--model-version',
                                 type=str, help='model version')
    undeploy_parser.add_argument('--grace-period',
                                 default=0,
                                 type=int, help='removal grace period')
    undeploy_parser.add_argument('--ignore-not-found',
                                 action='store_true', help='ignore if cannot found pod')
    undeploy_parser.add_argument('--local',
                                 action='store_true',
                                 help='un-deploy local deployed model. Incompatible with --grace-period')
    edi.add_arguments_for_wait_operation(undeploy_parser)
    security.add_edi_arguments(undeploy_parser)
    undeploy_parser.set_defaults(func=undeploy)
