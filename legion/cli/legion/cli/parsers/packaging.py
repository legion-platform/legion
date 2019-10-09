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
Packing commands for legion cli
"""
import logging
import time
from http.client import HTTPException

import click
from requests import RequestException

from legion.cli.utils.client import pass_obj
from legion.cli.utils.logs import print_logs
from legion.cli.utils.output import format_output, DEFAULT_OUTPUT_FORMAT
from legion.sdk import config
from legion.sdk.clients.edi import WrongHttpStatusCode, EDIConnectionException
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.clients.packaging import ModelPackaging, ModelPackagingClient, SUCCEEDED_STATE, FAILED_STATE

DEFAULT_WAIT_TIMEOUT = 3
DEFAULT_PACKAGING_TIMEOUT = 2400
LOG_READ_TIMEOUT_SECONDS = 60

LOGGER = logging.getLogger(__name__)


@click.group()
@click.option('--edi', help='EDI server host', default=config.EDI_URL)
@click.option('--token', help='EDI server jwt token', default=config.EDI_TOKEN)
@click.pass_context
def packaging(ctx: click.core.Context, edi: str, token: str):
    """
    Allow you to perform actions on packagings
    """
    ctx.obj = ModelPackagingClient(edi, token)


@packaging.command()
@click.option('--pack-id', '--id', help='Model packaging ID')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT)
@pass_obj
def get(client: ModelPackagingClient, pack_id: str, output_format: str):
    """
    Get packagings.\n
    The command without id argument retrieve all packagings.\n
    Get all packagings in json format:\n
        legionctl pack get --format json\n
    Get packaging with "git-repo" id:\n
        legionctl pack get --id git-repo\n
    Using jsonpath:\n
        legionctl pack get -o 'jsonpath=[*].spec.reference'
    \f
    :param client: Model packaging HTTP client
    :param pack_id: Model packaging ID
    :param output_format: Output format
    :return:
    """
    packs = [client.get(pack_id)] if pack_id else client.get_all()

    format_output(packs, output_format)


@packaging.command()
@click.option('--pack-id', '--id', help='Model packaging ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with packaging')
@click.option('--wait/--no-wait', default=True,
              help='no wait until scale will be finished')
@click.option('--artifact-name', type=str, help='Override artifact name from file')
@click.option('--timeout', default=DEFAULT_PACKAGING_TIMEOUT, type=int,
              help='timeout in seconds. for wait (if no-wait is off)')
@pass_obj
def create(client: ModelPackagingClient, pack_id: str, file: str, wait: bool, timeout: int,
           artifact_name: str):
    """
    Create a packaging.\n
    You should specify a path to file with a packaging. The file must contain only one packaging.
    For now, CLI supports yaml and JSON file formats.
    If you want to create multiples packagings than you should use "legionctl res apply" instead.
    If you provide the packaging id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl pack create -f pack.yaml --id examples-git
    \f
    :param timeout: timeout in seconds. for wait (if no-wait is off)
    :param wait: no wait until scale will be finished
    :param client: Model packaging HTTP client
    :param pack_id: Model packaging ID
    :param file: Path to the file with only one packaging
    :param artifact_name: Override artifact name from file
    """
    pack = parse_resources_file_with_one_item(file).resource
    if not isinstance(pack, ModelPackaging):
        raise ValueError(f'Model packaging expected, but {type(pack)} provided')

    if pack_id:
        pack.id = pack_id

    if artifact_name:
        pack.spec.artifact_name = artifact_name

    mp = client.create(pack)
    click.echo(f"Start packing: {mp}")

    wait_packaging_finish(timeout, wait, pack.id, client)


@packaging.command()
@click.option('--pack-id', '--id', help='Model packaging ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with packaging')
@click.option('--wait/--no-wait', default=True,
              help='no wait until scale will be finished')
@click.option('--artifact-name', type=str, help='Override artifact name from file')
@click.option('--timeout', default=DEFAULT_PACKAGING_TIMEOUT, type=int,
              help='timeout in seconds. for wait (if no-wait is off)')
@pass_obj
def edit(client: ModelPackagingClient, pack_id: str, file: str, wait: bool, timeout: int,
         artifact_name: str):
    """
    Update a packaging.\n
    You should specify a path to file with a packaging. The file must contain only one packaging.
    For now, CLI supports yaml and JSON file formats.
    If you want to update multiples packagings than you should use "legionctl res apply" instead.
    If you provide the packaging id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl pack update -f pack.yaml --id examples-git
    \f
    :param client: Model packaging HTTP client
    :param pack_id: Model packaging ID
    :param file: Path to the file with only one packaging
    :param timeout: timeout in seconds. for wait (if no-wait is off)
    :param wait: no wait until scale will be finished
    :param artifact_name: Override artifact name from file
    """
    pack = parse_resources_file_with_one_item(file).resource
    if not isinstance(pack, ModelPackaging):
        raise ValueError(f'Model packaging expected, but {type(pack)} provided')

    if pack_id:
        pack.id = pack_id

    if artifact_name:
        pack.spec.artifact_name = artifact_name

    mp = client.edit(pack)
    click.echo(f"Rerun packing: {mp}")

    wait_packaging_finish(timeout, wait, pack.id, client)


@packaging.command()
@click.option('--pack-id', '--id', help='Model packaging ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with packaging')
@click.option('--ignore-not-found/--not-ignore-not-found', default=False,
              help='ignore if Model Packaging is not found')
@pass_obj
def delete(client: ModelPackagingClient, pack_id: str, file: str, ignore_not_found: bool):
    """
    Delete a packaging.\n
    For this command, you must provide a packaging ID or path to file with one packaging.
    The file must contain only one packaging.
    If you want to delete multiples packagings than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl pack delete --id examples-git\n
        * legionctl pack delete -f pack.yaml
    \f
    :param client: Model packaging HTTP client
    :param pack_id: Model packaging ID
    :param file: Path to the file with only one packaging
    :param ignore_not_found: ignore if Model Packaging is not found
    """
    if not pack_id and not file:
        raise ValueError(f'You should provide a packaging ID or file parameter, not both.')

    if pack_id and file:
        raise ValueError(f'You should provide a packaging ID or file parameter, not both.')

    if file:
        pack = parse_resources_file_with_one_item(file).resource
        if not isinstance(pack, ModelPackaging):
            raise ValueError(f'Model packaging expected, but {type(pack)} provided')

        pack_id = pack.id

    try:
        message = client.delete(pack_id)
        click.echo(message)
    except WrongHttpStatusCode as e:
        if e.status_code != 404 or not ignore_not_found:
            raise e

        click.echo(f'Model packaging {pack_id} was not found. Ignore')


@packaging.command()
@click.option('--pack-id', '--id', help='Model packaging ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with packaging')
@click.option('--follow/--not-follow', default=True,
              help='Follow logs stream')
@pass_obj
def logs(client: ModelPackagingClient, pack_id: str, file: str, follow: bool):
    """
    Stream packaging logs.\n
    For this command, you must provide a packaging ID or path to file with one packaging.
    The file must contain only one packaging.
    If you want to delete multiples packagings than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl pack delete --id examples-git\n
        * legionctl pack delete -f pack.yaml
    \f
    :param follow: Follow logs stream
    :param client: Model packaging HTTP client
    :param pack_id: Model packaging ID
    :param file: Path to the file with only one packaging
    """
    if not pack_id and not file:
        raise ValueError(f'You should provide a packaging ID or file parameter, not both.')

    if pack_id and file:
        raise ValueError(f'You should provide a packaging ID or file parameter, not both.')

    if file:
        pack = parse_resources_file_with_one_item(file).resource
        if not isinstance(pack, ModelPackaging):
            raise ValueError(f'Model packaging expected, but {type(pack)} provided')

        pack_id = pack.id

    for msg in client.log(pack_id, follow):
        print_logs(msg)


def wait_packaging_finish(timeout: int, wait: bool, mp_id: str, mp_client: ModelPackagingClient):
    """
    Wait packaging to finish according command line arguments

    :param wait:
    :param timeout:
    :param mp_id: Model Packaging name
    :param mp_client: Model Packaging Client
    """
    if not wait:
        return

    start = time.time()
    if timeout <= 0:
        raise Exception('Invalid --timeout argument: should be positive integer')

    # We create a separate client for logs because it has the different timeout settings
    log_mp_client = ModelPackagingClient.construct_from_other(mp_client)
    log_mp_client.timeout = mp_client.timeout, LOG_READ_TIMEOUT_SECONDS

    click.echo("Logs streaming...")

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise Exception('Time out: operation has not been confirmed')

        try:
            mp = mp_client.get(mp_id)
            if mp.status.state == SUCCEEDED_STATE:
                click.echo(f'Model {mp_id} was packed. Packaging took {round(time.time() - start)} seconds')
                return
            elif mp.status.state == FAILED_STATE:
                raise Exception(f'Model packaging {mp_id} was failed.')
            elif mp.status.state == "":
                click.echo(f"Can't determine the state of {mp.id}. Sleeping...")
            else:
                for msg in log_mp_client.log(mp.id, follow=True):
                    print_logs(msg)

        except (WrongHttpStatusCode, HTTPException, RequestException, EDIConnectionException) as e:
            LOGGER.info('Callback have not confirmed completion of the operation. Exception: %s', str(e))

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)
