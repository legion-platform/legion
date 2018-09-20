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

import legion_test.utils


class Model:
    """
    Model API class
    """

    @staticmethod
    def invoke_model_api(model_id, model_version, edge, token, endpoint, **payload):
        """
        Invoke model through API

        :param model_id: model ID
        :param model_version: model version
        :param edge: edge url
        :param token: model API JWT token
        :param endpoint: name of endpoint
        :param payload: payload dict
        :return: dict -- response
        """
        headers = {"Authorization": "Bearer {}".format(token)}
        url = '{}/api/model/{}/{}/invoke/{}'.format(edge, model_id, model_version, endpoint)

        print('Requesting {} with data = {} in POST mode'.format(url, payload))

        response = requests.post(
            url,
            data=payload,
            headers=headers
        )

        if response.status_code != 200:
            raise Exception('Returned wrong status code: {}'.format(response.status_code))

        return response.json()

    @staticmethod
    def get_model_api_properties(model_id, model_version, edge, token):
        """
        Get model properties through model API

        :param model_id: model ID
        :param model_version: model version
        :param edge: edge url
        :param token: model API JWT token
        :return: dict -- response
        """
        headers = {"Authorization": "Bearer {}".format(token)}
        url = '{}/api/model/{}/{}/properties'.format(edge, model_id, model_version)

        print('Requesting {} in GET mode'.format(url))

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception('Returned wrong status code: {}'.format(response.status_code))

        return response.json()

    @staticmethod
    def ensure_model_property_has_been_updated(model_id, model_version, edge, token, prop_name, desired_value):
        """
        Get model properties through model API

        :param model_id: model ID
        :param model_version: model version
        :param edge: edge url
        :param token: model API JWT token
        :param prop_name: name of property
        :param desired_value: desired value
        :return: None
        """
        def check():
            properties = Model.get_model_api_properties(model_id, model_version, edge, token)
            return properties.get(prop_name) == desired_value

        if not legion_test.utils.wait_until(check, 1, 5):
            raise Exception('Property {} has not been updated to desired value {}'
                            .format(prop_name, desired_value))
