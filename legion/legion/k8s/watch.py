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
legion k8s watch context manager
"""
import logging

import kubernetes
import kubernetes.client.rest
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception
import urllib3
import urllib3.exceptions

LOGGER = logging.getLogger(__name__)
CONNECTION_CONTEXT = None


class ResourceWatch:
    """
    Watch for K8S resources (context manager)
    """

    def __init__(self, api_function, *args,
                 filter_callable=None,
                 object_constructor=None,
                 resource_version=None,
                 **kwargs):
        """
        Initialize context manager for resource watch

        :param api_function: API function to watch
        :param args: additional positional arguments for API function
        :param filter_callable: (Optional) callable to filter objects
        :param object_constructor:  (Optional) callable to construct object wrappers
        :param resource_version: (Optional) start resource version
        :param kwargs: additional key value arguments for API function
        """
        self._api_function = api_function
        self._filter_callable = filter_callable
        self._object_constructor = object_constructor
        self._resource_version = resource_version
        self._args = args
        self._kwargs = kwargs

    @property
    def stream(self):
        """
        Access watch stream

        :return: tuple(str, Any) -- event type and event object (plain or constructed if
                                    object_constructor has been passed)
        """
        LOGGER.debug('Starting watch stream')

        while True:
            LOGGER.debug('Entering event loop iteration in watch')
            try:
                watch = kubernetes.watch.Watch()
                kwargs = self._kwargs
                if self._resource_version:
                    LOGGER.debug('Using latest resource version: {}'.format(self._resource_version))
                    kwargs['resource_version'] = self._resource_version

                LOGGER.debug('Creating watcher for function {}. Args: {!r}, Kwargs: {!r}'
                             .format(self._api_function.__name__, self._args, kwargs))

                stream = watch.stream(self._api_function,
                                      *self._args,
                                      **kwargs)
                for event in stream:
                    event_type = event['type']
                    event_object = event['object']

                    if hasattr(event['object'], 'metadata') and hasattr(event['object'].metadata, 'resource_version'):
                        self._resource_version = event['object'].metadata.resource_version

                    # Check if valid object
                    pass_event = not self._filter_callable or self._filter_callable(event_object)

                    if pass_event:
                        # Construct specific object
                        if self._object_constructor:
                            event_object = self._object_constructor(event_object)

                        yield (event_type, event_object)
            except urllib3.exceptions.ProtocolError as protocol_error:
                LOGGER.warning('Connection to K8S API has been lost: {}. Reconnecting...'.format(protocol_error))
                continue
            except kubernetes.client.rest.ApiException as kube_api_exception:
                LOGGER.warning('Got Kubernetes API exception: {}'.format(kube_api_exception))
                if kube_api_exception.status == 500:
                    LOGGER.warning('Got Kubernetes error 500. Reconnecting...')
                    continue
                else:
                    LOGGER.warning('Got wrong error code. Breaking...')
                    break
            except Exception as general_exception:
                LOGGER.exception('Got general exception: {}. Breaking...'.format(general_exception))
                break

        LOGGER.debug('Watch stream has been ended')
