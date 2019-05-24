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
import typing

from texttable import Texttable

from legion.cli.parsers import security, prepare_resources, add_resources_params
from legion.sdk.clients import edi
from legion.sdk.clients.deployment import build_client, ModelDeployment, ModelDeploymentClient, READY_STATE, \
    FAILED_STATE
from legion.sdk.clients.edi import WrongHttpStatusCode, LocalEdiClient
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.containers.headers import DOMAIN_MODEL_NAME, DOMAIN_MODEL_VERSION

DEFAULT_WAIT_TIMEOUT = 5

DEFAULT_WIDTH = 120
MD_HEADER = ["Name", "State", "Min/Current/Max Replicas", "Service URL"]

DEFAULT_WIDTH_LOCAL = 160
MD_LOCAL_HEADER = ["Name", "Image", "Port", "Model Name", "Model Version"]

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def _convert_md_from_args(args: argparse.Namespace) -> ModelDeployment:
    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename).resource
        if not isinstance(resource, ModelDeployment):
            raise ValueError(f'ModelDeployment expected, but {type(resource)} provided')
        return resource
    elif args.name:
        return ModelDeployment(
            name=args.name,
            image=args.image,
            resources=prepare_resources(args),
            min_replicas=args.min_replicas,
            max_replicas=args.max_replicas,
            liveness_probe_initial_delay=args.livenesstimeout,
            readiness_probe_initial_delay=args.readinesstimeout,
            role_name=args.role_name,
        )
    else:
        raise ValueError(f'Provide name of a Model Deployment or path to a file')


def _prepare_labels(args: argparse.Namespace) -> typing.Dict[str, typing.Any]:
    """
    Convert cli parameters to k8s labels

    :param args: cli parameters
    :return: k8s labels
    """
    labels = {}
    if args.model_name:
        labels[DOMAIN_MODEL_NAME] = args.model_name
    if args.model_version:
        labels[DOMAIN_MODEL_VERSION] = args.model_version

    return labels


def get_local(args: argparse.Namespace):
    """
    Get all Model Deployments or by name
    :param args: cli parameters
    """
    md_client = LocalEdiClient()
    model_deployments = md_client.inspect(args.name)

    table = Texttable(max_width=DEFAULT_WIDTH_LOCAL)
    table.set_cols_align("c" * len(MD_LOCAL_HEADER))
    table.set_cols_valign("t" * len(MD_LOCAL_HEADER))
    table.add_rows([MD_LOCAL_HEADER] + [[
        md.deployment_name,
        md.image,
        md.local_port,
        md.name_and_version.name,
        md.name_and_version.version
    ] for md in model_deployments])
    print(table.draw() + "\n")


def get(args: argparse.Namespace):
    """
    Get all Model Deployments or by name
    :param args: cli parameters
    """
    if args.name and (args.model_name or args.model_version):
        raise ValueError(f'You should specify model deployment name or labels')

    if args.local:
        return get_local(args)

    md_client = build_client(args)

    model_deployments = [md_client.get(args.name)] if args.name else md_client.get_all(_prepare_labels(args))
    if not model_deployments:
        return

    table = Texttable(max_width=DEFAULT_WIDTH)
    table.set_cols_align("c" * len(MD_HEADER))
    table.set_cols_valign("t" * len(MD_HEADER))
    table.add_rows([MD_HEADER] + [[
        md.name,
        md.state,
        f'{md.min_replicas}/{md.available_replicas}/{md.max_replicas}',
        md.service_url
    ] for md in model_deployments])
    print(table.draw() + "\n")


def create(args: argparse.Namespace):
    """
    Create Model Deployment
    :param args: cli parameters
    """
    if args.local:
        md_client = LocalEdiClient()
        return md_client.deploy(args.name, args.image, args.port)

    md_client = build_client(args)

    md = _convert_md_from_args(args)
    message = md_client.create(md)

    wait_operation_finish(args, md.name, md_client)

    print(message)


def edit(args: argparse.Namespace):
    """
    Edit Model Deployments by name
    :param args: cli parameters
    """
    if args.local:
        print('Local mode is not supported for edit action.')
        return

    md_client = build_client(args)

    md = _convert_md_from_args(args)
    message = md_client.edit(md)

    wait_operation_finish(args, md.name, md_client)

    print(message)


def delete(args: argparse.Namespace):
    """
    Delete Model Deployment by name
    :param args: cli parameters
    """
    if args.local:
        md_client = LocalEdiClient()
        if not args.name:
            print('Please specify name of deployment')
            return

        return md_client.undeploy(args.name)

    md_client = build_client(args)

    md_name = args.name
    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename)
        if not isinstance(resource.resource, ModelDeployment):
            raise ValueError(f'ModelDeployment expected, but {type(resource.resource)} provided')
        md_name = resource.resource_name

    try:
        message = md_client.delete(md_name) if md_name else md_client.delete_all(_prepare_labels(args))
        print(message)
    except WrongHttpStatusCode as e:
        if e.status_code != 404 or not args.ignore_not_found:
            raise e

        print(f'Model deployment {md_name} was not found. Ignore')


def wait_operation_finish(args: argparse.Namespace, md_name: str, md_client: ModelDeploymentClient):
    """
    Wait deployment to finish according command line arguments

    :param md_name: Model Deployment name
    :param args: command arguments with .model_name, .namespace
    :param md_client: Model Deployment Client

    :return: None
    """
    if args.no_wait:
        return

    start = time.time()
    if args.timeout <= 0:
        raise Exception('Invalid --timeout argument: should be positive integer')

    while True:
        elapsed = time.time() - start
        if elapsed > args.timeout:
            raise Exception('Time out: operation has not been confirmed')

        try:
            md: ModelDeployment = md_client.get(md_name)
            if md.state == READY_STATE:
                if md.replicas == md.available_replicas:
                    print(f'Model {md_name} was deployed. '
                          f'Deployment process took is {round(time.time() - start)} seconds')
                    return
                else:
                    print(f'Model {md_name} was deployed. '
                          f'Number of available pods is {md.available_replicas}/{md.replicas}')
            elif md.state == FAILED_STATE:
                raise Exception(f'Model deployment {md_name} was failed')
            elif md.state == "":
                print(f"Can't determine the state of {md.name}. Sleeping...")
            else:
                print(f'Current deployment state is {md.state}. Sleeping...')
        except WrongHttpStatusCode:
            LOGGER.info('Callback have not confirmed completion of the operation')

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)


def _deployment_params(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--port', default=0,
                        type=int, help='port to listen on. Only for --local mode')
    parser.add_argument('--min-replicas', default=0, type=int, help='min number of instances')
    parser.add_argument('--max-replicas', default=1, type=int, help='max number of instances')
    parser.add_argument('--livenesstimeout', default=2, type=int,
                        help='model startup timeout for liveness probe')
    parser.add_argument('--readinesstimeout', default=2, type=int,
                        help='model startup timeout for readiness probe')
    parser.add_argument('--image', type=str, help='docker image')
    parser.add_argument('--role-name', '--role', type=str, help='role name')


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:  # pylint: disable=R0915
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    md_subparser = main_subparser.add_parser('model-deployment', aliases=('md', 'deployment'),
                                             description='Model Deployment manipulations').add_subparsers()

    md_create_parser = md_subparser.add_parser('create',
                                               description='deploys a model into a kubernetes cluster')
    md_create_parser.add_argument('name', nargs='?', type=str, help='VCS Credential name', default="")
    md_create_parser.add_argument('--local', action='store_true',
                                  help='deploy model locally. Incompatible with other arguments')
    _deployment_params(md_create_parser)
    add_resources_params(md_create_parser)
    edi.add_arguments_for_wait_operation(md_create_parser)
    security.add_edi_arguments(md_create_parser)
    md_create_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Deployment')
    md_create_parser.set_defaults(func=create)

    md_edit_parser = md_subparser.add_parser('edit',
                                             description='deploys a model into a kubernetes cluster')
    md_edit_parser.add_argument('name', nargs='?', type=str, help='VCS Credential name', default="")
    md_edit_parser.add_argument('--local', action='store_true',
                                help='edit locally deployed model. Incompatible with other arguments')
    _deployment_params(md_edit_parser)
    add_resources_params(md_edit_parser)
    md_edit_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Deployment')
    security.add_edi_arguments(md_edit_parser)
    edi.add_arguments_for_wait_operation(md_edit_parser)
    md_edit_parser.set_defaults(func=edit)

    md_get_parser = md_subparser.add_parser('get', description='get information about currently deployed models')
    md_get_parser.add_argument('name', type=str, nargs='?', help='VCS Credential name', default="")
    md_get_parser.add_argument('--local', action='store_true',
                               help='get locally deployed models. Incompatible with other arguments')
    md_get_parser.add_argument('--model-name', type=str, help='model name')
    md_get_parser.add_argument('--model-version', type=str, help='model version')
    security.add_edi_arguments(md_get_parser)
    md_get_parser.set_defaults(func=get)

    md_delete_parser = md_subparser.add_parser('delete', description='undeploy model deployment')
    md_delete_parser.add_argument('name', type=str, nargs='?', help='VCS Credential name', default="")
    md_delete_parser.add_argument('--local', action='store_true',
                                  help='delete locally deployed models. Incompatible with other arguments')
    md_delete_parser.add_argument('--model-name', type=str, help='model name')
    md_delete_parser.add_argument('--model-version', type=str, help='model version')
    md_delete_parser.add_argument('--ignore-not-found', action='store_true',
                                  help='ignore if Model Deployment is not found')
    md_delete_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Deployment')
    security.add_edi_arguments(md_delete_parser)
    md_delete_parser.set_defaults(func=delete)
