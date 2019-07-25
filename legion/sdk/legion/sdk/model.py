#
#    Copyright 2018 EPAM Systems
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
Python model
"""
import json
import logging
import typing
import zipfile

from legion.sdk.utils import extract_archive_item

LOGGER = logging.getLogger(__name__)

ZIP_COMPRESSION = zipfile.ZIP_STORED
ZIP_FILE_MODEL = 'model'
ZIP_FILE_INFO = 'manifest.json'

PROPERTY_MODEL_NAME = 'model.name'
PROPERTY_MODEL_VERSION = 'model.version'
PROPERTY_ENDPOINT_NAMES = 'model.endpoints'
PROPERTY_TRAINING_WORKING_DIRECTORY = 'model.trainWorkDir'


class ModelMeta:
    def __init__(self,
                 model_name: str,
                 model_version: str,
                 meta_information: typing.Dict[str, typing.Any] = None):
        """
        Build model meta

        :param model_name: model name
        :param model_version: model version
        :param meta_information: model meta information
        """
        if meta_information is None:
            meta_information = {}

        self._meta_information = meta_information

        self._model_name = model_name
        self._model_version = model_version

    @property
    def model_name(self) -> str:
        """
        Get model name

        :return: model name
        """
        return self._model_name

    @property
    def model_version(self) -> str:
        """
        Get model version

        :return: model version
        """
        return self._model_version

    @property
    def meta_information(self) -> typing.Dict[str, typing.Any]:
        """
        Get copy of meta information

        :return: dict -- copy of meta information
        """
        return self._meta_information.copy()


def load_meta_model(path: str) -> ModelMeta:
    """
    Populate model metadata

    :param path: path to model binary
    :return: None
    """
    LOGGER.debug('Loading metadata from {}'.format(ZIP_FILE_INFO))
    with extract_archive_item(path, ZIP_FILE_INFO) as manifest_path:
        with open(manifest_path, 'r') as manifest_file:
            meta_information = json.load(manifest_file)

    model_name = meta_information[PROPERTY_MODEL_NAME]
    model_version = meta_information[PROPERTY_MODEL_VERSION]

    LOGGER.debug('Loading has been finished')

    return ModelMeta(model_name, model_version, meta_information)
