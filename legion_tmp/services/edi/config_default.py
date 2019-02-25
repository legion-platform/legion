#!/usr/bin/env python
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
Default config for legion
"""

LEGION_API_ADDR = '0.0.0.0'
LEGION_API_PORT = 5001

NAMESPACE = ''

DEBUG = False

AUTH_ENABLED = False

AUTH_TOKEN_ENABLED = True
AUTH_TOKEN = 'demo-token'

REGISTER_ON_GRAFANA = True

CLUSTER_CONFIG_PATH = '/opt/legion/state/cluster.yaml'
CLUSTER_SECRETS_PATH = '/opt/legion/secrets'
JWT_CONFIG_PATH = '/opt/legion/jwtconf'
