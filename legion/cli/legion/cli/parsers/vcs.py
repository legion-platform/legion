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

from texttable import Texttable

from legion.cli.parsers import security
from legion.sdk.clients.vcs import build_client, VCSCredential
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item


VCS_HEADER = ["Name", "Type", "URI", "Default Reference", "Credential", "Public Key"]

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def _convert_vcs_from_args(args: argparse.Namespace) -> VCSCredential:
    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename).resource
        if not isinstance(resource, VCSCredential):
            raise ValueError(f'VCSCredential expected, but {type(resource)} provided')
        return resource
    elif args.name:
        return VCSCredential(
            name=args.name,
            type=args.type,
            uri=args.uri,
            default_reference=args.default_reference,
            credential=args.credential,
            public_key=args.public_key
        )
    else:
        raise ValueError(f'Provide name of a VCS Credential or path to a file')


def get(args: argparse.Namespace):
    """
    Get all of VCS Credentials or by name
    :param args: cli parameters
    """
    vcs_client = build_client(args)

    vcs_credentials = [vcs_client.get(args.name)] if args.name else vcs_client.get_all()

    table = Texttable()
    table.set_cols_align("c" * len(VCS_HEADER))
    table.set_cols_valign("t" * len(VCS_HEADER))
    table.add_rows([VCS_HEADER] + [[
        vcs.name,
        vcs.type,
        vcs.uri,
        vcs.default_reference,
        vcs.credential if args.show_secrets else '****',
        vcs.public_key
    ] for vcs in vcs_credentials])
    print(table.draw() + "\n")


def create(args: argparse.Namespace):
    """
    Create a VCS Credential
    :param args: cli parameters
    """
    vcs_client = build_client(args)

    message = vcs_client.create(_convert_vcs_from_args(args))

    print(message)


def edit(args: argparse.Namespace):
    """
    Edit a VCS Credential by name
    :param args: cli parameters
    """
    vcs_client = build_client(args)

    message = vcs_client.edit(_convert_vcs_from_args(args))

    print(message)


def delete(args: argparse.Namespace):
    """
    Edit a VCS Credential by name
    :param args: cli parameters
    """
    vcs_client = build_client(args)

    if not args.filename and not args.name:
        raise ValueError(f'Provide name of a VCS Credential or path to a file')

    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename)
        if not isinstance(resource.resource, VCSCredential):
            raise ValueError(f'VCSCredential expected, but {type(resource.resource)} provided')
        vcs_name = resource.resource_name
    else:
        vcs_name = args.name

    message = vcs_client.delete(vcs_name)
    print(message)


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    vcs_subparser = main_subparser.add_parser('vcs-credentials', aliases=('vcs',),
                                              description='VCS Credential manipulations').add_subparsers()

    vcs_get_parser = vcs_subparser.add_parser('get', description='Get all VCSCredentials or by name')
    vcs_get_parser.add_argument('name', type=str, nargs='?', help='VCS Credential name', default="")
    vcs_get_parser.add_argument('--show-secrets', action='store_true', help='show tokens and passwords', default=False)
    security.add_edi_arguments(vcs_get_parser)
    vcs_get_parser.set_defaults(func=get)

    vcs_create_parser = vcs_subparser.add_parser('create', description='Create a VCSCredential')
    vcs_create_parser.add_argument('name', nargs='?', type=str, help='VCS Credential name')
    vcs_create_parser.add_argument('--type', type=str, help='VCS Credential type: git')
    vcs_create_parser.add_argument('--uri', type=str,
                                   help='VCS Credential URI. For example: git@github.com:legion-platform/legion.git')
    vcs_create_parser.add_argument('--default-reference', type=str,
                                   help='Git reference: commit, branch ot tag')
    vcs_create_parser.add_argument('--credential', type=str, help='GIT SSH key')
    vcs_create_parser.add_argument('--public-key', type=str, help='Server public key')
    vcs_create_parser.add_argument('--filename', '-f', type=str, help='Filename to use to create the VCSCredential. '
                                                                      'This option ignores other VCS parameters!')
    security.add_edi_arguments(vcs_create_parser)
    vcs_create_parser.set_defaults(func=create)

    vcs_edit_parser = vcs_subparser.add_parser('edit', description='Get all VCSCredentials')
    vcs_edit_parser.add_argument('name', nargs='?', type=str, help='VCS Credential name')
    vcs_edit_parser.add_argument('--type', type=str, help='VCS Credential type: git')
    vcs_edit_parser.add_argument('--uri', type=str,
                                 help='VCS Credential URI. For example: git@github.com:legion-platform/legion.git')
    vcs_edit_parser.add_argument('--default-reference', type=str, help='Git reference: commit, branch ot tag')
    vcs_edit_parser.add_argument('--credential', type=str, help='GIT SSH key')
    vcs_edit_parser.add_argument('--public-key', type=str, help='Server public key')
    vcs_edit_parser.add_argument('--filename', '-f', type=str, help='Filename to use to edit the VCSCredential. '
                                                                    'This option ignores other VCS parameters!')
    security.add_edi_arguments(vcs_edit_parser)
    vcs_edit_parser.set_defaults(func=edit)

    vcs_delete_parser = vcs_subparser.add_parser('delete', description='Get all VCSCredentials')
    vcs_delete_parser.add_argument('name', nargs='?', type=str, help='VCS Credential name')
    vcs_delete_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the VCSCredential. '
                                                                      'This option ignores other VCS parameters!')
    security.add_edi_arguments(vcs_delete_parser)
    vcs_delete_parser.set_defaults(func=delete)
