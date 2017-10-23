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
DRun env names
"""

BUILD_NUMBER = 'BUILD_NUMBER', None
BUILD_COMMIT = 'BUILD_COMMIT', None

NODE_NAME = 'NODE_NAME', None

MODEL_SERVER_URL = 'MODEL_SERVER_URL', 'http://edge'

METRIC_LABEL = 'METRIC_LABEL', None
METRIC_ENDPOINT_HOST = 'METRIC_ENDPOINT_HOST', 'graphite'
METRIC_ENDPOINT_PORT = 'METRIC_ENDPOINT_PORT', 80

GRAFANA_URL = 'GRAFANA_URL', 'http://grafana:3000/'
GRAFANA_USER = 'GRAFANA_USER', 'admin'
GRAFANA_PASSWORD = 'GRAFANA_PASSWORD', 'admin'
