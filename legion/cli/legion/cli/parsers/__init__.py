#
#    Copyright 2019 EPAM Systems
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
CLI parsers
"""
import argparse
import json
import os
from typing import Any, Dict

import yaml


def prepare_resources(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Convert cli parameters to k8s resources
    :param args: cli parameters
    :return: k8s resources
    """
    resources = {"limits": {}, "requests": {}}
    if args.memory_limit:
        resources["limits"]["memory"] = args.memory_limit
    if args.memory_request:
        resources["requests"]["memory"] = args.memory_request
    if args.cpu_limit:
        resources["limits"]["cpu"] = args.cpu_limit
    if args.cpu_request:
        resources["requests"]["cpu"] = args.cpu_request

    if not resources["limits"]:
        del resources["limits"]

    if not resources["requests"]:
        del resources["requests"]

    return resources or None


def add_resources_params(parser: argparse.ArgumentParser) -> None:
    """
    Add resources parameters
    :param parser: Argument Parser
    """
    parser.add_argument('--memory-limit', default=None, type=str, help='limit memory for model deployment')
    parser.add_argument('--memory-request', '--memory', default=None, type=str,
                        help='request memory for model deployment')
    parser.add_argument('--cpu-limit', default=None, type=str, help='limit cpu for model deployment')
    parser.add_argument('--cpu-request', default=None, type=str, help='request cpu for model deployment')


def read_entity(file_path: str) -> Dict[str, Any]:
    """
    Read a MT/MD/VCS entity from the file
    :param file_path: file which contains a MT/MD/VCS
    :return: name and spec of MT/MD/VCS
    """
    _, ext = os.path.splitext(file_path)
    data: Dict[str, Any] = {}

    # We will use 1.2 yaml specification in the next golang cli implementation
    # Yaml 1.2 is superset of json format
    # We can avoid the following weird extension check
    with open(file_path) as f:
        # If the file doesn't contain extension than we assume that it's a yaml file.
        if not ext or ext == '.yaml' or ext == '.yml':
            data = yaml.safe_load(f)
        elif ext == '.json':
            data = json.load(f)
        else:
            raise ValueError("CLI can only read from yaml/json files")

    # Legionctl supports own rest api and k8s schemas
    name: str = data.get('name') or data.get('metadata', {}).get('name')
    if not name:
        raise ValueError(f'Unsupported file schema. Name is not provided. Read documentation about valid schema')

    spec: Dict[str, Any] = data.get('spec')
    if not spec:
        raise ValueError(f'Unsupported file schema. Spec is not provided. Read documentation about valid schema')

    return {"name": name, "spec": spec}
