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
import os
import os.path

import yaml

from .data_models import *
from .constants import *


def get_model_manifest(model: str) -> LegionProjectManifest:
    """
    Extract model manifest from file to object

    :param model: path to unpacked model (folder)
    :type model: str
    :return: None
    """
    manifest_file = os.path.join(model, PROJECT_FILE)
    if not manifest_file:
        raise Exception(f'Can not find manifest file {manifest_file}')

    try:
        with open(manifest_file, 'r') as manifest_stream:
            data = yaml.load(manifest_stream)
    except yaml.YAMLError as yaml_error:
        raise Exception(f'Can not parse YAML file: {yaml_error}')

    try:
        return LegionProjectManifest(**data)
    except pydantic.ValidationError as valid_error:
        raise Exception(f'Legion manifest file is in incorrect format: {valid_error}')


def parse_resource_file(resource_file: str) -> PackagingK8SResource:
    """
    Extract resource information

    :param resource_file: path to resource file
    :type resource_file: str
    :return: PackagingK8SResource -- resource
    """
    try:
        with open(resource_file, 'r') as resource_file_stream:
            data = yaml.load(resource_file_stream)
    except yaml.YAMLError as yaml_error:
        raise Exception(f'Can not parse YAML file: {yaml_error}')

    try:
        return PackagingK8SResource(**data)
    except pydantic.ValidationError as valid_error:
        raise Exception(f'Legion resource file is in incorrect format: {valid_error}')


def extract_connection_from_resource(resource: PackagingResource,
                                     connection_name: str) -> typing.Optional[PackagingResourceConnection]:
    """
    Extract connection by name

    :param resource: parsed resource
    :type resource: PackagingResource
    :param connection_name: name of connection
    :type connection_name: str
    :return: typing.Optional[PackagingResourceConnection] -- connection
    """
    for connection in resource.targets:
        if connection.name == connection_name:
            return connection
    return None


def validate_model_manifest(manifest: LegionProjectManifest) -> None:
    """
    Check that provided Legion Project Manifest is valid for current packer.

    :param manifest: Manifest object
    :type manifest: :py:class:`LegionProjectManifest`
    :raises Exception: If error in Manifest object is present
    :return: None
    """
    if manifest.binaries.type != 'python':
        raise Exception(f'Unsupported model binaries type: {manifest.binaries.type}')

    if manifest.binaries.dependencies != 'conda':
        raise Exception(f'Unsupported model dependencies type: {manifest.binaries.dependencies}')

    if not manifest.model:
        raise Exception('Model section is not set')

    if not manifest.legionVersion:
        raise Exception('legionVersion is not set')

    if not manifest.binaries.conda_path:
        raise Exception('Conda path is not set')
