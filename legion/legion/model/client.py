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
from legion.utils import normalize_name

from PIL import Image as PYTHON_Image


def load_image(path):
    """
    Load image for model

    :param path: path to local image
    :type path: str
    :return: bytes -- image content
    """
    image = PYTHON_Image.open(path)
    if not isinstance(image, PYTHON_Image.Image):
        raise Exception('Invalid image type')
    return open(path, 'rb').read()


class ModelClient:
    """
    Model HTTP client
    """

    def __init__(self, model_id, host=None, http_client=None, use_relative_url=False):
        """
        Build client

        :param model_id: model id
        :type model_id: str
        :param host: host that server model HTTP requests (default: from ENV)
        :type host: str or None
        :param http_client: HTTP client (default: requests)
        :type http_client: python class that implements requests-like post & get methods
        :param use_relative_url: use non-full get/post requests (useful for locust)
        :type use_relative_url: bool
        """
        self._model_id = normalize_name(model_id)

        if host:
            self._host = host
        else:
            self._host = os.environ.get(*legion.config.MODEL_SERVER_URL)

        if http_client:
            self._http_client = http_client
        else:
            self._http_client = requests

        if use_relative_url:
            self._host = ''
        else:
            self._host = self._host.rstrip('/')

    @property
    def api_url(self):
        """
        Build API root URL

        :return: str -- api root url
        """
        return '{host}/api/model/{model_id}'.format(host=self._host, model_id=self._model_id)

    @property
    def invoke_url(self):
        """
        Build API invoke URL

        :return: str -- invoke url
        """
        return self.api_url + '/invoke'

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
        Parse model response

        :param response: model response
        :return: dict -- parsed response
        """
        if not 200 <= response.status_code < 400:
            raise Exception('Wrong status code returned: {}. Data: {}'.format(response.status_code, response.text))

        data = response.text

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        return json.loads(data)

    def invoke(self, **parameters):
        """
        Invoke model with parameters

        :param parameters: parameters for model
        :type parameters: dict[str, object] -- dictionary with parameters
        :return: dict -- parsed model response
        """
        post_fields = {k: v for (k, v) in parameters.items() if not isinstance(v, bytes)}
        post_files = {k: v for (k, v) in parameters.items() if isinstance(v, bytes)}
        response = self._http_client.post(self.invoke_url, data=post_fields, files=post_files)

        return self._parse_response(response)

    def info(self):
        """
        Get model info

        :return: dict -- parsed model info
        """
        response = self._http_client.get(self.info_url)

        return self._parse_response(response)
