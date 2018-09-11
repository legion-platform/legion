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

import os
import json
import requests

import legion.config
import legion.http
from legion.utils import normalize_name

from PIL import Image as PYTHON_Image


def load_image(path):
    """
    Load image for model

    :param path: path to local image
    :type path: str
    :return: bytes -- image content
    """
    with PYTHON_Image.open(path) as image:
        if not isinstance(image, PYTHON_Image.Image):
            raise Exception('Invalid image type')

        with open(path, 'rb') as stream:
            return stream.read()


class ModelClient:
    """
    Model HTTP client
    """

    def __init__(self, model_id, model_version, token=None, host=None, http_client=None, use_relative_url=False,
                 timeout=None):
        """
        Build client

        :param model_id: model id
        :type model_id: str
        :param model_version: model version
        :type model_version: str
        :param token: API token value to use (default: None)
        :type token: str
        :param host: host that server model HTTP requests (default: from ENV)
        :type host: str or None
        :param http_client: HTTP client (default: requests)
        :type http_client: python class that implements requests-like post & get methods
        :param use_relative_url: use non-full get/post requests (useful for locust)
        :type use_relative_url: bool
        :param timeout: timeout for connections
        :type timeout: int
        """
        self._model_id = normalize_name(model_id)
        self._model_version = model_version
        self._token = token

        if host:
            self._host = host
        else:
            self._host = os.environ.get(*legion.config.MODEL_SERVER_URL)

        if http_client:
            self._http_client = http_client
        else:
            self._http_client = requests

        self._use_relative_url = use_relative_url
        if self._use_relative_url:
            self._host = ''
        else:
            self._host = self._host.rstrip('/')

        self._timeout = timeout

    def __repr__(self):
        """
        Get string representation of model client

        :return: str -- model client information
        """
        return '{}({!r}, {!r}, {!r}, {!r}, {!r})'.format(self.__class__.__name__,
                                                         self._model_id, self._host,
                                                         self._http_client, self._use_relative_url, self._timeout)

    __str__ = __repr__

    @property
    def api_url(self):
        """
        Build API root URL

        :return: str -- api root url
        """
        return '{host}/api/model/{model_id}/{model_version}'.format(host=self._host,
                                                                    model_id=self._model_id,
                                                                    model_version=self._model_version)

    def build_invoke_url(self, endpoint=None):
        """
        Build API invoke URL

        :param endpoint: (Optional) target endpoint
        :type endpoint: str
        :return: str -- invoke url
        """
        if endpoint:
            return '{}/invoke/{}'.format(self.api_url, endpoint)
        return '{}/invoke'.format(self.api_url)

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

    @staticmethod
    def _prepare_invoke_request(**parameters):
        """
        Build POST and FILE fields for request due their type

        :param parameters: dict -- invoke parameters
        :return: tuple[dict, dict] -- POST and FILE dictionaries in tuple
        """
        post_fields_dict = {k: v for (k, v) in parameters.items() if not isinstance(v, bytes)}
        post_files = {k: v for (k, v) in parameters.items() if isinstance(v, bytes)}

        post_fields_list = []
        for (k, v) in post_fields_dict.items():
            if isinstance(v, tuple) or isinstance(v, list):
                for item in v:
                    post_fields_list.append((k + '[]', str(item)))
            else:
                post_fields_list.append((k, str(v)))

        return post_fields_list, post_files

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

    def batch(self, invoke_parameters, endpoint=None):
        """
        Send batch invoke request

        :param invoke_parameters: list of dictionaries
        :type invoke_parameters: list[dict]
        :param endpoint: name of endpoint
        :type endpoint: str
        :return: list -- parsed model response
        """
        request_lines = []
        for parameters in invoke_parameters:
            data, files = self._prepare_invoke_request(**parameters)
            if files:
                raise Exception('Files object not allowed for batch invocation')

            request_lines.append(legion.http.encode_http_params(data))

        content = '\n'.join(request_lines)
        url = self.build_batch_url(endpoint)
        response = self._http_client.post(url,
                                          data=content,
                                          **self._additional_kwargs)
        return self._parse_response(response)

    def invoke(self, endpoint=None, **parameters):
        """
        Invoke model with parameters

        :param parameters: parameters for model
        :type parameters: dict[str, object] -- dictionary with parameters
        :param endpoint: name of endpoint
        :type endpoint: str
        :return: dict -- parsed model response
        """
        data, files = self._prepare_invoke_request(**parameters)
        url = self.build_invoke_url(endpoint)
        response = self._http_client.post(url,
                                          data=data, files=files,
                                          **self._additional_kwargs)

        return self._parse_response(response)

    def info(self):
        """
        Get model info

        :return: dict -- parsed model info
        """
        response = self._http_client.get(self.info_url,
                                         **self._additional_kwargs)

        return self._parse_response(response)
