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
Tool for executing adding secrets for airflow connections
"""
import os
import glob
import subprocess
import json

import yaml

SECRETS_DIRECTORY = 'SECRETS_DIRECTORY'
AIRFLOW_BINARY = 'AIRFLOW_BINARY'


def remove_connection(connection_info):
    """
    Remove connection from airflow

    :param connection_info: dict with next fields: connection_id, connection_type,  host, port, schema, login, password, extra
    :type connection_info: dict
    :return: None
    """
    if 'connection_id' not in connection_info:
        raise Exception('connection_id not found in %s' % repr(connection_info))

    airflow_binary = os.getenv(AIRFLOW_BINARY, 'airflow')

    arguments = [airflow_binary, 'connections', '--delete',
                 '--conn_id', connection_info['connection_id']]

    arguments = [str(x) for x in arguments]
    subprocess.check_call(arguments)


def add_connection(connection_info):
    """
    Add connection to airflow

    :param connection_info: dict with next fields: connection_id, connection_type,  host, port, schema, login, password, extra
    :type connection_info: dict
    :return: None
    """

    if 'connection_id' not in connection_info:
        raise Exception('connection_id not found in %s' % repr(connection_info))

    if 'connection_type' not in connection_info:
        raise Exception('connection_type not found in %s' % repr(connection_info))

    airflow_binary = os.getenv(AIRFLOW_BINARY, 'airflow')

    arguments = [airflow_binary, 'connections', '--add',
                 '--conn_id', connection_info['connection_id'],
                 '--conn_type', connection_info['connection_type']]

    if 'host' in connection_info:
        arguments.extend(['--conn_host', connection_info['host']])

    if 'port' in connection_info:
        arguments.extend(['--conn_port', connection_info['port']])

    if 'login' in connection_info:
        arguments.extend(['--conn_login', connection_info['login']])

    if 'password' in connection_info:
        arguments.extend(['--conn_password', connection_info['password']])

    if 'schema' in connection_info:
        arguments.extend(['--conn_schema', connection_info['schema']])

    if 'extra' in connection_info:
        arguments.extend(['--conn_extra', json.dumps(connection_info['extra'])])

    arguments = [str(x) for x in arguments]
    subprocess.check_call(arguments)


def process_file(path):
    """
    Process connections file

    :param path: path to connection configuration to load
    :type path: str
    :return: None
    """
    try:
        print('Processing secrets (connections) file: %s' % path)
        with open(path, 'r') as file_stream:
            data = yaml.load(file_stream)
            if isinstance(data, list):
                connections = data
            elif isinstance(data, dict) and 'connections' in data:
                connections = data['connections']
            else:
                raise Exception('Connections block not found')

            for connection in connections:
                try:
                    remove_connection(connection)
                    add_connection(connection)
                except Exception as add_exception:
                    print('Cannot remove/add connection %s from file %s - %s' % (repr(connection), path, add_exception))
    except Exception as read_exception:
        print('Cannot correctly read file %s - %s' % (path, read_exception))


def work():
    """
    Add connection from secrets

    :return: None
    """
    secrets_location = os.environ.get(SECRETS_DIRECTORY, None)

    if not secrets_location:
        print('%s not set' % SECRETS_DIRECTORY)
        return

    if not os.path.exists(secrets_location):
        print('%s not exists' % secrets_location)
        return

    if os.path.isfile(secrets_location):
        process_file(secrets_location)
    else:
        files = glob.glob('%s/**/*' % (secrets_location), recursive=True)
        for file in files:
            if os.path.isfile(file):
                process_file(file)


if __name__ == '__main__':
    work()
