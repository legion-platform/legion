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
from typing import Any, Dict

import colorama
from termcolor import colored

TRAIN_LOGS_COLOR = 'cyan'
colorama.init()


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


def print_training_logs(msg: str):
    """
    Print model training logs
    :param msg: training log
    """
    print(colored(msg, TRAIN_LOGS_COLOR))
