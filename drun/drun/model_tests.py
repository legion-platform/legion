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

from drun.model_http_api import load_image, get_requests_parameters_for_model_invoke, get_model_invoke_url

import unittest2
from locust import HttpLocust, TaskSet, task


class LocustTaskSet(TaskSet):
    """
    Base class for creating locust performance task sets
    """

    def setup_model(self, model_id):
        """
        Initialize model

        :param model_id: model id (as in legion build / deploy)
        :type model_id: str
        :return: None
        """
        self._model_id = model_id

    def _invoke_model(self, **values):
        """
        Query model for calculation

        :param values: values for passing to model. Key should be string (field name), value should be a string
        :type values: dict[str, any]
        :return: None
        """
        if not hasattr(self, '_model_id') or not getattr(self, '_model_id'):
            raise Exception('Firstly call self.setUpModel in self.setUp')

        url = get_model_invoke_url(self._model_id, False)
        parameters = get_requests_parameters_for_model_invoke(**values)

        self.client.post(url, **parameters)


class ModelUnitTests(unittest2.TestCase):
    """
    Base class for creating model tests
    """

    def setUpModel(self, model_id):
        """
        Initialize model

        :param model_id: model id (as in legion build / deploy)
        :type model_id: str
        :return: None
        """
        self._model_id = model_id

    def _load_image(self, path):
        """
        Load image from local path and check them

        :param path: path to local image
        :type path: str
        :return: bytes -- image content
        """
        self.assertTrue(os.path.exists(path), 'Image path not exists')
        return load_image(path)

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
        if not hasattr(self, '_model_id') or not getattr(self, '_model_id'):
            raise Exception('Firstly call self.setUpModel in self.setUp')

        url = get_model_invoke_url(self._model_id)
        parameters = get_requests_parameters_for_model_invoke(**values)

        response = requests.post(url, **parameters)
        self.assertEqual(response.status_code, 200,
                         'Invalid response code for model call on url %s: %s' % (url, response.text))

        return self._parse_json_response(response)
