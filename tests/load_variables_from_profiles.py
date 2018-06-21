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
Variables loader (from profiles/{env.PROFILE}.ansible.yml files)
"""

import os

import yaml
from legion_test.robot.dex_client import init_session_id

PROFILE_ENVIRON_KEY = 'PROFILE'


def get_variables(arg):
    """
    Gather and return all variables to robot

    :param arg: path to directory with profiles
    :type args: str
    :return: dict[str, Any] -- values for robot
    """
    profile = os.getenv(PROFILE_ENVIRON_KEY)
    if not profile:
        raise Exception('Cannot get profile - {} env variable is not set'.format(PROFILE_ENVIRON_KEY))

    if not arg:
        raise Exception('Cannot get profile - script should be run with one argument that '
                        'provides path to profiles dir. Current argument: {}'.format(arg))

    profile = os.path.join(arg, '{}.yml'.format(profile))
    if not os.path.exists(profile):
        raise Exception('Cannot get profile - file not found {}'.format(profile))

    with open(profile, 'r') as stream:
        data = yaml.load(stream)

    variables = {
        'CLUSTER_NAMESPACE': data['namespace'],
        'DEPLOYMENT': data['deployment'],

        'HOST_BASE_DOMAIN': data.get('test_base_domain', data['base_domain']),
        'USE_HTTPS_FOR_TESTS': data.get('use_https_for_tests', 'yes') == 'yes',

        'SERVICE_ACCOUNT': data['service_account']['login'],
        'SERVICE_PASSWORD': data['service_account']['password'],

        'JENKINS_JOBS': data['examples_to_test'],
        'ENCLAVES': data.get('enclaves', []),

        'CLUSTER_NAME': data['cluster_name']
    }

    variables['HOST_PROTOCOL'] = 'https' if variables['USE_HTTPS_FOR_TESTS'] else 'http'
    variables['MODEL_TEST_ENCLAVE'] = variables['ENCLAVES'][0] if len(variables['ENCLAVES']) > 0 else 'UNKNOWN_ENCLAVE'

    if 'dex' in data and data['dex']['enabled'] and 'staticPasswords' in data['dex']['config'] and \
            data['dex']['config']['staticPasswords']:
        static_user = data['dex']['config']['staticPasswords'][0]
        init_session_id(static_user['email'], static_user['password'], data.get('test_base_domain', data['base_domain']))

    return variables
