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

from texttable import Texttable

from legion.cli.parsers import security
from legion.sdk.clients import edi
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.clients.route import build_client, ModelRoute, ModelRouteClient, READY_STATE, ModelDeploymentTarget

DEFAULT_WAIT_TIMEOUT = 5

DEFAULT_WIDTH = 160
MD_HEADER = ["Name", "State", "Edge URL", "Model Deployment Targets", "Mirror"]

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def _convert_mr_from_args(args: argparse.Namespace) -> ModelRoute:
    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename).resource
        if not isinstance(resource, ModelRoute):
            raise ValueError(f'ModelRoute expected, but {type(resource)} provided')
        return resource
    elif args.name:
        return ModelRoute(
            name=args.name,
            url_prefix=args.url_prefix,
            model_deployment_targets=args.model_deployment_target,
            mirror=args.mirror,
        )
    else:
        raise ValueError(f'Provide name of a Model Route or path to a file')


def get(args: argparse.Namespace):
    """
    Get all Model Routes or by name
    :param args: cli parameters
    """
    mr_client = build_client(args)

    model_routes = [mr_client.get(args.name)] if args.name else mr_client.get_all()
    if not model_routes:
        return

    table = Texttable(max_width=DEFAULT_WIDTH)
    table.set_cols_align("c" * len(MD_HEADER))
    table.set_cols_valign("t" * len(MD_HEADER))
    table.add_rows([MD_HEADER] + [[
        mr.name,
        mr.state,
        mr.edge_url,
        ','.join(map(lambda md: f'{md.name}={md.weight}', mr.model_deployment_targets)),
        mr.mirror
    ] for mr in model_routes])
    print(table.draw() + "\n")


def create(args: argparse.Namespace):
    """
    Create Model Route
    :param args: cli parameters
    """
    mr_client = build_client(args)

    mr = _convert_mr_from_args(args)
    message = mr_client.create(mr)

    wait_operation_finish(args, mr.name, mr_client)

    print(message)


def edit(args: argparse.Namespace):
    """
    Edit Model Routes by name
    :param args: cli parameters
    """
    mr_client = build_client(args)

    mr = _convert_mr_from_args(args)
    message = mr_client.edit(mr)

    wait_operation_finish(args, mr.name, mr_client)

    print(message)


def delete(args: argparse.Namespace):
    """
    Delete Model Route by name
    :param args: cli parameters
    """
    mr_client = build_client(args)

    if not args.filename and not args.name:
        raise ValueError(f'Provide name of a Model Route or path to a file')

    mr_name = args.name
    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename)
        if not isinstance(resource.resource, ModelRoute):
            raise ValueError(f'ModelRoute expected, but {type(resource.resource)} provided')
        mr_name = resource.resource_name

    try:
        message = mr_client.delete(mr_name) if mr_name else mr_client.delete_all()
        print(message)
    except WrongHttpStatusCode as e:
        if e.status_code != 404 or not args.ignore_not_found:
            raise e

        print(f'Model route {mr_name} was not found. Ignore')


def _parse_targets(var: str) -> ModelDeploymentTarget:
    """
    Parse cli `-p md_name=weight` parameter

    :param var: target cli parameter
    :return: Model deployment target
    """
    if '=' not in var:
        return ModelDeploymentTarget(name=var, weight=100)

    md_name, weight = var.split('=')
    md_name, weight = md_name.strip(), weight.strip()

    if not md_name:
        raise ValueError(f'Model deployment is empty: {var}')

    if not weight:
        raise ValueError(f'Weight is empty: {var}')

    return ModelDeploymentTarget(name=md_name, weight=int(weight))


def wait_operation_finish(args: argparse.Namespace, mr_name: str, mr_client: ModelRouteClient):
    """
    Wait route to finish according command line arguments

    :param mr_name: Model Route name
    :param args: command arguments
    :param mr_client: Model Route Client

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
            mr = mr_client.get(mr_name)
            if mr.state == READY_STATE:
                print(f'Model Route {mr_name} is ready')
                return
            elif mr.state == "":
                print(f"Can't determine the state of {mr.name}. Sleeping...")
            else:
                print(f'Current route state is {mr.state}. Sleeping...')
        except WrongHttpStatusCode:
            LOGGER.info('Callback have not confirmed completion of the operation')

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)


def _common_mr_params(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('name', nargs='?', type=str, help='Model route name')
    parser.add_argument('--url-prefix', type=str, help='')
    parser.add_argument('--model-deployment-target', '--target', '-t', action='append', type=_parse_targets,
                        help='Format: Model_deployment_name=weight. For example: -t test-1=50 -t test-2=50')
    parser.add_argument('--mirror', type=str, help='')


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:  # pylint: disable=R0915
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    mr_subparser = main_subparser.add_parser('model-route', aliases=('mr', 'route'),
                                             description='Model Route manipulations').add_subparsers()

    mr_create_parser = mr_subparser.add_parser('create',
                                               description='deploys a model into a kubernetes cluster')
    _common_mr_params(mr_create_parser)
    edi.add_arguments_for_wait_operation(mr_create_parser)
    security.add_edi_arguments(mr_create_parser)
    mr_create_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Route')
    mr_create_parser.set_defaults(func=create)

    mr_edit_parser = mr_subparser.add_parser('edit',
                                             description='deploys a model into a kubernetes cluster')
    _common_mr_params(mr_edit_parser)
    mr_edit_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Route')
    security.add_edi_arguments(mr_edit_parser)
    edi.add_arguments_for_wait_operation(mr_edit_parser)
    mr_edit_parser.set_defaults(func=edit)

    mr_get_parser = mr_subparser.add_parser('get', description='get information about currently deployed models')
    mr_get_parser.add_argument('name', type=str, nargs='?', help='Model route name', default="")
    security.add_edi_arguments(mr_get_parser)
    mr_get_parser.set_defaults(func=get)

    mr_delete_parser = mr_subparser.add_parser('delete', description='undeploy model route')
    mr_delete_parser.add_argument('name', type=str, nargs='?', help='Model route name')
    mr_delete_parser.add_argument('--ignore-not-found', action='store_true',
                                  help='ignore if Model Route is not found')
    mr_delete_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Route')
    security.add_edi_arguments(mr_delete_parser)
    mr_delete_parser.set_defaults(func=delete)
