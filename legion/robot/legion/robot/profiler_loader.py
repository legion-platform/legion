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
Variables loader from json Cluster Profile
"""

import os
import json
import sys
from legion.robot.libraries import dex_client
from legion.robot.libraries.dex_client import init_session_id

CLUSTER_PROFILE = 'CLUSTER_PROFILE'

def get_variables(profile=None):
    """
    Gather and return all variables to robot

    :param profile: path to cluster profile
    :type profile: str
    :return: dict[str, Any] -- values for robot
    """

    # load Cluster Profile
    profile = profile or sys.argv[1] or os.getenv(CLUSTER_PROFILE)

    if not profile:
        raise Exception('Can\'t get profile at path {}'.format(profile))
    if not os.path.exists(profile):
        raise Exception('Can\'t get profile - {} file not found'.format(profile))

    with open(profile, 'r') as json_file:
        data = json.load(json_file)

        variables = {}

        try:
            host_base_domain = data.get('base_domain')
            variables = {
                'HOST_BASE_DOMAIN': host_base_domain,
                'CLUSTER_NAME': data.get('cluster_name'),
                'FEEDBACK_BUCKET': data.get('legion_data_bucket'),
                'GRAFANA_USER': data.get('grafana_admin'),
                'GRAFANA_PASSWORD': data.get('grafana_pass'),
                'CLOUD_TYPE': data.get('cloud_type'),
                'STATIC_USER_EMAIL': data.get('dex_static_user_email'),
                'STATIC_USER_PASS': data.get('dex_static_user_pass'),
                'EDGE_URL': os.getenv('EDGE_URL', 'https://edge.{host_base_domain}'),
                'EDI_URL': os.getenv('EDI_URL', f'https://edi.{host_base_domain}'),
                'GRAFANA_URL': os.getenv('GRAFANA_URL', f'https://grafana.{host_base_domain}'),
                'PROMETHEUS_URL': os.getenv('PROMETHEUS_URL', f'https://prometheus.{host_base_domain}'),
                'ALERTMANAGER_URL': os.getenv('ALERTMANAGER_URL', f'https://alertmanager.{host_base_domain}'),
                'DASHBOARD_URL': os.getenv('DASHBOARD_URL', f'https://dashboard.{host_base_domain}'),
                'JUPYTERLAB_URL': os.getenv('JUPITERLAB_URL', f'https://jupyterlab.{host_base_domain}'),
            }
        except Exception as err:
            raise Exception("Can\'t get variable from cluster profile: {}".format(err))

        try:
            init_session_id(variables['STATIC_USER_EMAIL'], variables['STATIC_USER_PASS'], host_base_domain)
            variables['DEX_TOKEN'] = dex_client.get_token()
            variables['DEX_COOKIES'] = dex_client.get_session_cookies()
        except Exception as err:
            raise Exception("Can\'t get dex authentication data: {}".format(err))

    return variables
