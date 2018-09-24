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
import itertools

import legion.config
import legion.http
import legion.model
import legion.pymodel
import legion.k8s.properties
import legion.k8s.utils
from flask import Flask, Blueprint, request, jsonify, redirect, render_template
from flask import current_app as app

LOGGER = logging.getLogger(__name__)
blueprint = Blueprint('pyserve', __name__)

SERVE_ROOT = '/'
SERVE_INFO = '/api/model/{model_id}/{model_version}/info'
SERVE_INVOKE = '/api/model/{model_id}/{model_version}/invoke/{endpoint}'
SERVE_INVOKE_DEFAULT = '/api/model/{model_id}/{model_version}/invoke'
SERVE_BATCH = '/api/model/{model_id}/{model_version}/batch/{endpoint}'
SERVE_BATCH_DEFAULT = '/api/model/{model_id}/{model_version}/batch'
SERVE_PROPERTIES = '/api/model/{model_id}/{model_version}/properties'
SERVE_EMIT_PROPERTIES = '/api/model/{model_id}/{model_version}/emit-properties-update'
SERVE_HEALTH_CHECK = '/healthcheck'

ALL_URLS = SERVE_ROOT, \
           SERVE_INFO, \
           SERVE_INVOKE, SERVE_INVOKE_DEFAULT, \
           SERVE_BATCH, SERVE_BATCH_DEFAULT, \
           SERVE_PROPERTIES, SERVE_EMIT_PROPERTIES, \
           SERVE_HEALTH_CHECK


def validate_model_id(model_id, model_version):
    """
    Check that passed model info is equal to current model info

    :param model_id: model id
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :return: None
    """
    if model_id != app.config['model'].model_id:
        raise Exception('Invalid model handler: {}, not {}'.format(app.config['model'].model_id, model_id))
    if model_version != app.config['model'].model_version:
        raise Exception('Invalid model handler: {}, not {}'.format(app.config['model'].model_version, model_version))


@blueprint.route(SERVE_ROOT)
def root():
    """
    Return static file for root query

    :return: :py:class:`Flask.Response` -- response index file
    """
    return redirect('index.html')


@blueprint.route(SERVE_INFO.format(model_id='<model_id>', model_version='<model_version>'))
def model_info(model_id, model_version):
    """
    Get model description

    :param model_id: model id
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :return: :py:class:`Flask.Response` -- model description
    """
    validate_model_id(model_id, model_version)

    model = app.config['model']

    return jsonify(model.description)


@blueprint.route(SERVE_INVOKE_DEFAULT.format(model_id='<model_id>', model_version='<model_version>'),
                 methods=['POST', 'GET'])
@blueprint.route(SERVE_INVOKE.format(model_id='<model_id>', model_version='<model_version>',
                                     endpoint='<endpoint>'), methods=['POST', 'GET'])
def model_invoke(model_id, model_version, endpoint='default'):
    """
    Call model for calculation

    :param model_id: model name
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :param endpoint: target endpoint name
    :type endpoint: str
    :return: :py:class:`Flask.Response` -- result of calculation
    """
    validate_model_id(model_id, model_version)

    input_dict = legion.http.parse_request(request)

    model = app.config['model']
    if endpoint not in model.endpoints:
        raise Exception('Unknown endpoint {!r}'.format(endpoint))

    output = model.endpoints[endpoint].invoke(input_dict)

    return legion.http.prepare_response(output)


@blueprint.route(SERVE_BATCH_DEFAULT.format(model_id='<model_id>', model_version='<model_version>'),
                 methods=['POST'])
@blueprint.route(SERVE_BATCH.format(model_id='<model_id>', model_version='<model_version>', endpoint='<endpoint>'),
                 methods=['POST'])
def model_batch(model_id, model_version, endpoint='default'):
    """
    Call model for calculation in batch mode

    :param model_id: model name
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :param endpoint: target endpoint name
    :type endpoint: str
    :return: :py:class:`Flask.Response` -- result of calculation
    """
    validate_model_id(model_id, model_version)

    input_dicts = legion.http.parse_batch_request(request)

    model = app.config['model']
    if endpoint not in model.endpoints:
        raise Exception('Unknown endpoint {!r}'.format(endpoint))

    responses = [model.endpoints[endpoint].invoke(input_dict) for input_dict in input_dicts]

    return legion.http.prepare_response(responses)


@blueprint.route(SERVE_HEALTH_CHECK)
def healthcheck():
    """
    Check that model is OK

    :return: str -- status string
    """
    return 'OK'


@blueprint.route(SERVE_PROPERTIES.format(model_id='<model_id>', model_version='<model_version>'))
def model_properties(model_id, model_version):
    """
    Get model properties

    :param model_id: model id
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :return: :py:class:`Flask.Response` -- model properties
    """
    validate_model_id(model_id, model_version)

    model = app.config['model']

    return jsonify(model.properties.data)


@blueprint.route(SERVE_EMIT_PROPERTIES.format(model_id='<model_id>', model_version='<model_version>'))
def emit_properties_update_signal(model_id, model_version):
    """
    Emit signal for properties update

    :param model_id: model id
    :type model_id: str
    :param model_version: model version
    :type model_version: str
    :return: :py:class:`Flask.Response` -- model properties
    """
    validate_model_id(model_id, model_version)

    model = app.config['model']
    model.properties.emit_update_signal()

    return jsonify(status=True)


def build_sitemap():
    """
    Build list of valid application URLs

    :return: list[str] -- list of urls
    """
    non_endpoint = [
        url.format(model_id=app.config['model'].model_id,
                   model_version=app.config['model'].model_version)
        for url in ALL_URLS
        if '{endpoint}' not in url
    ]
    with_endpoint = [
        [
            url.format(model_id=app.config['model'].model_id,
                       model_version=app.config['model'].model_version,
                       endpoint=endpoint)
            for url in ALL_URLS
            if '{endpoint}' in url
        ]
        for endpoint in app.config['model'].endpoints.keys()
    ]
    return non_endpoint + list(itertools.chain(*with_endpoint))


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
    model_container = legion.pymodel.Model.load(model_file_path)
    application.config['model'] = model_container
    LOGGER.info('Model container has been initialized')

    # Load model endpoints
    endpoints = model_container.endpoints  # force endpoints loading
    LOGGER.info('Loaded endpoints: {}'.format(list(endpoints.keys())))

    # Load model properties
    LOGGER.info('Setting properties to loaded properties {!r} (id: {})'.format(
        model_container.properties,
        id(model_container.properties)
    ))
    legion.model.set_properties(model_container.properties)

    # Force reload if code run in a cluster and model required any properties
    if legion.k8s.utils.is_code_run_in_cluster() and model_container.required_props:
        legion.model.properties.load()
        legion.model.properties.start_update_watcher()
    else:
        LOGGER.info('Ignoring running of update watcher because model is not ran in a cluster '
                    'or model does not contain required props')


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
    legion.http.configure_application(application, args)

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
