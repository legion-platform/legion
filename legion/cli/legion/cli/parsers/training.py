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

from http.client import HTTPException

from requests import RequestException
from texttable import Texttable

from legion.cli.parsers import security, prepare_resources, add_resources_params, print_training_logs
from legion.sdk.clients import edi
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.clients.training import build_client, ModelTraining, ModelTrainingClient, TRAINING_SUCCESS_STATE, \
    TRAINING_FAILED_STATE

DEFAULT_WIDTH = 240
DEFAULT_WAIT_TIMEOUT = 1
MT_HEADER = ["Name", "State", "Toolchain Type", "Entrypoint", "Arguments", "VCS Credential", "Reference",
             "Model ID", "Model Version", "Trained Docker image"]

LOGGER = logging.getLogger(__name__)

INSPECT_FORMAT_COLORIZED = 'colorized'
INSPECT_FORMAT_TABULAR = 'column'
VALID_INSPECT_FORMATS = INSPECT_FORMAT_COLORIZED, INSPECT_FORMAT_TABULAR


def _convert_mt_from_args(args: argparse.Namespace) -> ModelTraining:
    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename).resource
        if not isinstance(resource, ModelTraining):
            raise ValueError(f'ModelTraining expected, but {type(resource)} provided')
        return resource
    elif args.name:
        return ModelTraining(
            name=args.name,
            toolchain_type=args.toolchain_type,
            entrypoint=args.entrypoint,
            resources=prepare_resources(args),
            args=args.arg,
            vcs_name=args.vcs_name,
            reference=args.reference,
            work_dir=args.workdir
        )
    else:
        raise ValueError(f'Provide name of a Model Training or path to a file')


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
        mt.model_version,
        mt.trained_image
    ] for mt in mt_credentials])
    print(table.draw() + "\n")


def create(args: argparse.Namespace):
    """
    Create a Model Training
    :param args: cli parameters
    """
    mt_client = build_client(args)

    mt = _convert_mt_from_args(args)
    mt_client.create(mt)

    wait_training_finish(args, mt.name, mt_client)


def logs(args: argparse.Namespace):
    """
    Stream training logs
    :param args: cli parameters
    """
    mt_client = build_client(args)

    for msg in mt_client.log(args.name, args.follow):
        print_training_logs(msg)


def edit(args: argparse.Namespace):
    """
    Edit a Model Training by name
    :param args: cli parameters
    """
    mt_client = build_client(args)

    mt = _convert_mt_from_args(args)
    message = mt_client.edit(mt)

    wait_training_finish(args, mt.name, mt_client)

    print(message)


def delete(args: argparse.Namespace):
    """
    Delete a Model Training by name
    :param args: cli parameters
    """
    mt_client = build_client(args)

    if not args.name and not args.filename:
        raise ValueError(f'Provide name of a Model Training or path to a file')

    if args.filename:
        resource = parse_resources_file_with_one_item(args.filename)
        if not isinstance(resource.resource, ModelTraining):
            raise ValueError(f'ModelTraining expected, but {type(resource.resource)} provided')
        mt_name = resource.resource_name
    else:
        mt_name = args.name

    message = mt_client.delete(mt_name)
    print(message)


def wait_training_finish(args: argparse.Namespace, mt_name: str, mt_client: ModelTrainingClient):
    """
    Wait training to finish according command line arguments

    :param mt_name: Model Training name
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
            mt = mt_client.get(mt_name)
            if mt.state == TRAINING_SUCCESS_STATE:
                print(f'Model {mt_name} was trained. Training took {round(time.time() - start)} seconds')
                return
            elif mt.state == TRAINING_FAILED_STATE:
                raise Exception(f'Model training {mt_name} was failed.')
            elif mt.state == "":
                print(f"Can't determine the state of {mt.name}. Sleeping...")
            else:
                for msg in mt_client.log(mt.name, follow=True):
                    print_training_logs(msg)

        except (WrongHttpStatusCode, HTTPException, RequestException) as e:
            LOGGER.info('Callback have not confirmed completion of the operation. Exception: %s', str(e))

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
    mt_create_parser.add_argument('name', nargs='?', type=str, help='Model Training name')
    mt_create_parser.add_argument('--toolchain-type', '--toolchain', type=str, help='Toolchain types: legion or python')
    mt_create_parser.add_argument('--entrypoint', '-e', type=str, help='Model training file. It can be python\\bash'
                                                                       ' script or jupiter notebook')
    mt_create_parser.add_argument('--arg', '-a', action='append', help='Parameter for entrypoint script')
    mt_create_parser.add_argument('--vcs-name', '--vcs', type=str, help='Name of VCSCredential resource')
    mt_create_parser.add_argument('--workdir', type=str, help='Directory with model scripts/files in a git repository')
    mt_create_parser.add_argument('--reference', type=str, help='Commit\\tag\\branch name')
    mt_create_parser.add_argument('--filename', '-f', type=str, help='Filename to use to create the Model Training')
    add_resources_params(mt_create_parser)
    edi.add_arguments_for_wait_operation(mt_create_parser)
    security.add_edi_arguments(mt_create_parser)
    mt_create_parser.set_defaults(func=create)

    mt_edit_parser = mt_subparser.add_parser('edit', description='Get all ModelTrainings')
    mt_edit_parser.add_argument('name', nargs='?', type=str, help='Model Training name')
    mt_edit_parser.add_argument('--toolchain-type', '--toolchain', type=str, help='Toolchain types: legion or python')
    mt_edit_parser.add_argument('--entrypoint', '-e', type=str, help='Model training file. It can be python\\bash'
                                                                     ' script or jupiter notebook')
    mt_edit_parser.add_argument('--arg', '-a', action='append', help='Parameter for entrypoint script')
    mt_edit_parser.add_argument('--vcs-name', '--vcs', type=str, help='Name of VCSCredential resource')
    mt_edit_parser.add_argument('--workdir', type=str, help='Directory with model scripts/files in a git repository')
    mt_edit_parser.add_argument('--reference', type=str, help='Commit\\tag\\branch name')
    mt_edit_parser.add_argument('--filename', '-f', type=str, help='Filename to use to edit the Model Training')
    add_resources_params(mt_edit_parser)
    security.add_edi_arguments(mt_edit_parser)
    edi.add_arguments_for_wait_operation(mt_edit_parser)
    mt_edit_parser.set_defaults(func=edit)

    mt_delete_parser = mt_subparser.add_parser('delete', description='Get all ModelTrainings')
    mt_delete_parser.add_argument('name', nargs='?', type=str, help='Model Training name', default="")
    mt_delete_parser.add_argument('--filename', '-f', type=str, help='Filename to use to delete the Model Training')
    security.add_edi_arguments(mt_delete_parser)
    mt_delete_parser.set_defaults(func=delete)

    mt_log_parser = mt_subparser.add_parser('logs', description='Stream training logs')
    mt_log_parser.add_argument('name', type=str, help='Model Training name', default="")
    mt_log_parser.add_argument('--follow', '-f', action='store_true', help='Follow logs stream')
    security.add_edi_arguments(mt_log_parser)
    mt_log_parser.set_defaults(func=logs)
