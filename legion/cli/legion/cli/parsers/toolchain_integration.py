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
import http

import click
from legion.cli.utils.client import pass_obj
from legion.cli.utils.output import format_output, DEFAULT_OUTPUT_FORMAT, validate_output_format
from legion.sdk import config
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.clients.toolchain_integration import ToolchainIntegrationClient
from legion.sdk.models import ToolchainIntegration

IGNORE_NOT_FOUND_ERROR_MESSAGE = 'Toolchain integration {} was not found. Ignore'
ID_AND_FILE_MISSED_ERROR_MESSAGE = f'You should provide a toolchain ID or file parameter, not both.'


@click.group()
@click.option('--edi', help='EDI server host', default=config.EDI_URL)
@click.option('--token', help='EDI server jwt token', default=config.EDI_TOKEN)
@click.pass_context
def toolchain_integration(ctx: click.core.Context, edi: str, token: str):
    """
    Allow you to perform actions on toolchain integration
    """
    ctx.obj = ToolchainIntegrationClient(edi, token)


@toolchain_integration.command()
@click.option('--ti-id', '--id', help='Toolchain integration ID')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT, callback=validate_output_format)
@pass_obj
def get(client: ToolchainIntegrationClient, ti_id: str, output_format: str):
    """
    Get toolchain integrations.\n
    The command without id argument retrieve all toolchain integrations.\n
    Get all toolchain integrations in json format:\n
        legionctl tn-integration get --format json\n
    Get toolchain integration with "git-repo" id:\n
        legionctl tn-integration get --id git-repo\n
    Using jsonpath:\n
        legionctl tn-integration get -o 'jsonpath=[*].spec.reference'
    \f
    :param client: Toolchain integration HTTP client
    :param ti_id: Toolchain integration ID
    :param output_format: Output format
    :return:
    """
    tis = [client.get(ti_id)] if ti_id else client.get_all()

    format_output(tis, output_format)


@toolchain_integration.command()
@click.option('--ti-id', '--id', help='Toolchain integration ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with toolchain integration')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT, callback=validate_output_format)
@pass_obj
def create(client: ToolchainIntegrationClient, ti_id: str, file: str, output_format: str):
    """
    Create a toolchain integration.\n
    You should specify a path to file with a toolchain integration.
    The file must contain only one toolchain integration.
    For now, CLI supports yaml and JSON file formats.
    If you want to create multiples toolchain integrations than you should use "legionctl res apply" instead.
    If you provide the toolchain integration id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl tn-integration create -f ti.yaml --id examples-git
    \f
    :param client: Toolchain integration HTTP client
    :param ti_id: Toolchain integration ID
    :param file: Path to the file with only one toolchain integration
    :param output_format: Output format
    """
    ti = parse_resources_file_with_one_item(file).resource
    if not isinstance(ti, ToolchainIntegration):
        raise ValueError(f'Toolchain integration expected, but {type(ti)} provided')

    if ti_id:
        ti.id = ti_id

    click.echo(format_output([client.create(ti)], output_format))


@toolchain_integration.command()
@click.option('--ti-id', '--id', help='Toolchain integration ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with toolchain integration')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT, callback=validate_output_format)
@pass_obj
def edit(client: ToolchainIntegrationClient, ti_id: str, file: str, output_format: str):
    """
    Update a toolchain integration.\n
    You should specify a path to file with a toolchain integration.
    The file must contain only one toolchain integration.
    For now, CLI supports yaml and JSON file formats.
    If you want to update multiples toolchain integrations than you should use "legionctl res apply" instead.
    If you provide the toolchain integration id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl tn-integration update -f ti.yaml --id examples-git
    \f
    :param client: Toolchain integration HTTP client
    :param ti_id: Toolchain integration ID
    :param file: Path to the file with only one toolchain integration
    :param output_format: Output format
    """
    ti = parse_resources_file_with_one_item(file).resource
    if not isinstance(ti, ToolchainIntegration):
        raise ValueError(f'Toolchain integration expected, but {type(ti)} provided')

    if ti_id:
        ti.id = ti_id

    click.echo(format_output([client.edit(ti)], output_format))


@toolchain_integration.command()
@click.option('--ti-id', '--id', help='Toolchain integration ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with toolchain integration')
@click.option('--ignore-not-found/--not-ignore-not-found', default=False,
              help='ignore if toolchain integration is not found')
@pass_obj
def delete(client: ToolchainIntegrationClient, ti_id: str, file: str, ignore_not_found: bool):
    """
    Delete a toolchain integration.\n
    For this command, you must provide a toolchain integration ID or path to file with one toolchain integration.
    The file must contain only one toolchain integration.
    If you want to delete multiples toolchain integrations than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl tn-integration delete --id examples-git\n
        * legionctl tn-integration delete -f ti.yaml
    \f
    :param client: Toolchain integration HTTP client
    :param ti_id: Toolchain integration ID
    :param file: Path to the file with only one toolchain integration
    :param ignore_not_found: ignore if toolchain integration is not found
    """
    if not ti_id and not file:
        raise ValueError(ID_AND_FILE_MISSED_ERROR_MESSAGE)

    if ti_id and file:
        raise ValueError(ID_AND_FILE_MISSED_ERROR_MESSAGE)

    if file:
        ti = parse_resources_file_with_one_item(file).resource
        if not isinstance(ti, ToolchainIntegration):
            raise ValueError(f'Toolchain Integration expected, but {type(ti)} provided')

        ti_id = ti.id

    try:
        click.echo(client.delete(ti_id))
    except WrongHttpStatusCode as e:
        if e.status_code != http.HTTPStatus.NOT_FOUND or not ignore_not_found:
            raise e

        click.echo(IGNORE_NOT_FOUND_ERROR_MESSAGE.format(ti_id))
