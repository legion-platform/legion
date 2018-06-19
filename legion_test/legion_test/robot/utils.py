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
    def check_valid_http_response(url):
        """
        Check if model return valid code for get request

        :param url: url with model_id for checking
        :type url: str
        :return:  str -- response text
        """
        tries = 6
        error = None
        for i in range(tries):
            try:
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

    def wait_up_to_second(second, time_template=None):
        """
        Wait up to second then generate time from template

        :param second: target second
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
            return datetime.datetime.utcnow().strftime(time_template)
