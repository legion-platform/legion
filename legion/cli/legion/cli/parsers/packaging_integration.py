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
from legion.sdk.clients.packaging_integration import PackagingIntegrationClient
from legion.sdk.models import PackagingIntegration

IGNORE_NOT_FOUND_ERROR_MESSAGE = 'Packaging integration {} was not found. Ignore'
ID_AND_FILE_MISSED_ERROR_MESSAGE = f'You should provide a packaging integration ID or file parameter, not both.'


@click.group()
@click.option('--edi', help='EDI server host', default=config.EDI_URL)
@click.option('--token', help='EDI server jwt token', default=config.EDI_TOKEN)
@click.pass_context
def packaging_integration(ctx: click.core.Context, edi: str, token: str):
    """
    Allow you to perform actions on packaging integration
    """
    ctx.obj = PackagingIntegrationClient(edi, token)


@packaging_integration.command()
@click.option('--pi-id', '--id', help='Packaging integration ID')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT, callback=validate_output_format)
@pass_obj
def get(client: PackagingIntegrationClient, pi_id: str, output_format: str):
    """
    Get packaging integrations.\n
    The command without id argument retrieve all packaging integrations.\n
    Get all packaging integrations in json format:\n
        legionctl pack-integration get --format json\n
    Get packaging integration with "git-repo" id:\n
        legionctl pack-integration get --id git-repo\n
    Using jsonpath:\n
        legionctl pack-integration get -o 'jsonpath=[*].spec.reference'
    \f
    :param client: Packaging integration HTTP client
    :param pi_id: Packaging integration ID
    :param output_format: Output format
    :return:
    """
    pis = [client.get(pi_id)] if pi_id else client.get_all()

    format_output(pis, output_format)


@packaging_integration.command()
@click.option('--pi-id', '--id', help='Packaging integration ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with packaging integration')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT, callback=validate_output_format)
@pass_obj
def create(client: PackagingIntegrationClient, pi_id: str, file: str, output_format: str):
    """
    Create a packaging integration.\n
    You should specify a path to file with a packaging integration.
    The file must contain only one packaging integration.
    For now, CLI supports yaml and JSON file formats.
    If you want to create multiples packaging integrations than you should use "legionctl res apply" instead.
    If you provide the packaging integration id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl pack-integration create -f pi.yaml --id examples-git
    \f
    :param client: Packaging integration HTTP client
    :param pi_id: Packaging integration ID
    :param file: Path to the file with only one packaging integration
    :param output_format: Output format
    """
    pi = parse_resources_file_with_one_item(file).resource
    if not isinstance(pi, PackagingIntegration):
        raise ValueError(f'Packaging integration expected, but {type(pi)} provided')

    if pi_id:
        pi.id = pi_id

    click.echo(format_output([client.create(pi)], output_format))


@packaging_integration.command()
@click.option('--pi-id', '--id', help='Packaging integration ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with packaging integration')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT, callback=validate_output_format)
@pass_obj
def edit(client: PackagingIntegrationClient, pi_id: str, file: str, output_format: str):
    """
    Update a packaging integration.\n
    You should specify a path to file with a packaging integration.
    The file must contain only one packaging integration.
    For now, CLI supports yaml and JSON file formats.
    If you want to update multiples packaging integrations than you should use "legionctl res apply" instead.
    If you provide the packaging integration id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl pack-integration update -f pi.yaml --id examples-git
    \f
    :param client: Packaging integration HTTP client
    :param pi_id: Packaging integration ID
    :param file: Path to the file with only one packaging integration
    :param output_format: Output format
    """
    pi = parse_resources_file_with_one_item(file).resource
    if not isinstance(pi, PackagingIntegration):
        raise ValueError(f'Packaging integration expected, but {type(pi)} provided')

    if pi_id:
        pi.id = pi_id

    click.echo(format_output([client.edit(pi)], output_format))


@packaging_integration.command()
@click.option('--pi-id', '--id', help='Packaging integration ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with packaging integration')
@click.option('--ignore-not-found/--not-ignore-not-found', default=False,
              help='ignore if toolchain integration is not found')
@pass_obj
def delete(client: PackagingIntegrationClient, pi_id: str, file: str, ignore_not_found: bool):
    """
    Delete a packaging integration.\n
    For this command, you must provide a packaging integration ID or path to file with one packaging integration.
    The file must contain only one packaging integration.
    If you want to delete multiples packaging integrations than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl pack-integration delete --id examples-git\n
        * legionctl pack-integration delete -f pi.yaml
    \f
    :param client: Packaging integration HTTP client
    :param pi_id: Packaging integration ID
    :param file: Path to the file with only one packaging integration
    :param ignore_not_found: ignore if toolchain integration is not found
    """
    if not pi_id and not file:
        raise ValueError(ID_AND_FILE_MISSED_ERROR_MESSAGE)

    if pi_id and file:
        raise ValueError(ID_AND_FILE_MISSED_ERROR_MESSAGE)

    if file:
        pi = parse_resources_file_with_one_item(file).resource
        if not isinstance(pi, PackagingIntegration):
            raise ValueError(f'Packaging Integration expected, but {type(pi)} provided')

        pi_id = pi.id

    try:
        click.echo(client.delete(pi_id))
    except WrongHttpStatusCode as e:
        if e.status_code != http.HTTPStatus.NOT_FOUND or not ignore_not_found:
            raise e

        click.echo(IGNORE_NOT_FOUND_ERROR_MESSAGE.format(pi_id))
