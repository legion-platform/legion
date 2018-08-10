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
                 **kwargs):
        """
        Initialize context manager for resource watch

        :param api_function: API function to watch
        :param args: additional positional arguments for API function
        :param filter_callable: (Optional) callable to filter objects
        :param object_constructor:  (Optional) callable to construct object wrappers
        :param kwargs: additional key value arguments for API function
        """
        self._api_function = api_function
        self._filter_callable = filter_callable
        self._object_constructor = object_constructor
        self._args = args
        self._kwargs = kwargs

        self._watch = kubernetes.watch.Watch()
        self._stream = None

    def __enter__(self):
        """
        Enter watch

        :return:
        """
        self._stream = self._watch.stream(self._api_function,
                                          *self._args,
                                          **self._kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit watch

        :param exc_type: exception type
        :param exc_val: exception
        :param exc_tb: exception traceback
        :return: None
        """
        self.stop()

    @property
    def stream(self):
        """
        Access watch stream

        :return: tuple(str, Any) -- event type and event object (plain or constructed if
                                    object_constructor has been passed)
        """
        LOGGER.debug('Starting watch stream')

        reconnect = True
        while reconnect:
            reconnect = False

            try:
                for event in self._stream:
                    event_type = event['type']
                    event_object = event['object']

                    # Check if valid object
                    pass_event = not self._filter_callable or self._filter_callable(event_object)

                    if pass_event:
                        # Construct specific object
                        if self._object_constructor:
                            event_object = self._object_constructor(event_object)

                        yield (event_type, event_object)
            except urllib3.exceptions.ProtocolError:
                LOGGER.info('Connection to K8S API has been lost, reconnecting..')
                reconnect = True

        LOGGER.debug('Watch stream has been ended')

    @property
    def watch(self):
        """
        Access watch object

        :return: :py:class:`kubernetes.watch.Watch` -- watch object
        """
        return self._watch

    def stop(self):
        """
        Stop watch

        :return: None
        """
        try:
            self.watch.stop()
        finally:
            LOGGER.debug('Watch has been stopped')
