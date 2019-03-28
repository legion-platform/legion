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

from legion.sdk import config
from legion.sdk.k8s import properties
from legion.sdk.utils import extract_archive_item, model_properties_storage_name

LOGGER = logging.getLogger(__name__)

ZIP_COMPRESSION = zipfile.ZIP_STORED
ZIP_FILE_MODEL = 'model'
ZIP_FILE_INFO = 'manifest.json'
ZIP_FILE_PROPERTIES = 'properties'
ZIP_FILE_CALLBACK = 'callback'

PROPERTY_MODEL_ID = 'model.id'
PROPERTY_MODEL_VERSION = 'model.version'
PROPERTY_ENDPOINT_NAMES = 'model.endpoints'
PROPERTY_REQUIRED_PROPERTIES = 'model.required_properties'
PROPERTY_PROPERTIES_CALLBACK_EXISTS = 'mode.properties_callback_exists'


class ModelMeta:
    def __init__(self, model_id: str, model_version: str,
                 meta_information: typing.Dict[str, typing.Any] = None,
                 data_properties: typing.Dict[str, typing.Any] = None):
        """
        Build model meta

        :param model_id: model ID
        :param model_version: model version
        """
        if meta_information is None:
            meta_information = {}

        self._meta_information = meta_information

        self._model_id = model_id
        self._model_version = model_version

        storage_name = model_properties_storage_name(model_id, model_version)
        self._required_properties = []
        self._properties = properties.K8SConfigMapStorage(storage_name, cache_ttl=config.MODEL_PROPERTIES_CACHE_TTL)

        if data_properties:
            self._properties.data = data_properties

    @property
    def model_id(self) -> str:
        """
        Get model id

        :return: model id
        """
        return self._model_id

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

    @property
    def properties(self):
        """
        Get model properties

        :return: :py:class:`legion.k8s.K8SConfigMapStorage` -- model properties storage
        """
        return self._properties


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

    LOGGER.debug('Loading properties from {}'.format(ZIP_FILE_PROPERTIES))
    with extract_archive_item(path, ZIP_FILE_PROPERTIES) as properties_path:
        with open(properties_path, 'r') as properties_file:
            data_properties = json.load(properties_file)

    model_id = meta_information[PROPERTY_MODEL_ID]
    model_version = meta_information[PROPERTY_MODEL_VERSION]

    LOGGER.debug('Loading has been finished')

    return ModelMeta(model_id, model_version, meta_information, data_properties)
