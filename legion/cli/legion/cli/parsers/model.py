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
import json

import click
from legion.sdk import config
from legion.sdk.clients.model import ModelClient, calculate_url


@click.group()
def model():
    """
    Allow you to perform actions on deployed models
    """
    pass


@model.command()
@click.option('--model-route', '--mr', default=config.MODEL_ROUTE_NAME, type=str, help='Name of Model Route')
@click.option('--model-deployment', '--md', default=config.MODEL_DEPLOYMENT_NAME, type=str,
              help='Name of Model Deployment')
@click.option('--url', default=config.MODEL_SERVER_URL, type=str, help='Full url of model server')
@click.option('--url-prefix', type=str, help='Url prefix of model server')
@click.option('--host', type=str, default=config.MODEL_HOST, help='Host of edge')
@click.option('--jwt', type=str, default=config.MODEL_JWT_TOKEN, help='Model jwt token')
@click.option('--json', 'json_input', type=str, help='Json parameter. For example: --json {"x": 2}')
@click.option('--json-file', '--file', type=click.Path(exists=True), help='Path to json file')
def invoke(json_input, model_route: str, model_deployment: str, url: str, url_prefix: str,
           host: str, jwt: str, json_file: str):
    """
    Invoke model endpoint

    :param json_input:
    :param client:
    :return: None
    """
    if json_file:
        with open(json_file) as f:
            json_input = f.read()

    jwt = jwt or config.get_config_file_variable(model_route or model_deployment,
                                                 section=config.MODEL_JWT_TOKEN_SECTION)
    client = ModelClient(calculate_url(host, url, model_route, model_deployment, url_prefix), jwt)

    result = client.invoke(**json.loads(json_input))

    click.echo(json.dumps(result))


@model.command()
@click.option('--model-route', '--mr', default=config.MODEL_ROUTE_NAME, type=str, help='Name of Model Route')
@click.option('--model-deployment', '--md', default=config.MODEL_DEPLOYMENT_NAME, type=str,
              help='Name of Model Deployment')
@click.option('--url', default=config.MODEL_SERVER_URL, type=str, help='Full url of model server')
@click.option('--url-prefix', type=str, help='Url prefix of model server')
@click.option('--host', type=str, default=config.MODEL_HOST, help='Host of edge')
@click.option('--jwt', type=str, default=config.MODEL_JWT_TOKEN, help='Model jwt token')
def info(model_route: str, model_deployment: str, url: str, url_prefix: str,
         host: str, jwt: str):
    """
    Get model information

    :param client: Model HTTP Client
    """
    jwt = jwt or config.get_config_file_variable(model_route or model_deployment,
                                                 section=config.MODEL_JWT_TOKEN_SECTION)
    client = ModelClient(calculate_url(host, url, model_route, model_deployment, url_prefix), jwt)

    result = client.info()

    print(result)
