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

import kubernetes
import kubernetes.client
import kubernetes.client.models
import kubernetes.client.rest
import kubernetes.config
import kubernetes.config.config_exception
import yaml

import legion.containers.headers
import legion.config
from legion.k8s.definitions import ENCLAVE_NAMESPACE_LABEL
from legion.k8s.definitions import \
    LEGION_COMPONENT_NAME_API, LEGION_COMPONENT_NAME_EDI, \
    LEGION_COMPONENT_NAME_GRAFANA, LEGION_COMPONENT_NAME_GRAPHITE
import legion.k8s.watch
import legion.k8s.utils
import legion.k8s.services
import legion.utils

LOGGER = logging.getLogger(__name__)


class K8SPropertyStorage:

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

        if not k8s_namespace:
            k8s_namespace = legion.k8s.get_current_namespace()
        self._k8s_namespace = k8s_namespace

        LOGGER.info('Initializing {!r}'.format(self))

    @property
    def data(self):
        """
        Get current state

        :return: dict[str, any] -- current state
        """
        return self._state

    @data.setter
    def data(self, new_state):
        """
        Update current state

        :param new_state: new state
        :type new_state: dict[str, any]
        :return: None
        """
        self._state = new_state

    @data.deleter
    def data(self):
        """
        Reset current state

        :return: None
        """
        self._state = {}

    def __setitem__(self, key, value):
        """
        Set property value

        :param key: key (property name)
        :type key: str
        :param value: value of property
        :type value: any
        :return: None
        """
        self._state[key] = value

    def __getitem__(self, item):
        """
        Get value of property

        :param item: name of property field
        :type item: str
        :return: any -- property value or None
        """
        return self._state.get(item)

    @property
    def _core_api(self):
        client = legion.k8s.utils.build_client()
        return kubernetes.client.CoreV1Api(client)

    def _read_data_from_dict(self, dict):
        self._state = dict

    def _write_data_to_dict(self):
        return self._state

    def _read_k8s_resource(self):
        """
        Read contents of property object to self._state object

        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def _read_k8s_resource_exception_handler(self, exception):
        raise NotImplementedError('This function is not implemented in this class')

    def read(self):
        try:
            LOGGER.debug('Reading config map {!r} in namespace {!r}'.format(self._storage_name, self._k8s_namespace))

            config_map_object = self._read_k8s_resource()

            self._read_data_from_dict(config_map_object.data)

        except Exception as load_exception:
            self._read_k8s_resource_exception_handler(load_exception)

    def _write_k8s_resource(self):
        """
        Write current state object (self._state) to K8S object

        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def _write_k8s_resource_exception_handler(self, exception):
        raise NotImplementedError('This function is not implemented in this class')

    def write(self):
        """
        Write current state object (self._state) to K8S object

        :return: None
        """
        try:
            LOGGER.debug('Writing {!r}'.format(self))
            self._write_k8s_resource()
        except Exception as write_exception:
            self._write_k8s_resource_exception_handler(write_exception)


    def _remove_k8s_resource(self, delete_options):
        """
        Remove appropriate resource from K8S

        :return: None
        """
        raise NotImplementedError('This function is not implemented in this class')

    def remove(self):
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
            name=self._storage_name
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
