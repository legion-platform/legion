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
import sys
import typing

import click
from legion.cli.utils.client import pass_obj
from legion.sdk import config
from legion.sdk.clients.edi import RemoteEdiClient
from legion.sdk.clients.edi_aggregated import apply as edi_aggregated_apply
from legion.sdk.clients.edi_aggregated import parse_resources_file, LegionCloudResourceUpdatePair

LOGGER = logging.getLogger(__name__)


@click.group()
@click.option('--edi', help='EDI server host', default=config.EDI_URL)
@click.option('--token', help='EDI server jwt token', default=config.EDI_TOKEN)
@click.pass_context
def bulk(ctx: click.core.Context, edi: str, token: str):
    """
    Bulk operations on Legion resources
    """
    ctx.obj = RemoteEdiClient(edi, token)


@bulk.command()
@click.argument('file', required=True, type=click.Path())
@pass_obj
def apply(client: RemoteEdiClient, file: str):
    """
    Create/Update Legion resources on a EDI.\n
    You should specify a path to file with resources.
    For now, CLI supports yaml and JSON file formats.
    Usage example:\n
        * legionctl bulk apply resources.legion.yaml
    \f
    :param client: Generic EDI HTTP client
    :param file: Path to the file with legion resources
    """
    process_bulk_operation(client, file, False)


@bulk.command()
@click.argument('file', required=True, type=click.Path())
@pass_obj
def delete(client: RemoteEdiClient, file: str):
    """
    Remove Legion resources from a EDI.\n
    You should specify a path to file with resources.
    For now, CLI supports yaml and JSON file formats.
    Usage example:\n
        * legionctl bulk delete resources.legion.yaml
    \f
    :param client: Generic EDI HTTP client
    :param file: Path to the file with legion resources
    """
    process_bulk_operation(client, file, True)


def _print_resources_info_counter(objects: typing.Tuple[LegionCloudResourceUpdatePair]) -> str:
    """
    Output count of resources with their's types

    :param objects: resources to print
    :return: str
    """
    names = ', '.join(f'{type(obj.resource).__name__} {obj.resource_id}' for obj in objects)
    if objects:
        return f'{len(objects)} ({names})'
    else:
        return str(len(objects))


def process_bulk_operation(edi_client: RemoteEdiClient, filename: str, is_removal: bool):
    """
    Apply bulk operation helper

    :param edi_client: base EDI client to extract connection options from
    :param filename: path to file with resources
    :param is_removal: is it removal operation
    """
    legion_resources = parse_resources_file(filename)
    result = edi_aggregated_apply(legion_resources, edi_client, is_removal)
    output = ['Operation completed']
    if result.created:
        output.append(f'created resources: {_print_resources_info_counter(result.created)}')
    if result.changed:
        output.append(f'changed resources: {_print_resources_info_counter(result.changed)}')
    if result.removed:
        output.append(f'removed resources: {_print_resources_info_counter(result.removed)}')
    click.echo(', '.join(output))

    if result.errors:
        click.echo(f'Some errors detected:')
        for error in result.errors:
            click.echo(f'\t{error}')
        sys.exit(1)
