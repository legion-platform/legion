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

import legion.config
import legion.external.grafana
import legion.http
import legion.io
import legion.model.model as mlmodel
import legion.utils as utils
from flask import Flask, Blueprint, request, jsonify, redirect
from flask import current_app as app

LOGGER = logging.getLogger(__name__)
blueprint = Blueprint('pyserve', __name__)

SERVE_ROOT = '/'
SERVE_INFO = '/api/model/{model_id}/info'
SERVE_INVOKE = '/api/model/{model_id}/invoke'
SERVE_HEALTH_CHECK = '/healthcheck'


@blueprint.route(SERVE_ROOT)
def root():
    """
    Return static file for root query

    :return: :py:class:`Flask.Response` -- response index file
    """
    return redirect('index.html')


@blueprint.route(SERVE_INFO.format(model_id='<model_id>'))
def model_info(model_id):
    """
    Get model description

    :param model_id: model id
    :type model_id: str
    :return: :py:class:`Flask.Response` -- model description
    """
    if model_id != app.config['MODEL_ID']:
        raise Exception('Invalid model handler: {}, not {}'.format(app.config['MODEL_ID'], model_id))

    model = app.config['model']

    return jsonify(model.description)


@blueprint.route(SERVE_INVOKE.format(model_id='<model_id>'), methods=['POST', 'GET'])
def model_invoke(model_id):
    """
    Call model for calculation

    :param model_id: model name
    :type model_id: str
    :return: :py:class:`Flask.Response` -- result of calculation
    """
    if model_id != app.config['MODEL_ID']:
        raise Exception('Invalid model handler: {}, not {}'.format(app.config['MODEL_ID'], model_id))

    input_dict = legion.http.parse_request(request)

    model = app.config['model']

    output = model.apply(input_dict)

    return legion.http.prepare_response(output)


@blueprint.route(SERVE_HEALTH_CHECK)
def healthcheck():
    """
    Check that model is OK

    :return: str -- status string
    """
    return 'OK'


def init_model(application):
    """
    Load model from app configuration

    :param application: Flask app
    :type application: :py:class:`Flask.app`
    :return: model instance
    """
    if 'MODEL_FILE' in application.config:
        file = application.config['MODEL_FILE']
        LOGGER.info("Loading model from %s", file)
        with legion.io.ModelContainer(file) as container:
            model = container.model
    else:
        raise Exception('Unknown model file')
    return model


def create_application():
    """
    Create Flask application and register blueprints

    :return: :py:class:`Flask.app` -- Flask application instance
    """
    static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    application = Flask(__name__, static_url_path='', static_path=static_folder)

    application.register_blueprint(blueprint)

    return application


def register_dashboard(application):
    """
    Register application in Grafana (create dashboard)

    :param application: Flask application instance
    :type application: :py:class:`Flask.app`
    :return: None
    """
    host = os.environ.get(*legion.config.GRAFANA_URL)
    user = os.environ.get(*legion.config.GRAFANA_USER)
    password = os.environ.get(*legion.config.GRAFANA_PASSWORD)

    print('Creating Grafana client for host: %s, user: %s, password: %s' % (host, user, '*' * len(password)))
    client = legion.external.grafana.GrafanaClient(host, user, password)
    client.create_dashboard_for_model(application.config['MODEL_ID'])


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
    application.config['model'] = init_model(application)

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
