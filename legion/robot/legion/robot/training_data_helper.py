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
This module helps to test a downloading of a training data
"""
import json
import os
from os.path import join
from shutil import copyfile
from typing import Dict

import click
import yaml
from legion.sdk.models import K8sTrainer

INPUT_FILE_LOCATION = "input-file-location"
TARGET_FILE_LOCATION = "target-file-location"


def parse_model_training_entity(source_file: str) -> K8sTrainer:
    """
    Parse model training file
    """
    # Validate resource file exist
    if not os.path.exists(source_file) or not os.path.isfile(source_file):
        raise ValueError(f'File {source_file} is not readable')

    with open(source_file, 'r') as mt_file:
        mt = mt_file.read()

        try:
            mt = json.loads(mt)
        except json.JSONDecodeError:
            try:
                mt = yaml.safe_load(mt)
            except json.JSONDecodeError as decode_error:
                raise ValueError(f'Cannot decode ModelTraining resource file: {decode_error}')

    return K8sTrainer.from_dict(mt)


@click.command()
@click.option("--verbose", action='store_true', help="more extensive logging")
@click.option("--mt-file", '--mt', type=str, required=True,
              help="json/yaml file with a mode training resource")
@click.option("--target", type=str, default='mlflow_output',
              help="directory where result model will be saved")
def main(verbose: str, mt_file: str, target: str) -> None:  # pylint: disable=W0613
    """
    Move training data to zip model artifact

    \f
    :param verbose: more extensive logging
    :param mt_file: json/yaml file with a mode training resource
    :param target: directory where result model will be saved
    """
    k8s_trainer = parse_model_training_entity(mt_file)
    parameters: Dict[str, str] = k8s_trainer.model_training.spec.hyper_parameters

    copyfile(parameters[INPUT_FILE_LOCATION], parameters[join(target, TARGET_FILE_LOCATION)])

    click.echo("Files were copied!")
