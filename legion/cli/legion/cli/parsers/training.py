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
from legion.sdk.clients.training import build_client, ModelTraining, ModelTrainingClient, TRAINING_SUCCESS_STATE, \
    TRAINING_FAILED_STATE

DEFAULT_WIDTH = 120

DEFAULT_WAIT_TIMEOUT = 5

MT_HEADER = ["Name", "State", "Toolchain Type", "Entrypoint", "Arguments", "VCS Credential", "Reference",
             "Model ID", "Model Version"]

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def get(args: argparse.Namespace):
    """
    Get all of Model Trainings or by name
    :param args: cli parameters
    """
    mt_client = build_client(args)

    mt_credentials = [mt_client.get(args.name)] if args.name else mt_client.get_all()

    table = Texttable(max_width=DEFAULT_WIDTH)
    table.set_cols_align("c" * len(MT_HEADER))
    table.set_cols_valign("t" * len(MT_HEADER))
    table.add_rows([MT_HEADER] + [[
        mt.name,
        mt.state,
        mt.toolchain_type,
        mt.entrypoint,
        mt.args,
        mt.vcs_name,
        mt.reference,
        mt.model_id,
        mt.model_version
    ] for mt in mt_credentials])
    print(table.draw() + "\n")


def create(args: argparse.Namespace):
    """
    Create a Model Training
    :param args: cli parameters
    """
    mt_client = build_client(args)

    message = mt_client.create(ModelTraining(
        name=args.name,
        toolchain_type=args.toolchain_type,
        entrypoint=args.entrypoint,
        args=args.arg,
        vcs_name=args.vcs_name,
        reference=args.reference
    ))

    wait_training_finish(args, mt_client)

    print(message)


def edit(args: argparse.Namespace):
    """
    Edit a Model Training by name
    :param args: cli parameters
    """
    mt_client = build_client(args)

    message = mt_client.edit(ModelTraining(
        name=args.name,
        toolchain_type=args.toolchain_type,
        entrypoint=args.entrypoint,
        args=args.arg,
        vcs_name=args.vcs_name,
        reference=args.reference
    ))

    print(message)


def delete(args: argparse.Namespace):
    """
    Delete a Model Training by name
    :param args: cli parameters
    """
    mt_client = build_client(args)

    message = mt_client.delete(args.name)

    print(message)


def wait_training_finish(args: argparse.Namespace, mt_client: ModelTrainingClient):
    """
    Wait training to finish according command line arguments

    :param args: command arguments with .model_id, .namespace
    :param mt_client: Model Training Client

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
            mt = mt_client.get(args.name)
            if mt.state == TRAINING_SUCCESS_STATE:
                print(f'Model {args.name} was trained. Training took {round(time.time() - start)} seconds')
                return
            elif mt.state == TRAINING_FAILED_STATE:
                raise Exception(f'Model training {args.name} was failed.')

            print(f'Current training state is {mt.state}. Sleeping...')

        except WrongHttpStatusCode:
            LOGGER.info('Callback have not confirmed completion of the operation')

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    mt_subparser = main_subparser.add_parser('model-training', aliases=('mt', 'training'),
                                             description='Model Training manipulations').add_subparsers()

    mt_get_parser = mt_subparser.add_parser('get', description='Get all ModelTrainings or by name')
    mt_get_parser.add_argument('name', type=str, nargs='?', help='Model Training name', default="")
    security.add_edi_arguments(mt_get_parser)
    mt_get_parser.set_defaults(func=get)

    mt_create_parser = mt_subparser.add_parser('create', description='Create a ModelTraining')
    mt_create_parser.add_argument('name', type=str, help='Model Training name')
    mt_create_parser.add_argument('--toolchain-type', '--toolchain', type=str, help='Toolchain types: legion or python',
                                  required=True)
    mt_create_parser.add_argument('--entrypoint', '-e', type=str, help='Model Training name', required=True)
    mt_create_parser.add_argument('--arg', '-a', action='append', help='Model Training name')
    mt_create_parser.add_argument('--vcs-name', '--vcs', type=str, help='Model Training name', required=True)
    mt_create_parser.add_argument('--reference', type=str, help='Model Training name')
    edi.add_arguments_for_wait_operation(mt_create_parser)
    security.add_edi_arguments(mt_create_parser)
    mt_create_parser.set_defaults(func=create)

    mt_edit_parser = mt_subparser.add_parser('edit', description='Get all ModelTrainings')
    mt_edit_parser.add_argument('name', type=str, help='Model Training name')
    mt_edit_parser.add_argument('--toolchain-type', '--toolchain', type=str, help='Model Training name', required=True)
    mt_edit_parser.add_argument('--entrypoint', type=str, help='Model Training name', required=True)
    mt_edit_parser.add_argument('--arg', '-a', action='append', help='Model Training name')
    mt_edit_parser.add_argument('--vcs-name', '--vcs', type=str, help='Model Training name', required=True)
    mt_edit_parser.add_argument('--reference', type=str, help='Model Training name')
    security.add_edi_arguments(mt_edit_parser)
    mt_edit_parser.set_defaults(func=edit)

    mt_delete_parser = mt_subparser.add_parser('delete', description='Get all ModelTrainings')
    mt_delete_parser.add_argument('name', type=str, help='Model Training name')
    security.add_edi_arguments(mt_delete_parser)
    mt_delete_parser.set_defaults(func=delete)
