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
legion k8s properties class
"""
import base64
import logging
import time
import json
import threading
import typing

import kubernetes
import kubernetes.client
import kubernetes.client.models
import kubernetes.client.rest
import kubernetes.config
import kubernetes.config.config_exception

import legion.containers.headers
import legion.config
import legion.model
import legion.k8s.watch
import legion.k8s.utils
import legion.k8s.services
import legion.utils

LOGGER = logging.getLogger(__name__)


class K8SPropertyStorage:
    """
    K8S property storage
    """

    def __init__(self, storage_name, k8s_namespace=None, data=None, cache_ttl=None):
        """
        Build K8S properties storage

        :param storage_name: name of storage
        :type storage_name: str
        :param k8s_namespace: k8s namespace of None for auto deducing (auto deducing works only in-cluster)
        :type k8s_namespace: str or None
        :param data: start data or None
        :type data: dict[str, any]
        :param cache_ttl: amount of lifetime of cache in seconds or None for disabling
        :type cache_ttl: int
        """
        if not data:
            data = {}
        self._state = data  # type: dict

        self._cache_ttl = cache_ttl  # type: int or None

        self._storage_name = legion.utils.normalize_name(storage_name, dns_1035=True)  # type: str
        if self._storage_name != storage_name:
            LOGGER.warning('Name of storage has been normalized from {!r} to {!r}'.format(
                storage_name, self._storage_name
            ))

        self._last_load_time = None  # type: float or None
        self._saved = False  # type: bool
        self._callback_invoking_thread = None  # type: threading.Thread or None

        self._k8s_namespace = k8s_namespace  # type: str

        self._properties_update_thread = None  # type: threading.Thread or None
        self._on_property_change_callback_getter = None  # type: typing.Callable[[], typing.Callable[[], None]] or None

        LOGGER.info('Initializing {!r}'.format(self))

    @classmethod
    def retrive(cls, storage_name, k8s_namespace=None):
        """
        Initialize storage class from K8S object and load

        :param cls: linked class
        :type cls: :py:class:`legion.k8s.properties.K8SPropertyStorage`
        :param storage_name: name of storage
        :type storage_name: str
        :param k8s_namespace: k8s namespace of None for auto deducing (auto deducing works only in-cluster)
        :type k8s_namespace: str or None
        :return: :py:class:`legion.k8s.properties.K8SPropertyStorage` -- built and initialized object
        """
        instance = cls(storage_name, k8s_namespace)
        instance.load()
        return instance

    @classmethod
    def list(cls, k8s_namespace=None):
        """
        Get list of storage names

        :param cls: linked class
        :type cls: :py:class:`legion.k8s.properties.K8SPropertyStorage`
        :param k8s_namespace: target namespace or None for auto deducing (auto deducing works only in-cluster)
        :type k8s_namespace: str
        :return: list[str] -- list of storages
        """
        if not k8s_namespace:
            k8s_namespace = legion.k8s.get_current_namespace()

        resources = cls._find_k8s_resources(k8s_namespace)
        names = [
            resource.metadata.labels[legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE]
            for resource in resources
            if K8SPropertyStorage.is_valid_object(resource)
        ]
        return names

    @staticmethod
    def is_valid_object(obj):
        """
        Check that obj is valid K8S object

        :param obj: kubernetes object
        :return: bool -- is valid K8S object or not
        """
        return obj.metadata.labels and legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE in obj.metadata.labels

    @property
    def k8s_name(self):
        """
        Get storage name (object name)

        :return: str -- storage name
        """
        return self._storage_name

    @property
    def k8s_namespace(self):
        """
        Get K8S namespace name

        :return: str -- K8S namespace name
        """
        return self._k8s_namespace

    @property
    def k8s_namespace_or_default(self):
        """
        Get K8S namespace or set and retrive default namespace

        :return: str -- setted or default namespace
        """
        if not self._k8s_namespace:
            LOGGER.info('Detecting default namespace')
            self._k8s_namespace = legion.k8s.utils.get_current_namespace()

        return self._k8s_namespace

    @property
    def last_load_time(self):
        """
        Get last load time if it exists

        :return: float or None -- last load time
        """
        return self._last_load_time

    @property
    def data(self):
        """
        Get current state

        :return: dict[str, str] -- current state
        """
        self._check_and_reload()
        return self._state

    @data.setter
    def data(self, new_state):
        """
        Update current state with another dict

        :param new_state: new state
        :type new_state: dict[str, str-serializable]
        :return: None
        """
        self._last_load_time = None
        self._saved = False
        self._state = {k: str(v) for (k, v) in new_state.items()}

    @data.deleter
    def data(self):
        """
        Reset current state

        :return: None
        """
        self._last_load_time = None
        self._saved = False
        self._state = {}

    def serialize_data_to_string(self):
        """
        Serialize data to string

        :return: str -- serialized data
        """
        return json.dumps(self.data)

    @staticmethod
    def parse_data_from_string(string_value):
        """
        Parse data from string value

        :param string_value: string representation of value
        :type string_value: str
        :return: dict[str, str] -- parsed values
        """
        if not string_value:
            return {}
        return json.loads(string_value)

    def __setitem__(self, key, value):
        """
        Set property value (it would be converted to string immediately)

        :param key: key (property name)
        :type key: str
        :param value: value of property, should be str serializable
        :type value: str serializable object
        :return: None
        """
        self._last_load_time = None
        self._saved = False
        self._state[key] = str(value)

    def __getitem__(self, key):
        """
        Get value of property

        :param key: name of property field
        :type key: str
        :return: any -- property value or None
        """
        self._check_and_reload()
        return self._state.get(key)

    def keys(self):
        """
        Get list of keys

        :return: list[str] -- list of keys
        """
        self._check_and_reload()
        return list(self._state.keys())

    def get(self, key, cast):
        """
        Get value of property with cast to legion type

        :param key: name of property field
        :type key: str
        :param cast:
        :type cast: LegionType
        :return:
        """
        value = self[key]
        legion_base_type = cast.representation_type
        return legion_base_type.parse(value)

    @property
    def _core_api(self):
        """
        Build K8S Core API instance

        :return: :py:class:`kubernetes.client.CoreV1Api` -- Core V1 API instance
        """
        client = legion.k8s.utils.build_client()
        return kubernetes.client.CoreV1Api(client)

    def _read_data_from_dict(self, source_dict):
        """
        Update current state with values from dict

        :param source_dict: dict with readed values
        :type source_dict: dict[str, str]
        :return: None
        """
        self._state = source_dict

    def _write_data_to_dict(self):
        """
        Get dict of current state to be saved in K8S

        :return: dict[str, str] -- dict with values to save
        """
        return self._state

    @staticmethod
    def _find_k8s_resources(k8s_namespace):
        """
        Virtual function. Find K8S

        :return: V1ConfigMap or V1Secret  -- K8S object
        """
        raise NotImplementedError('This function is not implemented in this class')

    def _read_k8s_resource(self):
        """
        Virtual function. Get appropriate K8S object

        :return: V1ConfigMap or V1Secret  -- K8S object
        """
        raise NotImplementedError('This function is not implemented in this class')

    def _read_k8s_resource_exception_handler(self, exception):
        """
        Virtual function. Handler for exceptions that can appear during reading K8S resource

        :param exception: appeared exception
        :type exception: :py:class:`Exception`
        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def load(self):
        """
        Load data from K8S

        :return: None
        """
        try:
            LOGGER.debug('Reading {} {!r} in namespace {!r}'.format(self.__class__.__name__,
                                                                    self.k8s_name,
                                                                    self.k8s_namespace_or_default))

            config_map_object = self._read_k8s_resource()

            self._read_data_from_dict(config_map_object.data)
        except Exception as load_exception:
            self._read_k8s_resource_exception_handler(load_exception)

        self._last_load_time = time.time()
        self._saved = True

    def _check_and_reload(self):
        """
        Check and reload data if last operation was reading and time is out

        :return: None
        """
        if not self._cache_ttl:
            return

        if not self._last_load_time or not self._saved:
            return

        delta = time.time() - self._last_load_time
        if delta > self._cache_ttl:
            self.load()

    def _write_k8s_resource(self):
        """
        Virtual function. Create K8S object with appropriate content (from self._state)

        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def _write_k8s_resource_exception_handler(self, exception):
        """
        Virtual function. Handler for exceptions that can appear during creating K8S resource

        :param exception: appeared exception
        :type exception: :py:class:`Exception`
        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def save(self):
        """
        Write current state object (self._state) to K8S object

        :return: None
        """
        try:
            LOGGER.debug('Writing {!r}'.format(self))
            self._write_k8s_resource()
        except Exception as write_exception:
            self._write_k8s_resource_exception_handler(write_exception)

        self._saved = True

    def _remove_k8s_resource(self, delete_options):
        """
        Remove appropriate resource from K8S

        :param delete_options: K8S delete options
        :type delete_options: :py:class:`kubernetes.client.V1DeleteOptions`
        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def destroy(self):
        """
        Remove appropriate K8S object

        :return: None
        """
        delete_options = kubernetes.client.V1DeleteOptions(propagation_policy='Foreground',
                                                           grace_period_seconds=0)

        LOGGER.debug('Deleting {!r}'.format(self))
        self._remove_k8s_resource(delete_options)

    def __repr__(self):
        """
        Get representation of object

        :return: str -- representation
        """
        return '<{} k8s_name={!r}, k8s_namespace={!r}, data={!r}>' \
            .format(self.__class__.__name__, self._storage_name, self._k8s_namespace, self._state)

    def is_watched_object(self, obj):
        """
        Check if K8S object is a target watch item

        :param obj: kubernetes object
        :return: bool -- is target or not
        """
        return self.is_valid_object(obj) and obj.metadata.name == self._storage_name

    def watch(self):
        """
        Get generator that watches for storage updates and yields EVENT and new data as dict

        :return: None
        """
        LOGGER.info('Creating watch for object {!r}'.format(self))
        watch = self._build_k8s_resource_watch()
        for (event_type, event_object) in watch.stream:
            LOGGER.info('Watch got new event. Type = {}'.format(event_type))
            self.load()
            yield (event_type, self.data)

    def _call_callback(self):
        """
        Update callback logic

        :return: None
        """
        try:
            callback = self._on_property_change_callback_getter()
            LOGGER.debug('Invoking callback {!r} (id: {}) in dedicated thread...'.format(callback, id(callback)))
            invoke_result = callback()
            LOGGER.debug('Result of callback invocation: {!r}'.format(invoke_result))
        except Exception as property_update_callback_invoke_exception:
            LOGGER.exception('Cannot invoke model update callback',
                             exc_info=property_update_callback_invoke_exception)

    def emit_update_signal(self):
        """
        Emit signal of properties update to model

        :return: None
        """
        if self._callback_invoking_thread and self._callback_invoking_thread.is_alive():
            LOGGER.warning('Ignoring update callback: another is working')
        else:
            self._callback_invoking_thread = threading.Thread(name='invoke-model-properties-update',
                                                              daemon=True,
                                                              target=self._call_callback)

            self._callback_invoking_thread.daemon = True
            LOGGER.info('Starting thread {}'.format(self._callback_invoking_thread.name))
            self._callback_invoking_thread.start()

    def update_thread(self):
        """
        Process update callback logic

        :return: None
        """
        LOGGER.info('Properties watch thread has been started')
        for event, new_data in self.watch():
            LOGGER.info('Model have got information that properties storage had got update: {}'.format(event))
            self.emit_update_signal()
        LOGGER.error('Update thread has been finished')

    def set_change_callback(self, callback_getter):
        """
        Set change callback getter and start thread (thread starts only once)

        :param callback_getter: callback getter result of which will be called on each property update
        :type callback_getter: :py:class:`Callable[[], typing.Callable[[], None]]`
        :return: None
        """
        if not callable(callback_getter):
            raise Exception('Invalid argument: object should be callable')

        LOGGER.debug('Setting new property change callback getter for {!r} to {!r} (id: {})'
                     .format(self, callback_getter, id(callback_getter)))

        self._on_property_change_callback_getter = callback_getter

    def start_update_watcher(self):
        """
        Start update watcher

        :return: None
        """
        if not self.last_load_time:
            LOGGER.info('Properties has not been loaded, so watch thread will not be started')
            return

        if self._properties_update_thread:
            LOGGER.debug('Thread already has been started')
            return

        self._properties_update_thread = threading.Thread(name='watch-model-properties-update',
                                                          daemon=True,
                                                          target=self.update_thread)

        self._properties_update_thread.daemon = True
        LOGGER.info('Starting thread')
        self._properties_update_thread.start()
        LOGGER.info('Thread has been started')

    def _build_k8s_resource_watch(self):
        """
        Get K8S resource watch object

        :return: :py:class:`legion.k8s.watch.ResourceWatch` -- resource watch
        """
        raise NotImplementedError('This function is not implemented in this class')


class K8SConfigMapStorage(K8SPropertyStorage):
    """
    Storage for properties that uses K8S config map for storing
    """

    @staticmethod
    def _find_k8s_resources(k8s_namespace):
        """
        Find K8S resources

        :return: list[:py:class:`kubernetes.client.V1ConfigMap`] -- K8S objects
        """
        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)
        objects = core_api.list_namespaced_config_map(k8s_namespace).items

        return objects

    def _build_k8s_resource_watch(self):
        """
        Get K8S resource watch object

        :return: :py:class:`legion.k8s.watch.ResourceWatch` -- resource watch
        """
        return legion.k8s.watch.ResourceWatch(self._core_api.list_namespaced_config_map,
                                              namespace=self.k8s_namespace_or_default,
                                              filter_callable=self.is_watched_object)

    def _read_k8s_resource(self):
        """
        Get appropriate K8S config map

        :return: :py:class:`kubernetes.client.V1ConfigMap` -- K8S object
        """
        return self._core_api.read_namespaced_config_map(self.k8s_name, self.k8s_namespace_or_default)

    def _read_k8s_resource_exception_handler(self, exception):
        """
        Handle exceptions that can appear during reading K8S config map

        :param exception: appeared exception
        :type exception: :py:class:`Exception`
        :return: None
        """
        raise Exception('Cannot read config map {!r} in namespace {!r}: {}'
                        .format(self.k8s_name, self.k8s_namespace_or_default, exception))

    def _write_k8s_resource(self):
        """
        Create K8S config map with appropriate content (from self._state)

        :return: None
        """
        config_map_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
            name=self.k8s_name,
            labels={
                legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE: self._storage_name
            }
        )

        config_map_body = kubernetes.client.models.v1_config_map.V1ConfigMap(
            metadata=config_map_metadata,
            data=self._write_data_to_dict()
        )

        try:
            LOGGER.info('Overriding ConfigMap {!r} in {!r} namespace'.format(self.k8s_name,
                                                                             self.k8s_namespace_or_default))
            self._core_api.replace_namespaced_config_map(self.k8s_name,
                                                         self.k8s_namespace_or_default,
                                                         config_map_body)
        except kubernetes.client.rest.ApiException as invoke_exception:
            if invoke_exception.status == 404:
                LOGGER.info('Creating ConfigMap {!r} in {!r} namespace'.format(self.k8s_name,
                                                                               self.k8s_namespace_or_default))
                self._core_api.create_namespaced_config_map(self.k8s_namespace_or_default,
                                                            config_map_body)

    def _write_k8s_resource_exception_handler(self, exception):
        """
        Handle exceptions that can appear during creating K8S resource

        :param exception: appeared exception
        :type exception: :py:class:`Exception`
        :return: None
        """
        raise Exception('Cannot write config map {!r} in namespace {!r}: {}'
                        .format(self.k8s_name, self.k8s_namespace_or_default, exception))

    def _remove_k8s_resource(self, delete_options):
        """
        Remove config map from K8S

        :param delete_options: K8S delete options
        :type delete_options: :py:class:`kubernetes.client.V1DeleteOptions`
        :return: None
        """
        self._core_api.delete_namespaced_config_map(self.k8s_name,
                                                    self.k8s_namespace_or_default,
                                                    body=delete_options)


class K8SSecretStorage(K8SPropertyStorage):
    """
    Storage for properties that uses K8S secret for storing
    """

    def _read_data_from_dict(self, source_dict):
        """
        Update current state with values from dict

        :param source_dict: dict with readed values
        :type source_dict: dict[str, str]
        :return: None
        """
        self._state = {
            k: base64.b64decode(v.encode('ascii')).decode('utf-8')
            for k, v in source_dict.items()
        }

    def _write_data_to_dict(self):
        """
        Get dict of current state to be saved in K8S

        :return: dict[str, str] -- dict with values to save
        """
        return {
            k: base64.b64encode(v.encode('utf-8')).decode('ascii')  # encode string with base64
            for k, v in self._state.items()
        }

    @staticmethod
    def _find_k8s_resources(k8s_namespace):
        """
        Find K8S resources

        :return: list[:py:class:`kubernetes.client.V1Secret`] -- K8S objects
        """
        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)
        objects = core_api.list_namespaced_secret(k8s_namespace).items

        return objects

    def _build_k8s_resource_watch(self):
        """
        Get K8S resource watch object

        :return: :py:class:`legion.k8s.watch.ResourceWatch` -- resource watch
        """
        return legion.k8s.watch.ResourceWatch(self._core_api.list_namespaced_secret,
                                              namespace=self.k8s_namespace_or_default,
                                              filter_callable=self.is_watched_object)

    def _read_k8s_resource(self):
        """
        Get appropriate K8S secret

        :return: :py:class:`kubernetes.client.V1Secret` -- K8S object
        """
        return self._core_api.read_namespaced_secret(self.k8s_name, self.k8s_namespace_or_default)

    def _read_k8s_resource_exception_handler(self, exception):
        """
        Handle exceptions that can appear during reading K8S secret

        :param exception: appeared exception
        :type exception: :py:class:`Exception`
        :return: None
        """
        raise Exception('Cannot read secret {!r} in namespace {!r}: {}'
                        .format(self.k8s_name, self.k8s_namespace_or_default, exception))

    def _write_k8s_resource(self):
        """
        Create K8S secret with appropriate content (from self._state)

        :return: None
        """
        secret_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
            name=self.k8s_name,
            labels={
                legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE: self._storage_name
            }
        )

        secret_body = kubernetes.client.models.v1_secret.V1Secret(
            metadata=secret_metadata,
            data=self._write_data_to_dict()
        )

        try:
            LOGGER.info(
                'Overriding Secret {!r} in {!r} namespace'.format(self.k8s_name, self.k8s_namespace_or_default))
            self._core_api.replace_namespaced_secret(self.k8s_name, self.k8s_namespace_or_default, secret_body)
        except kubernetes.client.rest.ApiException as invoke_exception:
            if invoke_exception.status == 404:
                LOGGER.info(
                    'Creating Secret {!r} in {!r} namespace'.format(self.k8s_name, self.k8s_namespace_or_default))
                self._core_api.create_namespaced_secret(self.k8s_namespace_or_default, secret_body)

    def _write_k8s_resource_exception_handler(self, exception):
        """
        Handle exceptions that can appear during creating K8S resource

        :param exception: appeared exception
        :type exception: :py:class:`Exception`
        :return: None
        """
        raise Exception('Cannot write Secret {!r} in namespace {!r}: {}'
                        .format(self.k8s_name, self.k8s_namespace_or_default, exception))

    def _remove_k8s_resource(self, delete_options):
        """
        Remove secret from K8S

        :param delete_options: K8S delete options
        :type delete_options: :py:class:`kubernetes.client.V1DeleteOptions`
        :return: None
        """
        self._core_api.delete_namespaced_secret(self.k8s_name,
                                                self.k8s_namespace_or_default,
                                                body=delete_options)
