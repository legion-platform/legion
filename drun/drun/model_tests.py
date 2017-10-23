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
Base functionality for creating model tests
"""

import json
import os
import requests

import unittest2
import drun.env
from PIL import Image as PYTHON_Image


def get_model_base_url(model_name):
    """
    Get model base url from model name

    :param model_name: model name
    :type model_name: str
    :return: str -- base path for model calls
    """
    model_server_url = os.environ.get(*drun.env.MODEL_SERVER_URL)
    return '%s/api/model/%s' % (model_server_url, model_name)


class ModelUnitTests(unittest2.TestCase):
    """
    Base class for creating model tests
    """

    def setUpModel(self, model_name):
        """
        Initialize model

        :param model_name: model id (as in legion build / deploy)
        :type model_name: str
        :return: None
        """
        self._model_name = model_name
        self._base_url = get_model_base_url(model_name)

    def _load_image(self, path):
        """
        Load image from local path and check them

        :param path: path to local image
        :type path: str
        :return: bytes -- image content
        """
        self.assertTrue(os.path.exists(path), 'Image path not exists')
        image = PYTHON_Image.open(path)

        self.assertIsInstance(image, PYTHON_Image.Image, 'Invalid image type')

        return open(path, 'rb').read()

    def _parse_json_response(self, response):
        """
        Parse JSON response from model, check headers and return decoded JSON data

        :param response: response from server
        :type response: :py:class:`requests.response`
        :return: dict[str, any] -- returned values
        """
        self.assertEqual(response.headers.get('Content-Type'), 'application/json', 'Invalid response mimetype')

        data = response.text

        if isinstance(data, bytes):
            data = data.decode('utf-8')

        return json.loads(data)

    def _query_model(self, **values):
        """
        Query model for calculation

        :param values: values for passing to model. Key should be string (field name), value should be a string
        :type values: dict[str, any]
        :return: dict -- output values
        """
        if not hasattr(self, '_base_url'):
            raise Exception('Firstly call self.setUpModel in self.setUp')

        post_fields = {k: v for (k, v) in values.items() if not isinstance(v, bytes)}
        post_files = {k: v for (k, v) in values.items() if isinstance(v, bytes)}
        response = requests.post(self._base_url + '/invoke', post_fields, files=post_files)
        self.assertEqual(response.status_code, 200, 'Invalid response code for model call: %s' % response.text)

        return self._parse_json_response(response)
