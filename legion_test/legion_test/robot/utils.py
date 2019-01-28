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
Robot test library - utils
"""

import datetime
import socket
import requests
import time
import json


class Utils:
    """
    Utilities for robot tests
    """

    @staticmethod
    def check_domain_exists(domain):
        """
        Check that domain (DNS name) has been registered

        :param domain: domain name (A record)
        :type domain: str
        :raises: Exception
        :return: None
        """
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror as exception:
            if exception.errno == -2:
                raise Exception('Unknown domain name: {}'.format(domain))
            else:
                raise

    @staticmethod
    def check_remote_file_exists(url, login=None, password=None):
        """
        Check that remote file exists (through HTTP/HTTPS)

        :param url: remote file URL
        :type url: str
        :param login: login
        :type login: str or None
        :param password: password
        :type password: str or None
        :raises: Exception
        :return: None
        """
        credentials = None
        if login and password:
            credentials = login, password

        response = requests.get(url,
                                stream=True,
                                verify=False,
                                auth=credentials)
        if response.status_code >= 400 or response.status_code < 200:
            raise Exception('Returned wrong status code: {}'.format(response.status_code))

        response.close()

    @staticmethod
    def sum_up(*values):
        """
        Sum up arguments

        :param values: Values to sum up
        :type values: int[]
        :return: Sum
        :rtype: int
        """
        result = 0
        for value in values:
            result += value
        return result

    @staticmethod
    def subtract(minuend, *values):
        """
        Subtract arguments from minuend

        :param minuend: A Minuend
        :type minuend: int
        :param values: Values to subtract from minuend
        :type values: int[]
        :rtype: int
        """
        result = minuend
        for value in values:
            result -= value
        return result

    @staticmethod
    def parse_edi_inspect_columns_info(edi_output):
        """
        Parse EDI inspect output

        :param edi_output: EDI stdout
        :type edi_output: str
        :return: list[list[str]] -- parsed EDI output
        """
        lines = edi_output.splitlines()
        if len(lines) < 2:
            return []

        return [[item.strip() for item in line.split('|')] for line in lines[1:]]

    @staticmethod
    def find_model_information_in_edi(parsed_edi_output, model_id, model_version=None):
        """
        Get specific model EDI output

        :param parsed_edi_output: parsed EDI output
        :type parsed_edi_output: list[list[str]]
        :param model_id: model id
        :type model_id: str
        :param model_version: (Optional) model version
        :type model_version: str
        :return: list[str] -- parsed EDI output for specific model
        """
        founded = [info for info in parsed_edi_output if info[0] == model_id and model_version in (None, info[2])]
        if not founded:
            raise Exception('Info about model {!r} v {!r} not found'.format(model_id, model_version))

        return founded[0]

    @staticmethod
    def check_valid_http_response(url, token=None):
        """
        Check if model return valid code for get request

        :param url: url with model_id for checking
        :type url: str
        :param token: token for the authorization
        :type token: str
        :return:  str -- response text
        """
        tries = 6
        error = None
        for i in range(tries):
            try:
                if token:
                    headers = {"Authorization": "Bearer {}".format(token)}
                    response = requests.get(url, timeout=10, headers=headers)
                else:
                    response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    return response.text
                elif i >= 5:
                    raise Exception('Returned wrong status code: {}'.format(response.status_code))
                elif response.status_code >= 400 or response.status_code < 200:
                    print('Response code = {}, sleep and try again'.format(response.status_code))
                    time.sleep(3)
            except requests.exceptions.Timeout as e:
                error = e
                time.sleep(3)
        if error:
            raise error
        else:
            raise Exception('Unexpected case happen!')

    @staticmethod
    def execute_post_request(url, data=None, json=None, cookies=None):
        """
        Execute post request

        :param url: url for request
        :type url: str
        :param data: data to send in request
        :type data: dict
        :param json: json data to send in request
        :type json: dict
        :param cookies: cookies to send in request
        :type cookies: dict
        :return:  str -- response text
        """
        response = requests.post(url, json=json, data=data, cookies=cookies)

        return {"text": response.text, "code": response.status_code}

    @staticmethod
    def get_component_auth_page(url, jenkins=False, token=None):
        """
        Get component main auth page

        :param boolean jenkins: if jenkins service is under test
        :param url: component url
        :type url: str
        :param token: token for the authorization
        :type url: str
        :return:  response_code and response_text
        :rtype: dict
        """
        if jenkins:
            response = requests.get('{}/securityRealm/commenceLogin'.format(url), timeout=10)
        elif token:
            headers = {"Authorization": "Bearer {}".format(token)}
            response = requests.get(url, timeout=10, headers=headers)
        else:
            response = requests.get(url, timeout=10)
        return {"response_code": response.status_code, "response_text": response.text}

    @staticmethod
    def post_credentials_to_auth(component_url, cluster_host, creds, jenkins=False):
        """
        Get session id and send post request with credentials to authorize

        :param boolean jenkins: if jenkins service is under test
        :param str component_url: legion core component url
        :param str cluster_host: cluster host name
        :param dict creds: dict with login and password
        :return: response_code and response_text after auth try
        :rtype: dict
        """
        from legion_test.robot.dex_client import REQUEST_ID_REGEXP, AUTHENTICATION_PATH
        import re

        session = requests.Session()
        if jenkins:
            response = session.get("{}.{}/securityRealm/commenceLogin".format(component_url, cluster_host))
        else:
            response = session.get("{}.{}".format(component_url, cluster_host))

        if response.status_code != 200:
            raise IOError('Authentication endpoint is unavailable, got {} http code'
                          .format(response.status_code))
        match = re.search(REQUEST_ID_REGEXP, response.text)

        if match:
            request_id = match.group(1)
        else:
            raise ValueError('Request ID was not found on page')

        if creds["login"] == "admin":
            response = session.post(AUTHENTICATION_PATH.format(cluster_host, request_id), creds)
        else:
            response = session.post(AUTHENTICATION_PATH.format(cluster_host, request_id), creds)
        return {"response_code": response.status_code, "response_text": response.text}

    @staticmethod
    def get_static_user_data():
        """
        Get static user email and password form secrets

        :return: user email and password
        :rtype: dict
        """
        import os

        import yaml
        from legion_test.profiler_loader import CREDENTIAL_SECRETS_ENVIRONMENT_KEY
        secrets = os.getenv(CREDENTIAL_SECRETS_ENVIRONMENT_KEY)
        if not secrets:
            raise Exception(
                'Cannot get secrets - {} env variable is not set'.format(CREDENTIAL_SECRETS_ENVIRONMENT_KEY))

        if not os.path.exists(secrets):
            raise Exception('Cannot get secrets - file not found {}'.format(secrets))

        with open(secrets, 'r') as stream:
            data = yaml.load(stream)

        static_user = data['dex']['config']['staticPasswords'][0]
        return {"login": static_user['email'], "password": static_user['password']}

    @staticmethod
    def parse_json_string(str):
        """
        Parse JSON string

        :param str: JSON string
        :type str: str
        :return: dict -- object
        """
        return json.loads(str)

    @staticmethod
    def get_current_time(time_template):
        """
        Get templated time

        :param time_template: time template
        :type time_template: str
        :return: None or str -- time from template
        """
        return datetime.datetime.utcnow().strftime(time_template)

    @staticmethod
    def get_future_time(offset, time_template):
        """
        Get templated time on `offset` seconds in future

        :param offset: time offset from current time in seconds
        :type offset: str
        :param time_template: time template
        :type time_template: str
        :return: str -- time from template
        """
        return (datetime.datetime.utcnow() +
                datetime.timedelta(seconds=int(offset))).strftime(time_template)

    @staticmethod
    def reformat_time(time_str, initial_format, target_format):
        datetime_obj = datetime.datetime.strptime(time_str, initial_format)
        return datetime.datetime.strftime(datetime_obj, target_format)

    @staticmethod
    def wait_up_to_second(second, time_template=None):
        """
        Wait up to second then generate time from template

        :param second: target second (0..59)
        :type second: int
        :param time_template: (Optional) time template
        :type time_template: str
        :return: None or str -- time from template
        """
        current_second = datetime.datetime.now().second
        target_second = int(second)

        if current_second > target_second:
            sleep_time = 60 - (current_second - target_second)
        else:
            sleep_time = target_second - current_second

        if sleep_time:
            print('Waiting {} second(s)'.format(sleep_time))
            time.sleep(sleep_time)

        if time_template:
            return Utils.get_current_time(time_template)

    @staticmethod
    def order_list_of_dicts_by_key(list_of_dicts, field_key):
        """
        Order list of dictionaries by key as integer

        :param list_of_dicts: list of dictionaries
        :type list_of_dicts: List[dict]
        :param field_key: key to be ordered by
        :type field_key: str
        :return: List[dict] -- ordered list
        """
        return sorted(list_of_dicts, key=lambda item: int(item[field_key]))

    @staticmethod
    def concatinate_list_of_dicts_field(list_of_dicts, field_key):
        """
        Concatinate list of dicts field to string

        :param list_of_dicts: list of dictionaries
        :type list_of_dicts: List[dict]
        :param field_key: key of field to be concatinated
        :type field_key: str
        :return: str -- concatinated string
        """
        return ''.join([item[field_key] for item in list_of_dicts])

    @staticmethod
    def repeat_string_n_times(string, count):
        """
        Repeat string N times

        :param string: string to be repeated
        :type string: str
        :param count: count
        :type count: int
        :return: str -- result string
        """
        return string * int(count)

