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
Robot test library - model API
"""
import requests


class Model:
    """
    Model API class
    """
    @staticmethod
    def invoke_model_api(model_id, model_version, edge, endpoint, **payload):
        """
        Invoke model through API

        :param model_id: model ID
        :param model_version: model version
        :param edge: edge url
        :param endpoint: name of endpoint
        :param payload: payload dict
        :return: dict -- response
        """
        response = requests.post(
            '{}/api/model/{}/{}/invoke/{}'.format(edge, model_id, model_version, endpoint),
            data=payload
        )

        if response.status_code != 200:
            raise Exception('Returned wrong status code: {}'.format(response.status_code))

        return response.json()

    @staticmethod
    def get_model_api_properties(model_id, model_version, edge):
        """
        Invoke model through API

        :param model_id: model ID
        :param model_version: model version
        :param edge: edge url
        :return: dict -- response
        """
        response = requests.get(
            '{}/api/model/{}/{}/properties'.format(edge, model_id, model_version)
        )

        if response.status_code != 200:
            raise Exception('Returned wrong status code: {}'.format(response.status_code))

        return response.json()
