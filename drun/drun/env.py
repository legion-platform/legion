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

BUILD_NUMBER = 'BUILD_NUMBER', 0
BUILD_COMMIT = 'BUILD_COMMIT', None
JOB_NAME = 'JOB_NAME', 'UNKNOWN JOB'

NODE_NAME = 'NODE_NAME', None

MODEL_SERVER_URL = 'MODEL_SERVER_URL', 'http://edge'

STATSD_HOST = 'STATSD_HOST', 'graphite'
STATSD_PORT = 'STATSD_PORT', 8125
STATSD_NAMESPACE = 'STATSD_NAMESPACE', 'legion.model'

GRAPHITE_HOST = 'GRAPHITE_HOST', 'graphite'
GRAPHITE_PORT = 'GRAPHITE_PORT', 2003
GRAPHITE_NAMESPACE = 'GRAPHITE_NAMESPACE', 'stats.legion.model'

GRAFANA_URL = 'GRAFANA_URL', 'http://grafana:3000/'
GRAFANA_USER = 'GRAFANA_USER', 'admin'
GRAFANA_PASSWORD = 'GRAFANA_PASSWORD', 'admin'
