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
Variables loader (from profiles/{env.PROFILE}.yml and /{env.CREDENTIAL_SECRETS}.yml files)
"""

import os
import typing

import yaml
from legion.robot.libraries import dex_client
from legion.robot.libraries.dex_client import init_session_id

PROFILE_ENVIRON_KEY = 'CLUSTER_NAME'
PATH_TO_PROFILES_DIR = 'PATH_TO_PROFILES_DIR'
PATH_TO_COOKIES_FILE = 'PATH_TO_COOKIES'
CREDENTIAL_SECRETS_ENVIRONMENT_KEY = 'CREDENTIAL_SECRETS'


def get_variables(arg: typing.Optional[str] = None, profile: typing.Optional[str] = None):
    """
    Gather and return all variables to robot

    :param arg: path to directory with profiles
    :param profile: name of profile
    :return: dict[str, Any] -- values for robot
    """
    # Build default path to profiles directory
    if not arg:
        arg = os.getenv(PATH_TO_PROFILES_DIR)
        if not arg:
            arg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'profiles'))

    # load Profile
    if not profile:
        profile = os.getenv(PROFILE_ENVIRON_KEY)
        if not profile:
            raise Exception('Cannot get profile - {} env variable is not set'.format(PROFILE_ENVIRON_KEY))

    profile = os.path.abspath(os.path.join(arg, '{}.yml'.format(profile)))
    if not os.path.exists(profile):
        raise Exception('Cannot get profile - file not found {}'.format(profile))

    with open(profile, 'r') as stream:
        data = yaml.safe_load(stream)

    # load Secrets
    secrets = os.getenv(CREDENTIAL_SECRETS_ENVIRONMENT_KEY)
    if not secrets:
        raise Exception('Cannot get secrets - {} env variable is not set'.format(CREDENTIAL_SECRETS_ENVIRONMENT_KEY))

    if not os.path.exists(secrets):
        raise Exception('Cannot get secrets - file not found {}'.format(secrets))

    with open(secrets, 'r') as stream:
        data.update(yaml.safe_load(stream))

    host_base_domain = data.get('test_base_domain', data['base_domain'])
    variables = {
        'HOST_BASE_DOMAIN': host_base_domain,
        'CLUSTER_NAME': data['cluster_name'],
        'FEEDBACK_BUCKET': data['legion_data_bucket'],
        'GRAFANA_USER': data['grafana']['admin']['username'],
        'GRAFANA_PASSWORD': data['grafana']['admin']['password'],
        'CLOUD_TYPE': data.get('cloud_type', 'gcp'),

        'EDGE_URL': os.getenv('EDGE_URL', f'https://edge.{host_base_domain}'),
        'EDI_URL': os.getenv('EDI_URL', f'https://edi.{host_base_domain}'),
        'GRAFANA_URL': os.getenv('GRAFANA_URL', f'https://grafana.{host_base_domain}'),
        'PROMETHEUS_URL': os.getenv('PROMETHEUS_URL', f'https://prometheus.{host_base_domain}'),
        'ALERTMANAGER_URL': os.getenv('ALERTMANAGER_URL', f'https://alertmanager.{host_base_domain}'),
        'DASHBOARD_URL': os.getenv('DASHBOARD_URL', f'https://dashboard.{host_base_domain}'),
    }

    if 'dex' in data and data['dex']['enabled'] and 'staticPasswords' in data['dex']['config'] and \
            data['dex']['config']['staticPasswords']:
        static_user = data['dex']['config']['staticPasswords'][0]

        init_session_id(static_user['email'], static_user['password'],
                            data.get('test_base_domain', data['base_domain']))

        variables['STATIC_USER_EMAIL'] = static_user['email']
        variables['STATIC_USER_PASS'] = static_user['password']

        variables['DEX_TOKEN'] = dex_client.get_token()
        variables['DEX_COOKIES'] = dex_client.get_session_cookies()
    else:
        variables['STATIC_USER_EMAIL'] = ''
        variables['STATIC_USER_PASS'] = ''

    return variables
