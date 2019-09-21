#
#    Copyright 2017 EPAM Systems
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
Model HTTP API client and utils
"""
import json
import logging

import requests
from requests.compat import urlencode
from requests.utils import to_key_val_list
from urllib3.exceptions import HTTPError

from legion.sdk import config
from legion.sdk.clients.route import ModelRouteClient
from legion.sdk.utils import ensure_function_succeed

LOGGER = logging.getLogger(__name__)


def encode_http_params(data):
    """
    Encode HTTP parameters to URL query string

    :param data: data as text or tuple/list
    :type data: str or bytes or tuple or list
    :return: str -- encoded data
    """
    if isinstance(data, (str, bytes)):
        return urlencode(data)
    elif hasattr(data, '__iter__'):
        result = []
        for key, value in to_key_val_list(data):
            if value is not None:
                result.append(
                    (key.encode('utf-8') if isinstance(key, str) else key,
                     value.encode('utf-8') if isinstance(value, str) else value))
        return urlencode(result, doseq=True)
    raise ValueError('Invalid argument')


def calculate_url(host: str, url: str = None, model_route: str = None, model_deployment: str = None,
                  url_prefix: str = None, mr_client: ModelRouteClient = None):
    """
    Calculate url for model

    :param host: edge host
    :param url: full url to model api
    :param model_route: model route name
    :param model_deployment: model deployment name
    :param url_prefix: model prefix
    :return: model url
    """
    if url:
        return url

    if url_prefix:
        LOGGER.debug('')
        return f'{host}{url_prefix}'

    model_route = model_route or model_deployment
    if model_route:
        if mr_client is None:
            mr_client = ModelRouteClient()

        model_route = mr_client.get(model_route)

        LOGGER.debug('Found model route: %s', model_route)
        return model_route.status.edge_url

    raise NotImplementedError("Cannot create a model url")


def calculate_url_from_config():
    """
    Calculate url for model with config values

    :return: model url
    """
    return calculate_url(config.MODEL_HOST, config.MODEL_SERVER_URL, config.MODEL_ROUTE_NAME,
                         config.MODEL_DEPLOYMENT_NAME, config.MODEL_PREFIX_URL)


class ModelClient:
    """
    Model HTTP client
    """

    def __init__(self, url=None, token=None, http_client=requests,
                 http_exception=requests.exceptions.RequestException,
                 timeout=None):
        """
        Build client

        :param token: API token value to use (default: None)
        :type token: str
        :param http_client: HTTP client (default: requests)
        :type http_client: python class that implements requests-like post & get methods
        :param http_exception: http_client exception class, which can be thrown by http_client in case of some errors
        :type http_exception: python class that implements Exception class interface
        :param timeout: timeout for connections
        :type timeout: int
        """
        self._url = url
        self._token = token
        self._http_client = http_client
        self._http_exception = http_exception
        self._timeout = timeout

        LOGGER.debug('Model client params: %s, %s, %s, %s, %s', url, token, http_client, http_exception, timeout)

    @property
    def api_url(self):
        """
        Build API root URL

        :return: str -- api root url
        """
        return '{host}/api/model'.format(host=self._url)

    def build_batch_url(self, endpoint=None):
        """
        Build API batch invoke URL

        :param endpoint: (Optional) target endpoint
        :type endpoint: str
        :return: str -- batch invoke url
        """
        if endpoint:
            return '{}/batch/{}'.format(self.api_url, endpoint)
        return '{}/batch'.format(self.api_url)

    @property
    def info_url(self):
        """
        Build API info URL

        :return: str -- info url
        """
        return self.api_url + '/info'

    @staticmethod
    def _parse_response(response):
        """
        Parse model response (requests or FlaskClient)

        :param response: model HTTP response
        :type response: object with .text or .data and .status_code attributes
        :return: dict -- parsed response
        """
        data = response.text if hasattr(response, 'text') else response.data

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        try:
            data = json.loads(data)
        except ValueError:
            pass

        if not 200 <= response.status_code < 400:
            url = response.url if hasattr(response, 'url') else None
            raise Exception('Wrong status code returned: {}. Data: {}. URL: {}'
                            .format(response.status_code, data, url))

        return data

    @property
    def _additional_kwargs(self):
        """
        Get additional HTTP client key-value arguments like timestamp

        :return: dict -- additional kwargs
        """
        kwargs = {}
        if self._token:
            kwargs['headers'] = {'Authorization': 'Bearer {token}'.format(token=self._token)}
        if self._timeout is not None:
            kwargs['timeout'] = self._timeout
        return kwargs

    def _request(self, http_method, url, data=None, files=None, retries=10, sleep=3, **kwargs):
        """
        Send request with provided method and other parameters
        :param http_method: HTTP method
        :type http_method: str
        :param url: url to send request to
        :type url: str
        :param data: request data
        :type data: any
        :param files: files to send with request
        :type files: dict
        :param retries: How many times to retry executing a request
        :type retries: int
        :param sleep: How much time to sleep between retries in case of errors
        :type sleep: int
        :return: dict -- parsed model response
        """
        http_method = http_method.lower()

        client_method = getattr(self._http_client, http_method)

        if data:
            kwargs['data'] = data
        if files:
            kwargs['files'] = files

        def check_function():
            try:
                return client_method(url, **kwargs)
            except (self._http_exception, HTTPError) as e:
                LOGGER.error('Failed to connect to {}: {}.'.format(url, e))

        response = ensure_function_succeed(check_function, retries, sleep)
        if response is None:
            raise self._http_exception('HTTP request failed')
        return self._parse_response(response)

    def invoke(self, **parameters):
        """
        Invoke model with parameters

        :param parameters: parameters for model
        :type parameters: dict[str, object] -- dictionary with parameters
        :return: dict -- parsed model response
        """
        return self._request('post', f'{self.api_url}/invoke', **self._additional_kwargs, json=parameters)

    def info(self):
        """
        Get model info

        :return: dict -- parsed model info
        """
        return self._request('get', self.info_url, **self._additional_kwargs)
