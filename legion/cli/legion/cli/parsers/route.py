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
import logging
import time

import click
from click import pass_obj
from legion.cli.utils.output import DEFAULT_OUTPUT_FORMAT, format_output
from legion.sdk import config
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.clients.route import ModelRoute, ModelRouteClient, READY_STATE

DEFAULT_WAIT_TIMEOUT = 5
LOGGER = logging.getLogger(__name__)


@click.group()
@click.option('--edi', help='EDI server host', default=config.EDI_URL)
@click.option('--token', help='EDI server jwt token', default=config.EDI_TOKEN)
@click.pass_context
def route(ctx: click.core.Context, edi: str, token: str):
    """
    Allow you to perform actions on routes
    """
    ctx.obj = ModelRouteClient(edi, token)


@route.command()
@click.option('--mr-id', '--id', help='ModelRoute ID')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT)
@pass_obj
def get(client: ModelRouteClient, mr_id: str, output_format: str):
    """
    Get routes.\n
    The command without id argument retrieve all routes.\n
    Get all routes in json format:\n
        legionctl conn get --format json\n
    Get model route with "git-repo" id:\n
        legionctl conn get --id git-repo\n
    Using jsonpath:\n
        legionctl conn get -o 'jsonpath=[*].spec.reference'
    \f
    :param client: ModelRoute HTTP client
    :param mr_id: ModelRoute ID
    :param output_format: Output format
    :return:
    """
    conns = [client.get(mr_id)] if mr_id else client.get_all()

    format_output(conns, output_format)


@route.command()
@click.option('--mr-id', '--id', help='ModelRoute ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with model route')
@click.option('--wait/--no-wait', default=True,
              help='no wait until scale will be finished')
@click.option('--timeout', default=600, type=int,
              help='timeout in seconds. for wait (if no-wait is off)')
@pass_obj
def create(client: ModelRouteClient, mr_id: str, file: str, wait: bool, timeout: int):
    """
    Create a model route.\n
    You should specify a path to file with a model route. The file must contain only one model route.
    For now, CLI supports yaml and JSON file formats.
    If you want to create multiples routes than you should use "legionctl res apply" instead.
    If you provide the model route id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl conn create -f conn.yaml --id examples-git
    \f
    :param timeout: timeout in seconds. for wait (if no-wait is off)
    :param wait: no wait until operation will be finished
    :param client: ModelRoute HTTP client
    :param mr_id: ModelRoute ID
    :param file: Path to the file with only one model route
    """
    conn = parse_resources_file_with_one_item(file).resource
    if not isinstance(conn, ModelRoute):
        raise ValueError(f'ModelRoute expected, but {type(conn)} provided')

    if mr_id:
        conn.id = mr_id

    click.echo(client.create(conn))

    wait_operation_finish(timeout, wait, mr_id, client)


@route.command()
@click.option('--route-id', '--id', help='ModelRoute ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with model route')
@pass_obj
def edit(client: ModelRouteClient, mr_id: str, file: str):
    """
    Update a model route.\n
    You should specify a path to file with a model route. The file must contain only one model route.
    For now, CLI supports yaml and JSON file formats.
    If you want to update multiples routes than you should use "legionctl res apply" instead.
    If you provide the model route id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl conn update -f conn.yaml --id examples-git
    \f
    :param client: Model route HTTP client
    :param mr_id: Model route ID
    :param file: Path to the file with only one model route
    """
    conn = parse_resources_file_with_one_item(file).resource
    if not isinstance(conn, ModelRoute):
        raise ValueError(f'ModelRoute expected, but {type(conn)} provided')

    if mr_id:
        conn.id = mr_id

    click.echo(client.edit(conn))


@route.command()
@click.option('--route-id', '--id', help='ModelRoute ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with model route')
@pass_obj
def delete(client: ModelRouteClient, mr_id: str, file: str):
    """
    Delete a model route.\n
    For this command, you must provide a model route ID or path to file with one model route.
    The file must contain only one model route.
    If you want to delete multiples routes than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl conn delete --id examples-git\n
        * legionctl conn delete -f conn.yaml
    \f
    :param client: ModelRoute HTTP client
    :param mr_id: ModelRoute ID
    :param file: Path to the file with only one model route
    """
    if not mr_id and not file:
        raise ValueError(f'You should provide a model route ID or file parameter, not both.')

    if mr_id and file:
        raise ValueError(f'You should provide a model route ID or file parameter, not both.')

    if file:
        conn = parse_resources_file_with_one_item(file).resource
        if not isinstance(conn, ModelRoute):
            raise ValueError(f'ModelRoute expected, but {type(conn)} provided')

        mr_id = conn.id

    click.echo(client.delete(mr_id))


def wait_operation_finish(timeout: int, wait: bool, mr_id: str, mr_client: ModelRouteClient):
    """
    Wait route to finish according command line arguments

    :param timeout: timeout in seconds. for wait (if no-wait is off)
    :param wait: no wait until operation will be finished
    :param mr_id: Model Route id
    :param args: command arguments
    :param mr_client: Model Route Client

    :return: None
    """
    if not wait:
        return

    start = time.time()
    if timeout <= 0:
        raise Exception('Invalid --timeout argument: should be positive integer')

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise Exception('Time out: operation has not been confirmed')

        try:
            mr = mr_client.get(mr_id)
            if mr.status.state == READY_STATE:
                print(f'Model Route {mr_id} is ready')
                return
            elif mr.status.state == "":
                print(f"Can't determine the state of {mr.id}. Sleeping...")
            else:
                print(f'Current route state is {mr.status.state}. Sleeping...')
        except WrongHttpStatusCode:
            LOGGER.info('Callback have not confirmed completion of the operation')

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)
