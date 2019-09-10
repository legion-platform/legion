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
import json
import os.path
import typing

import pydantic
import yaml

from legion.packager.rest.constants import PROJECT_FILE, RESULT_FILE_NAME, DOCKER_IMAGE_RESULT
from legion.packager.rest.data_models import LegionProjectManifest
from legion.sdk.models import K8sPackager, Connection


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

    with open(manifest_file, 'r') as manifest_stream:
        data = manifest_stream.read()

        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(data)
            except yaml.YAMLError as decode_error:
                raise ValueError(f'Cannot decode ModelPacking resource file: {decode_error}')

    try:
        return LegionProjectManifest(**data)
    except pydantic.ValidationError as valid_error:
        raise Exception(f'Legion manifest file is in incorrect format: {valid_error}')


def parse_resource_file(resource_file: str) -> K8sPackager:
    """
    Extract resource information

    :param resource_file: path to resource file
    :type resource_file: str
    :return: PackagingK8SResource -- resource
    """
    with open(resource_file, 'r') as resource_file_stream:
        data = resource_file_stream.read()

        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(data)
            except yaml.YAMLError as decode_error:
                raise ValueError(f'Cannot decode Connection resource file: {decode_error}')

    try:
        return K8sPackager.from_dict(data)
    except pydantic.ValidationError as valid_error:
        raise Exception(f'Legion resource file is in incorrect format: {valid_error}')


def extract_connection_from_resource(k8s_packager: K8sPackager,
                                     connection_purpose: str) -> typing.Optional[Connection]:
    """
    Extract connection by name

    :param k8s_packager: parsed resource
    :param connection_purpose: name of connection
    :return: connection
    """
    for target in k8s_packager.targets:
        if target.name == connection_purpose:
            return target.connection
    return None


def validate_model_manifest(manifest: LegionProjectManifest) -> None:
    """
    Check that provided Legion Project Manifest is valid for current packager.

    :param manifest: Manifest object
    :raises Exception: If error in Manifest object is present
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


def save_result(remote_image_name: str):
    with open(RESULT_FILE_NAME, 'w') as fp:
        json.dump({DOCKER_IMAGE_RESULT: remote_image_name}, fp)
