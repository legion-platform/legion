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
Training commands for legion cli
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
from legion.sdk.clients.edi import WrongHttpStatusCode
from legion.sdk.clients.edi_aggregated import parse_resources_file_with_one_item
from legion.sdk.clients.training import ModelTraining, ModelTrainingClient, TRAINING_SUCCESS_STATE, \
    TRAINING_FAILED_STATE

DEFAULT_WAIT_TIMEOUT = 3
LOG_READ_TIMEOUT_SECONDS = 60

LOGGER = logging.getLogger(__name__)


@click.group()
@click.option('--edi', help='EDI server host', default=config.EDI_URL)
@click.option('--token', help='EDI server jwt token', default=config.EDI_TOKEN)
@click.pass_context
def training(ctx: click.core.Context, edi: str, token: str):
    """
    Allow you to perform actions on trainings
    """
    ctx.obj = ModelTrainingClient(edi, token)


@training.command()
@click.option('--train-id', '--id', help='Model training ID')
@click.option('--output-format', '-o', 'output_format', help='Output format',
              default=DEFAULT_OUTPUT_FORMAT)
@pass_obj
def get(client: ModelTrainingClient, train_id: str, output_format: str):
    """
    Get trainings.\n
    The command without id argument retrieve all trainings.\n
    Get all trainings in json format:\n
        legionctl train get --format json\n
    Get training with "git-repo" id:\n
        legionctl train get --id git-repo\n
    Using jsonpath:\n
        legionctl train get -o 'jsonpath=[*].spec.reference'
    \f
    :param client: Model training HTTP client
    :param train_id: Model training ID
    :param output_format: Output format
    :return:
    """
    trains = [client.get(train_id)] if train_id else client.get_all()

    format_output(trains, output_format)


@training.command()
@click.option('--train-id', '--id', help='Model training ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with training')
@click.option('--wait/--no-wait', default=True,
              help='no wait until scale will be finished')
@click.option('--timeout', default=1200, type=int,
              help='timeout in seconds. for wait (if no-wait is off)')
@pass_obj
def create(client: ModelTrainingClient, train_id: str, file: str, wait: bool, timeout: int):
    """
    Create a training.\n
    You should specify a path to file with a training. The file must contain only one training.
    For now, CLI supports yaml and JSON file formats.
    If you want to create multiples trainings than you should use "legionctl res apply" instead.
    If you provide the training id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl train create -f train.yaml --id examples-git
    \f
    :param timeout: timeout in seconds. for wait (if no-wait is off)
    :param wait: no wait until scale will be finished
    :param client: Model training HTTP client
    :param train_id: Model training ID
    :param file: Path to the file with only one training
    """
    train = parse_resources_file_with_one_item(file).resource
    if not isinstance(train, ModelTraining):
        raise ValueError(f'Model training expected, but {type(train)} provided')

    if train_id:
        train.id = train_id

    train = client.create(train)
    click.echo(f"Start training: {train}")

    wait_training_finish(timeout, wait, train.id, client)


@training.command()
@click.option('--train-id', '--id', help='Model training ID')
@click.option('--file', '-f', type=click.Path(), required=True, help='Path to the file with training')
@click.option('--wait/--no-wait', default=True,
              help='no wait until scale will be finished')
@click.option('--timeout', default=1200, type=int,
              help='timeout in seconds. for wait (if no-wait is off)')
@pass_obj
def edit(client: ModelTrainingClient, train_id: str, file: str, wait: bool, timeout: int):
    """
    Rerun a training.\n
    You should specify a path to file with a training. The file must contain only one training.
    For now, CLI supports yaml and JSON file formats.
    If you want to update multiples trainings than you should use "legionctl res apply" instead.
    If you provide the training id parameter than it will be overridden before sending to EDI server.\n
    Usage example:\n
        * legionctl train update -f train.yaml --id examples-git
    \f
    :param client: Model training HTTP client
    :param train_id: Model training ID
    :param file: Path to the file with only one training
    :param timeout: timeout in seconds. for wait (if no-wait is off)
    :param wait: no wait until scale will be finished
    """
    train = parse_resources_file_with_one_item(file).resource
    if not isinstance(train, ModelTraining):
        raise ValueError(f'Model training expected, but {type(train)} provided')

    if train_id:
        train.id = train_id

    train = client.edit(train)
    click.echo(f"Rerun training: {train}")

    wait_training_finish(timeout, wait, train.id, client)


@training.command()
@click.option('--train-id', '--id', help='Model training ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with training')
@click.option('--ignore-not-found/--not-ignore-not-found', default=False,
              help='ignore if Model Training is not found')
@pass_obj
def delete(client: ModelTrainingClient, train_id: str, file: str, ignore_not_found: bool):
    """
    Delete a training.\n
    For this command, you must provide a training ID or path to file with one training.
    The file must contain only one training.
    If you want to delete multiples trainings than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl train delete --id examples-git\n
        * legionctl train delete -f train.yaml
    \f
    :param client: Model training HTTP client
    :param train_id: Model training ID
    :param file: Path to the file with only one training
    :param ignore_not_found: ignore if Model Training is not found
    """
    if not train_id and not file:
        raise ValueError(f'You should provide a training ID or file parameter, not both.')

    if train_id and file:
        raise ValueError(f'You should provide a training ID or file parameter, not both.')

    if file:
        train = parse_resources_file_with_one_item(file).resource
        if not isinstance(train, ModelTraining):
            raise ValueError(f'Model training expected, but {type(train)} provided')

        train_id = train.id

    try:
        message = client.delete(train_id)
        click.echo(message)
    except WrongHttpStatusCode as e:
        if e.status_code != 404 or not ignore_not_found:
            raise e

        click.echo(f'Model training {train_id} was not found. Ignore')


@training.command()
@click.option('--train-id', '--id', help='Model training ID')
@click.option('--file', '-f', type=click.Path(), help='Path to the file with training')
@click.option('--follow/--not-follow', default=True,
              help='Follow logs stream')
@pass_obj
def logs(client: ModelTrainingClient, train_id: str, file: str, follow: bool):
    """
    Stream training logs.\n
    For this command, you must provide a training ID or path to file with one training.
    The file must contain only one training.
    If you want to delete multiples trainings than you should use "legionctl res delete" instead.
    For now, CLI supports yaml and JSON file formats.
    The command will be failed if you provide both arguments.\n
    Usage example:\n
        * legionctl train delete --id examples-git\n
        * legionctl train delete -f train.yaml
    \f
    :param follow: Follow logs stream
    :param client: Model training HTTP client
    :param train_id: Model training ID
    :param file: Path to the file with only one training
    """
    if not train_id and not file:
        raise ValueError(f'You should provide a training ID or file parameter, not both.')

    if train_id and file:
        raise ValueError(f'You should provide a training ID or file parameter, not both.')

    if file:
        train = parse_resources_file_with_one_item(file).resource
        if not isinstance(train, ModelTraining):
            raise ValueError(f'Model training expected, but {type(train)} provided')

        train_id = train.id

    for msg in client.log(train_id, follow):
        print_logs(msg)


def wait_training_finish(timeout: int, wait: bool, mt_id: str, mt_client: ModelTrainingClient):
    """
    Wait training to finish according command line arguments

    :param wait:
    :param timeout:
    :param mt_id: Model Training name
    :param mt_client: Model Training Client
    """
    if not wait:
        return

    start = time.time()
    if timeout <= 0:
        raise Exception('Invalid --timeout argument: should be positive integer')

    # We create a separate client for logs because it has the different timeout settings
    log_mt_client = ModelTrainingClient.construct_from_other(mt_client)
    log_mt_client.timeout = mt_client.timeout, LOG_READ_TIMEOUT_SECONDS

    click.echo("Logs streaming...")

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise Exception('Time out: operation has not been confirmed')

        try:
            mt = mt_client.get(mt_id)
            if mt.status.state == TRAINING_SUCCESS_STATE:
                click.echo(f'Model {mt_id} was trained. Training took {round(time.time() - start)} seconds')
                return
            elif mt.status.state == TRAINING_FAILED_STATE:
                raise Exception(f'Model training {mt_id} was failed.')
            elif mt.status.state == "":
                click.echo(f"Can't determine the state of {mt.id}. Sleeping...")
            else:
                for msg in log_mt_client.log(mt.id, follow=True):
                    print_logs(msg)

        except (WrongHttpStatusCode, HTTPException, RequestException) as e:
            LOGGER.info('Callback have not confirmed completion of the operation. Exception: %s', str(e))

        LOGGER.debug('Sleep before next request')
        time.sleep(DEFAULT_WAIT_TIMEOUT)
