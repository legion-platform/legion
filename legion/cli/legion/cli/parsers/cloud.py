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
import sys
import typing

from legion.cli.parsers import security
from legion.sdk.clients.edi import build_client, RemoteEdiClient
from legion.sdk.clients.edi_aggregated import parse_resources_file, apply, LegionCloudResourceUpdatePair

LOGGER = logging.getLogger(__name__)


def _print_resources_info_counter(objects: typing.Tuple[LegionCloudResourceUpdatePair]) -> str:
    """
    Output count of resources with their's types

    :param objects: resources to print
    :type objects: typing.Tuple[LegionCloudResourceUpdatePair]
    :return: str
    """
    names = ', '.join(f'{type(obj.resource).__name__} {obj.resource_name}' for obj in objects)
    if objects:
        return f'{len(objects)} ({names})'
    else:
        return str(len(objects))


def process_bulk_operation(edi_client: RemoteEdiClient, filename: str, is_removal: bool):
    """
    Apply bulk operation helper

    :param edi_client: base EDI client to extract connection options from
    :type edi_client: :py:class:RemoteEdiClient
    :param filename: path to file with resources
    :type filename: str
    :param is_removal: is it removal operation
    :type is_removal: bool
    :return: None
    """
    resources = parse_resources_file(filename)
    result = apply(resources, edi_client, is_removal)
    output = ['Operation completed']
    if result.created:
        output.append(f'created resources: {_print_resources_info_counter(result.created)}')
    if result.changed:
        output.append(f'changed resources: {_print_resources_info_counter(result.changed)}')
    if result.removed:
        output.append(f'removed resources: {_print_resources_info_counter(result.removed)}')
    print(', '.join(output))

    if result.errors:
        print(f'Some errors detected:')
        for error in result.errors:
            print(f'\t{error}')
        sys.exit(1)


def apply_command(args: argparse.Namespace):
    """
    Apply resources from file

    :param args: cli parameters
    """
    client = build_client(args)
    process_bulk_operation(client, args.filename, False)


def remove_command(args: argparse.Namespace):
    """
    Remove resources from file

    :param args: cli parameters
    """
    client = build_client(args)
    process_bulk_operation(client, args.filename, True)


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    mt_subparser = main_subparser.add_parser('cloud', aliases=('cloud-bulk',),
                                             description='Bulk operations on Legion cloud resources').add_subparsers()

    apply_parser = mt_subparser.add_parser('apply', description='Create/Update Legion resources on a cloud')
    security.add_edi_arguments(apply_parser)
    apply_parser.add_argument('filename', type=str, help='Path to file with resources declaration (YAML/JSON)')
    apply_parser.set_defaults(func=apply_command)

    remove_parser = mt_subparser.add_parser('remove', description='Remove Legion resources from a cloud')
    security.add_edi_arguments(remove_parser)
    remove_parser.add_argument('filename', type=str, help='Path to file with resources declaration (YAML/JSON)')
    remove_parser.set_defaults(func=remove_command)
