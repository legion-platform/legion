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
import logging
import os
import time

import kubernetes
import kubernetes.client
import kubernetes.client.models
import kubernetes.client.rest
import kubernetes.config
import kubernetes.config.config_exception

import legion.containers.headers
import legion.config
import legion.model
from legion.k8s.definitions import ENCLAVE_NAMESPACE_LABEL
import legion.k8s.watch
import legion.k8s.utils
import legion.k8s.services
import legion.utils

LOGGER = logging.getLogger(__name__)
RELOAD_TIMEOUT_SECONDS = 10


class K8SPropertyStorage:
    """
    K8S property storage
    """

    KEY_VALUE_POSTFIX = '.value'
    KEY_TYPE_POSTFIX = '.type'

    def __init__(self, storage_name, k8s_namespace=None, data=None):
        """
        Build K8S properties storage

        :param storage_name: name of storage
        :type storage_name: str
        :param k8s_namespace: k8s namespace of None for auto deducing (auto deducing works only in-cluster)
        :type k8s_namespace: str or None
        :param data: start data or None
        :type data: dict[str, any]
        """
        if not data:
            data = {}
        self._state = data

        self._storage_name = storage_name

        self._last_load_time = None
        self._saved = False

        if not k8s_namespace:
            k8s_namespace = legion.k8s.get_current_namespace()
        self._k8s_namespace = k8s_namespace

        LOGGER.info('Initializing {!r}'.format(self))

    @staticmethod
    def initialize(cls, storage_name, k8s_namespace=None):
        """
        Initialize K8S object and load

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
    def list_storages(cls, namespace):
        """
        Get list of storages

        :param cls: linked class
        :type cls: :py:class:`legion.k8s.properties.K8SPropertyStorage`
        :return: list[str] -- list of storages
        """
        resources = cls._find_k8s_resources(namespace)
        names = [
            resource.metadata.labels[legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE]
            for resource in resources
        ]
        return names

    @property
    def storage_name(self):
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
    def data(self):
        """
        Get current state

        :return: dict[str, any] -- current state
        """
        self._check_and_reload()
        return self._state

    @data.setter
    def data(self, new_state):
        """
        Update current state

        :param new_state: new state
        :type new_state: dict[str, any]
        :return: None
        """
        self._last_load_time = None
        self._saved = False
        self._state = new_state

    @data.deleter
    def data(self):
        """
        Reset current state

        :return: None
        """
        self._last_load_time = None
        self._saved = False
        self._state = {}

    def __setitem__(self, key, value):
        """
        Set property value

        :param key: key (property name)
        :type key: str
        :param value: value of property, should be str serializable
        :type value: str serializable object
        :return: None
        """
        self._last_load_time = None
        self._saved = False
        self._state[key] = value

    def __getitem__(self, item):
        """
        Get value of property

        :param item: name of property field
        :type item: str
        :return: any -- property value or None
        """
        self._check_and_reload()
        return self._state.get(item)

    @property
    def _core_api(self):
        """
        Build K8S Core API instance

        :return: :py:class:`kubernetes.client.CoreV1Api` -- Core V1 API instance
        """
        client = legion.k8s.utils.build_client()
        return kubernetes.client.CoreV1Api(client)

    def _unserialize_data(self, value, field_description):
        return value

    def _serialize_data(self, value, field_description):
        return value

    def _read_data_from_dict(self, source_dict):
        self._state = {
            k[:-len(self.KEY_VALUE_POSTFIX)]: self._unserialize_data(v, None)
            for (k, v) in source_dict.items()
        }
        return self._state

    def _write_data_to_dict(self):
        data = {
            k + self.KEY_VALUE_POSTFIX: self._serialize_data(v, None)
            for (k, v) in self._state.items()
        }

        return data

    def _find_k8s_resources(self):
        """
        Virtual function. Find K8S

        :return: V1ConfigMap or V1Secret  -- K8S object
        """
        raise NotImplementedError('This function is not implemented in this class')

    def _read_k8s_resource(self):
        """
        Virtual function. Create K8S object with appropriate content (from self._state)

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
            LOGGER.debug('Reading config map {!r} in namespace {!r}'.format(self._storage_name, self._k8s_namespace))

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
        if not self._last_load_time or not self._saved:
            return

        delta = time.time() - self._last_load_time
        if delta > RELOAD_TIMEOUT_SECONDS:
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

        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def destroy(self):
        """
        Remove config map from K8S

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
        return '<{} storage_name={!r}, k8s_namespace={!r}, data={!r}>'\
            .format(self.__class__.__name__, self._storage_name, self._k8s_namespace, self._state)


class K8SConfigMapStorage(K8SPropertyStorage):
    """
    Storage for properties that uses K8S config map for storing
    """

    @staticmethod
    def _find_k8s_resources(namespace):
        """
        Find K8S resources

        :return: V1ConfigMap -- K8S object
        """
        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)
        objects = core_api.list_namespaced_config_map(namespace).items

        objects = [
            obj
            for obj in objects
            if obj.metadata.labels and legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE in obj.metadata.labels
        ]

        return objects

    def _read_k8s_resource(self):
        """
        Read current state from K8S config map

        :return: None
        """
        return self._core_api.read_namespaced_config_map(self._storage_name, self._k8s_namespace)

    def _read_k8s_resource_exception_handler(self, exception):
        raise Exception('Cannot read config map {!r} in namespace {!r}: {}'
                        .format(self._storage_name, self._k8s_namespace, exception))

    def _write_k8s_resource(self):
        """
        Write current state to K8S config map

        :return: None
        """
        config_map_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
            name=self._storage_name,
            labels={
                legion.containers.headers.DOMAIN_MODEL_PROPERTY_TYPE: self._storage_name
            }
        )

        config_map_body = kubernetes.client.models.v1_config_map.V1ConfigMap(
            metadata=config_map_metadata,
            data=self._write_data_to_dict()
        )

        self._core_api.create_namespaced_config_map(self._k8s_namespace, config_map_body)

    def _write_k8s_resource_exception_handler(self, exception):
        raise Exception('Cannot write config map {!r} in namespace {!r}: {}'
                        .format(self._storage_name, self._k8s_namespace, exception))

    def _remove_k8s_resource(self, delete_options):
        """
        Remove config map from K8S

        :param delete_options:
        :type delete_options:
        :return: None
        """
        self._core_api.delete_namespaced_config_map(self._storage_name,
                                                    self._k8s_namespace,
                                                    body=delete_options)


class K8SSecretStorage(K8SPropertyStorage):
    """
    Storage for properties that uses K8S config map for storing
    """

    def read(self):
        """
        Read current state from K8S secret

        :return: None
        """
        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)

        try:
            LOGGER.debug('Reading secret {!r} in namespace {!r}'.format(self._storage_name, self._k8s_namespace))

            secret_object = core_api.read_namespaced_secret(self._storage_name, self._k8s_namespace)
        except Exception as load_exception:
            raise Exception('Cannot load secret {!r} in namespace {!r}: {}'
                            .format(self._storage_name, self._k8s_namespace, load_exception))

        if self.DATA_FIELD not in secret_object.data:
            raise Exception('Invalid Storage object')

        self._read_from_text(secret_object.data[self.DATA_FIELD])

    def write(self):
        """
        Write current state to K8S secret

        :return: None
        """
        client = legion.k8s.utils.build_client()
        core_api = kubernetes.client.CoreV1Api(client)

        secret_metadata = kubernetes.client.models.v1_object_meta.V1ObjectMeta(
            name=self._storage_name
        )

        secret_body = kubernetes.client.models.v1_secret.V1Secret(
            metadata=secret_metadata,
            data={self.DATA_FIELD: self._write_to_text()}
        )

        try:
            LOGGER.debug('Writing secret {!r} to namespace {!r}'.format(self._storage_name, self._k8s_namespace))

            core_api.create_namespaced_secret(self._k8s_namespace, secret_body)
        except Exception as load_exception:
            raise Exception('Cannot write secret {!r} in namespace {!r}: {}'
                            .format(self._storage_name, self._k8s_namespace, load_exception))

    def _remove_k8s_resource(self, delete_options):
        """
        Remove secret from K8S

        :param delete_options:
        :type delete_options:
        :return: None
        """
        self._core_api.delete_namespaced_secret(self._storage_name,
                                                self._k8s_namespace,
                                                body=delete_options)
