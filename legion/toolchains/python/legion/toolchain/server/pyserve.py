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
Flask app
"""

import logging
import os
import typing

from flask import Flask, Blueprint, request, jsonify, redirect
from flask import current_app as app
from legion.toolchain.pymodel.model import Model
from legion.toolchain.server.http import parse_batch_request, parse_request, configure_application, prepare_response

LOGGER = logging.getLogger(__name__)
blueprint = Blueprint('pyserve', __name__)

SERVE_ROOT = '/'
SERVE_INFO = '/api/model/info'
SERVE_INVOKE = '/api/model/invoke/{endpoint}'
SERVE_INVOKE_DEFAULT = '/api/model/invoke'
SERVE_BATCH = '/api/model/batch/{endpoint}'
SERVE_BATCH_DEFAULT = '/api/model/batch'
SERVE_HEALTH_CHECK = '/healthcheck'

ALL_URLS = SERVE_ROOT, \
           SERVE_INFO, \
           SERVE_INVOKE, SERVE_INVOKE_DEFAULT, \
           SERVE_BATCH, SERVE_BATCH_DEFAULT, \
           SERVE_HEALTH_CHECK


@blueprint.route(SERVE_ROOT)
def root():
    """
    Return static file for root query

    :return: :py:class:`Flask.Response` -- response index file
    """
    return redirect('index.html')


@blueprint.route(SERVE_INFO)
def model_info():
    """
    Get model description

    :return: :py:class:`Flask.Response` -- model description
    """
    model = app.config['model']

    return jsonify(model.description)


@blueprint.route(SERVE_INVOKE_DEFAULT, methods=['POST', 'GET'])
@blueprint.route(SERVE_INVOKE.format(endpoint='<endpoint>'), methods=['POST', 'GET'])
def model_invoke(endpoint: str = 'default'):
    """
    Call model for calculation

    :param endpoint: target endpoint name
    :return: :py:class:`Flask.Response` -- result of calculation
    """
    input_dict = parse_request(request)

    model = app.config['model']
    if endpoint not in model.endpoints:
        raise Exception('Unknown endpoint {!r}'.format(endpoint))

    output = model.endpoints[endpoint].invoke(input_dict)
    return prepare_response(output, model_name=app.config['model'].model_name,
                            model_version=app.config['model'].model_version,
                            model_endpoint=endpoint)


@blueprint.route(SERVE_BATCH_DEFAULT, methods=['POST'])
@blueprint.route(SERVE_BATCH.format(endpoint='<endpoint>'), methods=['POST'])
def model_batch(endpoint: str = 'default'):
    """
    Call model for calculation in batch mode

    :param endpoint: target endpoint name
    :return: :py:class:`Flask.Response` -- result of calculation
    """
    input_dicts = parse_batch_request(request)

    model = app.config['model']
    if endpoint not in model.endpoints:
        raise Exception('Unknown endpoint {!r}'.format(endpoint))

    responses = [model.endpoints[endpoint].invoke(input_dict) for input_dict in input_dicts]
    return prepare_response(responses, model_name=app.config['model'].model_name,
                            model_version=app.config['model'].model_name,
                            model_endpoint=endpoint)


@blueprint.route(SERVE_HEALTH_CHECK)
def healthcheck():
    """
    Check that model is OK

    :return: str -- status string
    """
    return 'OK'


def build_sitemap():
    """
    Build list of valid application URLs

    :return: list[str] -- list of urls
    """
    endpoints: typing.List[str] = []

    for url in ALL_URLS:
        if '{endpoint}' in url:
            for endpoint in app.config['model'].endpoints.keys():
                endpoints.append(url.format(endpoint=endpoint))
        else:
            endpoints.append(url)

    return endpoints


def page_not_found_handler(e):
    """
    Exception handler for page not found error

    :param e: NotFound exception
    :type e: :py:class:`werkzeug.exceptions.NotFound`
    :return: tuple[str, int] -- response with error code
    """
    return jsonify(error=True,
                   message=e.description,
                   valid_urls=build_sitemap()), e.code


def init_model(application):
    """
    Initialize model from app configuration

    :param application: Flask app
    :type application: :py:class:`Flask.app`
    :return: None
    """
    if 'MODEL_FILE' not in application.config:
        raise Exception('No model file provided')

    # Select model binary file path
    model_file_path = application.config['MODEL_FILE']
    LOGGER.info('Loading model from {}'.format(model_file_path))

    # Load model container
    model_container = Model.load(model_file_path)
    application.config['model'] = model_container
    LOGGER.info('Model container has been initialized')

    # Load model endpoints
    endpoints = model_container.endpoints  # force endpoints loading
    LOGGER.info('Loaded endpoints: {}'.format(list(endpoints.keys())))


def create_application():
    """
    Create Flask application and register blueprints

    :return: :py:class:`Flask.app` -- Flask application instance
    """
    static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    application = Flask(__name__, static_url_path='', static_path=static_folder)

    application.register_blueprint(blueprint)

    return application


def init_application(args=None):
    """
    Initialize configured Flask application instance
    Overall configuration priority: config_default.py, env::FLASK_APP_SETTINGS_FILES file,
    ENV parameters, CLI parameters

    :param args: arguments if provided
    :type args: :py:class:`argparse.Namespace` or None
    :return: :py:class:`Flask.app` -- application instance
    """
    application = create_application()
    configure_application(application, args)

    # Put a model object into application configuration
    init_model(application)
    application.register_error_handler(404, page_not_found_handler)

    return application


def serve_model(args):
    """
    Serve model

    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    logging.info('Legion pyserve initializing')
    application = init_application(args)

    application.run(host=application.config['LEGION_ADDR'],
                    port=application.config['LEGION_PORT'],
                    debug=application.config['DEBUG'],
                    use_reloader=False)

    return application
