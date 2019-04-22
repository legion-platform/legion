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

from legion.cli.parsers import security
from legion.sdk.clients import edi
from legion.sdk.clients.deployment import build_client, ModelDeployment, ModelDeploymentClient, SUCCESS_STATE, \
    FAILED_STATE
from legion.sdk.clients.edi import WrongHttpStatusCode, LocalEdiClient
from legion.sdk.containers.headers import DOMAIN_MODEL_ID, DOMAIN_MODEL_VERSION

DEFAULT_WIDTH = 80

DEFAULT_WAIT_TIMEOUT = 5

MD_HEADER = ["Name", "State", "Replicas", "Service URL"]

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def _prepare_labels(args: argparse.Namespace) -> typing.Dict[str, typing.Any]:
    """
    Convert cli parameters to k8s labels

    :param args: cli parameters
    :return: k8s labels
    """
    labels = {}
    if args.model_id:
        labels[DOMAIN_MODEL_ID] = args.model_id
    if args.model_version:
        labels[DOMAIN_MODEL_VERSION] = args.model_version

    return labels


def get(args: argparse.Namespace):
    """
    Get all Model Deployments or by name
    :param args: cli parameters
    """
    md_client = build_client(args)

    if args.name and (args.model_id or args.model_version):
        raise ValueError(f'You should specify model deployment name or labels')

    model_deployments = [md_client.get(args.name)] if args.name else md_client.get_all(_prepare_labels(args))
    if not model_deployments:
        return

    table = Texttable(max_width=DEFAULT_WIDTH)
    table.set_cols_align("c" * len(MD_HEADER))
    table.set_cols_valign("t" * len(MD_HEADER))
    table.add_rows([MD_HEADER] + [[
        md.name,
        md.state,
        md.replicas,
        md.service_url
    ] for md in model_deployments])
    print(table.draw() + "\n")


def _prepare_resources(args: argparse.Namespace) -> typing.Dict[str, typing.Any]:
    """
    Convert cli parameters to k8s resources
    :param args: cli parameters
    :return: k8s resources
    """
    resources = {"limits": {}, "requests": {}}
    if args.memory_limit:
        resources["limits"]["memory"] = args.memory_limit
    if args.memory_request:
        resources["requests"]["memory"] = args.memory_request
    if args.cpu_limit:
        resources["limits"]["cpu"] = args.cpu_limit
    if args.cpu_request:
        resources["requests"]["cpu"] = args.cpu_request

    if not resources["limits"]:
        del resources["limits"]

    if not resources["requests"]:
        del resources["requests"]

    return resources


def create(args: argparse.Namespace):
    """
    Create Model Deployment
    :param args: cli parameters
    """
    if args.local:
        md_client = LocalEdiClient()
        return md_client.deploy(args.image, args.port)

    md_client = build_client(args)

    message = md_client.create(ModelDeployment(
        name=args.name,
        image=args.image,
        resources=_prepare_resources(args),
        annotations=args.annotations,
        replicas=args.replicas,
        liveness_probe_initial_delay=args.livenesstimeout,
        readiness_probeInitial_delay=args.readinesstimeout
    ))

    wait_deployment_finish(args, md_client)

    print(message)


def edit(args: argparse.Namespace):
    """
    Edit Model Deployments by name
    :param args: cli parameters
    """
    md_client = build_client(args)

    message = md_client.edit(ModelDeployment(
        name=args.name,
        image=args.image,
        resources=_prepare_resources(args),
        annotations=args.arg,
        replicas=args.replicas,
        liveness_probe_initial_delay=args.livenesstimeout,
        readiness_probeInitial_delay=args.readinesstimeout
    ))

    wait_deployment_finish(args, md_client)

    print(message)


def scale(args: argparse.Namespace):
    """
    Change number of Model Deployments replicas
    :param args: cli parameters
    """
    md_client = build_client(args)

    message = md_client.scale(args.name, args.replicas)

    wait_deployment_finish(args, md_client)

    print(message)


def delete(args: argparse.Namespace):
    """
    Delete Model Deployment by name
    :param args: cli parameters
    """
    md_client = build_client(args)

    try:
        message = md_client.delete(args.name) if args.name else md_client.delete_all(_prepare_labels(args))
        print(message)
    except WrongHttpStatusCode as e:
        if e.status_code != 404 or not args.ignore_not_found:
            raise e

        print(f'Model deployment {args.name} was not found. Ignore')


def wait_deployment_finish(args: argparse.Namespace, md_client: ModelDeploymentClient):
    """
    Wait training to finish according command line arguments

    :param args: command arguments with .model_id, .namespace
    :param md_client: Model Training Client

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
            md = md_client.get(args.name)
            if md.state == SUCCESS_STATE:
                print(f'Model {args.name} was deployed. '
                      f'Deployment process took is {round(time.time() - start)} seconds')
                return
            elif md.state == FAILED_STATE:
                raise Exception(f'Model deployment {args.name} was failed')

            print(f'Current deployment state is {md.state}. Sleeping...')
        except WrongHttpStatusCode:
            LOGGER.info('Callback have not confirmed completion of the operation')

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    md_subparser = main_subparser.add_parser('model-deployment', aliases=('md', 'deployment'),
                                             description='Model Training manipulations').add_subparsers()

    md_create_parser = md_subparser.add_parser('create',
                                               description='deploys a model into a kubernetes cluster')
    md_create_parser.add_argument('name', type=str, help='VCS Credential name', default="")
    md_create_parser.add_argument('--image',
                                  type=str, help='docker image', required=True)
    md_create_parser.add_argument('--local', action='store_true',
                                  help='deploy model locally. Incompatible with other arguments')
    md_create_parser.add_argument('--port', default=0,
                                  type=int, help='port to listen on. Only for --local mode')
    md_create_parser.add_argument('--replicas', default=1, type=int, help='count of instances')
    md_create_parser.add_argument('--annotations', type=str, help='count of instances')
    md_create_parser.add_argument('--livenesstimeout', default=2, type=int,
                                  help='model startup timeout for liveness probe')
    md_create_parser.add_argument('--readinesstimeout', default=2, type=int,
                                  help='model startup timeout for readiness probe')
    md_create_parser.add_argument('--memory-limit', default=None, type=str, help='limit memory for model deployment')
    md_create_parser.add_argument('--memory-request', '--memory', default=None, type=str,
                                  help='request memory for model deployment')
    md_create_parser.add_argument('--cpu-limit', default=None, type=str, help='limit cpu for model deployment')
    md_create_parser.add_argument('--cpu-request', default=None, type=str, help='request cpu for model deployment')
    edi.add_arguments_for_wait_operation(md_create_parser)
    security.add_edi_arguments(md_create_parser)
    md_create_parser.set_defaults(func=create)

    md_edit_parser = md_subparser.add_parser('edit',
                                             description='deploys a model into a kubernetes cluster')
    md_edit_parser.add_argument('name', type=str, help='VCS Credential name', default="")
    md_edit_parser.add_argument('--image',
                                type=str, help='docker image', required=True)
    md_edit_parser.add_argument('--local', action='store_true',
                                help='deploy model locally. Incompatible with other arguments')
    md_edit_parser.add_argument('--port', default=0,
                                type=int, help='port to listen on. Only for --local mode')
    md_edit_parser.add_argument('--replicas', default=1,
                                type=int, help='count of instances')
    md_edit_parser.add_argument('--livenesstimeout', default=2, type=int,
                                help='model startup timeout for liveness probe')
    md_edit_parser.add_argument('--readinesstimeout', default=2, type=int,
                                help='model startup timeout for readiness probe')
    md_edit_parser.add_argument('--memory-limit', default=None, type=str, help='limit memory for model deployment')
    md_edit_parser.add_argument('--memory-request', '--memory', default=None, type=str,
                                help='request memory for model deployment')
    md_edit_parser.add_argument('--cpu-limit', default=None, type=str, help='limit cpu for model deployment')
    md_edit_parser.add_argument('--cpu-request', default=None, type=str, help='request cpu for model deployment')
    edi.add_arguments_for_wait_operation(md_edit_parser)
    security.add_edi_arguments(md_edit_parser)
    md_edit_parser.set_defaults(func=create)

    md_get_parser = md_subparser.add_parser('get', description='get information about currently deployed models')
    md_get_parser.add_argument('name', type=str, nargs='?', help='VCS Credential name', default="")
    md_get_parser.add_argument('--model-id',
                               type=str, help='model ID')
    md_get_parser.add_argument('--model-version',
                               type=str, help='model version')
    security.add_edi_arguments(md_get_parser)
    md_get_parser.set_defaults(func=get)

    md_scale_parser = md_subparser.add_parser('scale',
                                              description='change count of model pods')
    md_scale_parser.add_argument('name', type=str, help='VCS Credential name', default="")
    md_scale_parser.add_argument('--replicas',
                                 type=int, help='new count of replicas', required=True)
    edi.add_arguments_for_wait_operation(md_scale_parser)
    security.add_edi_arguments(md_scale_parser)
    md_scale_parser.set_defaults(func=scale)

    md_delete_parser = md_subparser.add_parser('delete',
                                               description='undeploy model deployment')
    md_delete_parser.add_argument('name', type=str, nargs='?', help='VCS Credential name', default="")
    md_delete_parser.add_argument('--model-id',
                                  type=str, help='model ID')
    md_delete_parser.add_argument('--model-version',
                                  type=str, help='model version')
    md_delete_parser.add_argument('--ignore-not-found', action='store_true',
                                  help='ignore if Model Deployment is not found')
    md_delete_parser.add_argument('--local', action='store_true',
                                  help='un-deploy local deployed model. Incompatible with --grace-period')
    edi.add_arguments_for_wait_operation(md_delete_parser)
    security.add_edi_arguments(md_delete_parser)
    md_delete_parser.set_defaults(func=delete)
