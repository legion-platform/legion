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
EDGE commands for legion cli
"""
import argparse
import json
import typing

from legion.sdk import config
from legion.sdk.clients import model


def _parse_p_parameter(var: str):
    """
    Parse cli `-p key=value` parameter

    :param var:
    :return:
    """
    key, value = var.split('=')
    key, value = key.strip(), value.strip()

    if not key:
        raise ValueError(f'Keys is empty: {key}')

    if not value:
        raise ValueError(f'Values is empty: {value}')

    return key, value


def _prepare_invoke_parameters(args: argparse.Namespace) -> typing.Dict[str, typing.Any]:
    """
    Convert `-p` and `--json` cli parameters to the dict by the following rules:
        1) Evaluate `--json` parameter value to the dict
        2) Insert every `-p key=value`to the created dict

    :param args: cli argument
    :return dict result
    """
    params: typing.Dict[str, typing.Any] = {}

    if args.json:
        params = {**params, **json.loads(args.json)}

    if args.p:
        for k, v in args.p:
            params[k] = v

    return params


def invoke(args: argparse.Namespace):
    """
    Invoke model endpoint

    :param args: command arguments with .model_name, .namespace and .scale
    :return: None
    """
    model_client = model.build_client(args)
    params = _prepare_invoke_parameters(args)
    result = model_client.invoke(args.endpoint, **params)
    print(result)


def info(args: argparse.Namespace):
    """
    Invoke model endpoint
    :param args: command arguments with .model_name, .namespace and .scale
    :return: None
    """
    edge_client = model.build_client(args)
    result = edge_client.info()
    print(result)


def _add_model_discovery_params(parser: argparse.ArgumentParser):
    parser.add_argument('--model-route', '--mr', default=config.MODEL_ROUTE_NAME, type=str, help='Name of Model Route')
    parser.add_argument('--model-deployment', '--md', default=config.MODEL_DEPLOYMENT_NAME, type=str,
                        help='Name of Model Deployment')
    parser.add_argument('--url', default=config.MODEL_SERVER_URL, type=str, help='Full url of model server')
    parser.add_argument('--url-prefix', type=str, help='Url prefix of model server')
    parser.add_argument('--host', type=str, default=config.MODEL_HOST, help='Host of edge')
    parser.add_argument('--jwt', type=str, default=config.MODEL_JWT_TOKEN, help='Model jwt token')
    parser.add_argument('--local', action='store_true', help='Invoke locally deployed model')


def generate_parsers(main_subparser: argparse._SubParsersAction) -> None:
    """
    Generate cli parsers

    :param main_subparser: parent cli parser
    """
    model_subparser = main_subparser.add_parser('model',
                                                description='Model manipulations').add_subparsers()

    model_invoke_parser = model_subparser.add_parser('invoke', description='invoke model')
    _add_model_discovery_params(model_invoke_parser)
    model_invoke_parser.add_argument('-p', action='append', help='Key-value parameter. For example: -p x=2',
                                     type=_parse_p_parameter)
    model_invoke_parser.add_argument('--json', type=str, help='Json parameter. For example: --json {"x": 2}')
    model_invoke_parser.add_argument('--endpoint', default='default', help='Invoke specific module endpoint', type=str)
    model_invoke_parser.set_defaults(func=invoke)

    model_info_parser = model_subparser.add_parser('info', description='invoke model')
    _add_model_discovery_params(model_info_parser)
    model_info_parser.set_defaults(func=info)
