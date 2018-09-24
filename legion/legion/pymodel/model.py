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
import sys
import os
import time
import zipfile

import logging
import legion.config
import legion.containers.headers
import legion.model
import legion.k8s.properties
import legion.model.types
import legion.metrics
from legion.utils import model_properties_storage_name, send_header_to_stderr, \
    extract_archive_item, TemporaryFolder, deduce_model_file_name, save_file


import dill


LOGGER = logging.getLogger(__name__)


class ModelEndpoint:
    """
    Object describes named model invocation endpoint
    """

    def __init__(self, *, name, apply, column_types, prepare, use_df):
        """
        Build model endpoint

        :param name: endpoint name
        :type name: str
        :param apply: apply function (callable object)
        :type apply: callable
        :param column_types: (Optional) column types dictionary
        :type column_types: dict[str, ColumnInformation]
        :param prepare: (Optional) prepare function (callable object)
        :type prepare: callable
        :param use_df: use db for prepare function
        :type use_df: bool
        """
        self._name = name
        self._apply = apply
        self._column_types = column_types
        self._prepare = prepare
        self._use_df = use_df

    @property
    def description(self):
        """
        Get model description

        :return: dict[str, any] -- dict with model description
        """
        data = {
            'name': self.name,
            'use_df': self.use_df
        }

        if self.column_types:
            data['input_params'] = {k: v.description_for_api for (k, v) in self.column_types.items()}
        else:
            data['input_params'] = False

        return data

    def invoke(self, input_vector):
        """
        Calculate result of model execution

        :param input_vector: input data
        :type input_vector: dict[str, union[str, Image]]
        :return: dict -- output data
        """
        LOGGER.info('Input vector: %r' % input_vector)
        data_frame = legion.model.types.build_df(self.column_types, input_vector, not self.use_df)

        LOGGER.info('Running prepare with DataFrame: %r' % data_frame)
        data_frame = self.prepare(data_frame)

        LOGGER.info('Applying function with DataFrame: %s' % str(data_frame))
        response = self.apply(data_frame)
        LOGGER.info('Returning response: %s' % str(response))

        return response

    @property
    def name(self):
        """
        Get endpoint name

        :return: str -- name of endpoint
        """
        return self._name

    @property
    def apply(self):
        """
        Get apply function

        :return: function
        """
        return self._apply

    @property
    def column_types(self):
        """
        Get column types

        :return:
        """
        return self._column_types

    @property
    def prepare(self):
        """
        Get prepare function

        :return:
        """
        return self._prepare

    @property
    def use_df(self):
        """
        Use pandas DataFrame for input parameters

        :return: bool -- use DataFrame
        """
        return self._use_df

    def __str__(self):
        """
        Get string representation

        :return: str -- string representation
        """
        return 'ModelEndpoint for endpoint {}'.format(self.name)

    __repr__ = __str__


class Model:
    NAME = 'pymodel'

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

    def __init__(self, model_id, model_version):
        """
        Build empty model container

        :param model_id: model ID
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        """
        self._meta_information = {}  # type: dict

        self._model_id = model_id
        self._model_version = model_version

        self._required_properties = []

        self._endpoints = {}  # type: dict or None
        self._path = None  # type: str or None

        self._on_property_change_callback = None  # type: typing.Callable[[], None] or None
        self._on_property_change_callback_loaded = False  # type: bool

        storage_name = model_properties_storage_name(self.model_id, self.model_version)
        self._properties = legion.k8s.K8SConfigMapStorage(storage_name,
                                                          cache_ttl=legion.config.MODEL_PROPERTIES_CACHE_TTL)

        LOGGER.info('Setting properties change callback getter to local function {!r} (id: {})'.format(
            self.get_on_property_change_callback,
            id(self.get_on_property_change_callback)
        ))

        self._properties.set_change_callback(self.get_on_property_change_callback)

        send_header_to_stderr(legion.containers.headers.MODEL_ID, self.model_id)
        send_header_to_stderr(legion.containers.headers.MODEL_VERSION, self.model_version)

    @property
    def properties(self):
        """
        Get model properties

        :return: :py:class:`legion.k8s.K8SConfigMapStorage` -- model properties storage
        """
        return self._properties

    def _load_from_archive(self, path):
        """
        Populate model container with data from file after initialization

        :param path: path to model binary
        :type path: str
        :return: None
        """
        self._path = path
        self._endpoints = None
        self._on_property_change_callback_loaded = False
        LOGGER.info('Loading model from {}'.format(path))

        LOGGER.debug('Loading metadata from {}'.format(Model.ZIP_FILE_INFO))
        with extract_archive_item(path, Model.ZIP_FILE_INFO) as manifest_path:
            with open(manifest_path, 'r') as manifest_file:
                self._meta_information = json.load(manifest_file)

        self._required_properties = self._meta_information[self.PROPERTY_REQUIRED_PROPERTIES]

        LOGGER.debug('Loading properties from {}'.format(Model.ZIP_FILE_PROPERTIES))
        with extract_archive_item(path, Model.ZIP_FILE_PROPERTIES) as properties_path:
            with open(properties_path, 'r') as properties_file:
                self.properties.data = json.load(properties_file)

        LOGGER.debug('Loading has been finished')

    @staticmethod
    def load(path):
        """
        Populate model container with data from file and initialize

        :param path: path to model binary
        :type path: str
        :return: :py:class:`legion.pymodel.model.Model` -- model container
        """
        if not os.path.exists(path):
            raise Exception('File not existed: {}'.format(path))

        with extract_archive_item(path, Model.ZIP_FILE_INFO) as manifest_path:
            with open(manifest_path, 'r') as manifest_file:
                manifest_data = json.load(manifest_file)

                model_id = manifest_data[Model.PROPERTY_MODEL_ID]
                model_version = manifest_data[Model.PROPERTY_MODEL_VERSION]

        instance = Model(model_id, model_version)
        instance._load_from_archive(path)

        return instance

    @staticmethod
    def _build_endpoint_file_name(endpoint_name):
        """
        Build name of endpoint file in model binary

        :param endpoint_name: endpoint name
        :type endpoint_name: str
        :return: inner path to file
        :rtype: str
        """
        return endpoint_name

    def load_properties_change_callback(self):
        """
        Load properties change callback from binary

        :return: deserialized model properties change callback
        :rtype: :py:class:`typing.Callable[[], None]`
        """
        LOGGER.debug('Loading properties change callback')
        with extract_archive_item(self._path, self.ZIP_FILE_CALLBACK) as callback_path:
            with open(callback_path, 'rb') as callback_file:
                return dill.load(callback_file)

    def load_endpoint(self, endpoint_name):
        """
        Load endpoint from model binary

        :param endpoint_name: endpoint name
        :type endpoint_name: str
        :return: deserialized model endpoint
        :rtype: :py:class:`legion.pymodel.model.ModelEndpoint`
        """
        LOGGER.debug('Loading endpoint {}'.format(endpoint_name))
        with extract_archive_item(self._path, self._build_endpoint_file_name(endpoint_name)) as endpoint_path:
            with open(endpoint_path, 'rb') as endpoint_file:
                return dill.load(endpoint_file)

    @property
    def description(self):
        """
        Get model container description

        :return: dict[str, any] -- model description
        """
        return {
            'model_id': self.model_id,
            'model_version': self.model_version,
            'endpoints': {ep.name: ep.description for ep in self.endpoints.values()}
        }

    @property
    def endpoints(self):
        """
        Get or lazy load endpoints

        :return: dict -- current endpoints
        """
        # If endpoint is None it means that model in partial loaded state
        # (properties has been loaded, endpoints - not)
        if self._endpoints is None:
            self._endpoints = {}

            endpoint_names = self._meta_information.get(self.PROPERTY_ENDPOINT_NAMES)
            if not endpoint_names:
                raise Exception('PyModel does not contain {} field or field is empty'
                                .format(self.PROPERTY_ENDPOINT_NAMES))

            for endpoint_name in endpoint_names:
                self._endpoints[endpoint_name] = self.load_endpoint(endpoint_name)

        return self._endpoints

    def save(self, path=None):
        """
        Save model to path (or deduce path)

        :param path: (Optional) target save name
        :return: :py:class:`legion.pymodel.model.Model` -- model container
        """
        if not self.endpoints:
            raise ValueError('Cannot save empty model container (no one export function has been called)')
        properties_change_callback_exists = self.get_on_property_change_callback() is not None

        meta_information_to_save = self._meta_information.copy()
        meta_information_to_save.update(self._collect_build_info())

        # Add model id, model version, model endpoint
        meta_information_to_save[self.PROPERTY_MODEL_ID] = self.model_id
        meta_information_to_save[self.PROPERTY_MODEL_VERSION] = self.model_version
        meta_information_to_save[self.PROPERTY_ENDPOINT_NAMES] = list(self._endpoints.keys())
        meta_information_to_save[self.PROPERTY_REQUIRED_PROPERTIES] = list(self._required_properties)
        meta_information_to_save[self.PROPERTY_PROPERTIES_CALLBACK_EXISTS] = properties_change_callback_exists

        self._path = path

        file_name_has_been_deduced = False
        if not self._path:
            self._path = deduce_model_file_name(self.model_id, self.model_version)

        LOGGER.info('Saving model to {}'.format(self._path))

        # Save
        with TemporaryFolder('legion-model-save') as temp_directory:
            temp_file = os.path.join(temp_directory.path, 'result.zip')
            with zipfile.ZipFile(temp_file, 'w', self.ZIP_COMPRESSION) as stream:
                # Add manifest file
                LOGGER.debug('Saving manifest file to {}'.format(self.ZIP_FILE_INFO))
                with open(os.path.join(temp_directory.path, self.ZIP_FILE_INFO), 'w') as info_file:
                    json.dump(meta_information_to_save, info_file)
                stream.write(os.path.join(temp_directory.path, self.ZIP_FILE_INFO), self.ZIP_FILE_INFO)

                # Add current properties state
                LOGGER.debug('Saving current property values to {}'.format(self.ZIP_FILE_PROPERTIES))
                with open(os.path.join(temp_directory.path, self.ZIP_FILE_PROPERTIES), 'w') as props_file:
                    json.dump(legion.model.properties.data, props_file)
                stream.write(os.path.join(temp_directory.path, self.ZIP_FILE_PROPERTIES), self.ZIP_FILE_PROPERTIES)

                # Add callback file
                if properties_change_callback_exists:
                    LOGGER.debug('Saving property change callback to {}'.format(self.ZIP_FILE_CALLBACK))
                    with open(os.path.join(temp_directory.path, self.ZIP_FILE_CALLBACK), 'wb') as callback_file:
                        dill.dump(self.get_on_property_change_callback(), callback_file, recurse=True)
                    stream.write(os.path.join(temp_directory.path, self.ZIP_FILE_CALLBACK), self.ZIP_FILE_CALLBACK)

                # Add endpoints
                for endpoint in self.endpoints.values():
                    path = self._build_endpoint_file_name(endpoint.name)
                    LOGGER.debug('Saving endpoint {!r} to {}'.format(endpoint, path))
                    with open(os.path.join(temp_directory.path, path), 'wb') as endpoint_file:
                        dill.dump(endpoint, endpoint_file, recurse=True)
                    stream.write(os.path.join(temp_directory.path, path), path)

            result_path = save_file(temp_file, self._path)

        send_header_to_stderr(legion.containers.headers.MODEL_PATH, result_path)
        send_header_to_stderr(legion.containers.headers.SAVE_STATUS, 'OK')

        if file_name_has_been_deduced:
            print('Model has been saved to {}'.format(result_path), file=sys.stderr)

        return self

    def _export(self, apply_func, prepare_func, column_types, use_df, endpoint_name):
        """
        Export simple Pandas based model as a bundle

        :param apply_func: an apply function DF->DF
        :type apply_func: func(x) -> y
        :param prepare_func: a function to prepare input DF->DF
        :type prepare_func: func(x) -> y
        :param column_types: result of deduce_param_types or prepared column information or None
        :type column_types: dict[str, :py:class:`legion.model.types.ColumnInformation`] or None
        :param use_df: use pandas DF for prepare and apply function
        :type use_df: bool
        :param endpoint_name: name of endpoint
        :type endpoint_name: str
        :return: None
        """
        if not hasattr(apply_func, '__call__'):
            raise Exception('Provided non-callable object as apply_function')

        if column_types:
            if not isinstance(column_types, dict) \
                    or not column_types.keys() \
                    or not isinstance(list(column_types.values())[0], legion.model.types.ColumnInformation):
                raise Exception('Bad param_types / input_data_frame provided')

        if prepare_func is None:
            def prepare_func(input_dict):
                """
                Return input value (default prepare function)
                :param x: dict of values
                :return: dict of values
                """
                return input_dict

        if endpoint_name in self._endpoints:
            raise Exception('Endpoint {} already existed in endpoints'.format(endpoint_name))

        new_endpoint = ModelEndpoint(name=endpoint_name,
                                     apply=apply_func,
                                     column_types=column_types,
                                     prepare=prepare_func,
                                     use_df=use_df)

        self.endpoints[endpoint_name] = new_endpoint

    def export_df(self, apply_func, input_data_frame, *, prepare_func=None, endpoint='default'):
        """
        Export simple Pandas DF based model as a bundle

        :param apply_func: an apply function DF->DF
        :type apply_func: func(x) -> y
        :param input_data_frame: pandas DF
        :type input_data_frame: :py:class:`pandas.DataFrame`
        :param prepare_func: a function to prepare input DF->DF
        :type prepare_func: func(x) -> y
        :param endpoint: (Optional) endpoint name, default is 'default'
        :type endpoint: str
        :return: :py:class:`legion.pymodel.model.Model` -- model container
        """
        column_types = legion.model.types.get_column_types(input_data_frame)
        self._export(apply_func, prepare_func, column_types, True, endpoint)
        return self

    def export(self, apply_func, column_types, *, prepare_func=None, endpoint='default'):
        """
        Export simple parameters defined model as a bundle

        :param apply_func: an apply function DF->DF
        :type apply_func: func(x) -> y
        :param column_types: result of deduce_param_types or prepared column information
        :type column_types: dict[str, :py:class:`legion.model.types.ColumnInformation`]
        :param prepare_func: a function to prepare input DF->DF
        :type prepare_func: func(x) -> y
        :param endpoint: (Optional) endpoint name, default is 'default'
        :type endpoint: str
        :return: :py:class:`legion.pymodel.model.Model` -- model container
        """
        self._export(apply_func, prepare_func, column_types, False, endpoint)
        return self

    def export_untyped(self, apply_func, *, prepare_func=None, endpoint='default'):
        """
        Export simple untyped model as a bundle

        :param apply_func: an apply function DF->DF
        :type apply_func: func(x) -> y
        :param prepare_func: a function to prepare input DF->DF
        :type prepare_func: func(x) -> y
        :param endpoint: (Optional) endpoint name, default is 'default'
        :type endpoint: str
        :return: :py:class:`legion.pymodel.model.Model` -- model container
        """
        self._export(apply_func, prepare_func, None, False, endpoint)
        return self

    def get_on_property_change_callback(self):
        """
        Get or lazy load registered callback or empty callback

        :return: :py:class:`Callable[[], None]` -- callback function
        """
        # If property change callback loaded - return
        if not self._on_property_change_callback_loaded:
            callback_exists = self._meta_information.get(self.PROPERTY_PROPERTIES_CALLBACK_EXISTS)

            if not callback_exists:
                LOGGER.warning('Property change callback is empty - using lambda')
                self._on_property_change_callback = lambda: None
            else:
                self._on_property_change_callback = self.load_properties_change_callback()
            self._on_property_change_callback_loaded = True

        return self._on_property_change_callback

    def on_property_change(self, callable):
        """
        Set property change callback

        :param callback: callback which will be called on each property change
        :type callback: :py:class:`Callable[[], None]`
        :return: None
        """
        self._on_property_change_callback = callable
        self._on_property_change_callback_loaded = True

    @property
    def model_id(self):
        """
        Get model id

        :return: str or None -- model id
        """
        return self._model_id

    @property
    def model_version(self):
        """
        Get model version

        :return: str or None -- model version
        """
        return self._model_version

    @property
    def required_props(self):
        """
        Get model required props

        :return: list[str] -- list of required property names
        """
        return self._required_properties

    @property
    def meta_information(self):
        """
        Get copy of meta information

        :return: dict -- copy of meta information
        """
        return self._meta_information.copy()

    def _collect_build_info(self):
        """
        Get additional container properties for container

        :return: dict[str, any] -- additional container properties
        """
        return {
            'legion.version': legion.__version__,

            'jenkins.build_number': os.environ.get(*legion.config.BUILD_NUMBER),
            'jenkins.build_id': os.environ.get(*legion.config.BUILD_ID),
            'jenkins.build_tag': os.environ.get(*legion.config.BUILD_TAG),
            'jenkins.build_url': os.environ.get(*legion.config.BUILD_URL),

            'jenkins.git_commit': os.environ.get(*legion.config.GIT_COMMIT),
            'jenkins.git_branch': os.environ.get(*legion.config.GIT_BRANCH),

            'jenkins.node_name': os.environ.get(*legion.config.NODE_NAME),
            'jenkins.job_name': os.environ.get(*legion.config.JOB_NAME)
        }

    def send_metric(self, metric, value):
        """
        Send build metric value

        :param metric: metric type or metric name
        :type metric: :py:class:`legion.metrics.Metric` or str
        :param value: metric value
        :type value: float or int
        :return: None
        """
        return legion.metrics.send_metric(self.model_id, metric, value)

    def define_property(self, name, initial_value):
        """
        Define model property and set initial value

        :param name: property name
        :type name: str
        :param initial_value: initial property value
        :type initial_value: any
        :return: :py:class:`legion.pymodel.model.Model` -- model container
        """
        self._required_properties.append(name)

        if not legion.model.properties:
            raise Exception('Model properties has not been initialized')

        legion.model.properties[name] = initial_value

        return self
