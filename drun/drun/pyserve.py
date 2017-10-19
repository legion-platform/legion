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

import os
import logging
import consul
from flask import Flask, Blueprint, request, jsonify, redirect
from flask import current_app as app

import drun.io
import drun.model as mlmodel
import drun.utils as utils


LOGGER = logging.getLogger('pyserve')


class HttpProtocolHandler:

    def parse_request(self, input_request):
        """
        Produce a model input dictionary from HTTP request (GET/POST fields, and Files)

        :param input_request: request object
        :type input_request: :py:class:`Flask.request`
        :return: dict with requested fields
        """
        result = {}

        # Fill in URL parameters
        for k in input_request.args:
            result[k] = input_request.args[k]

        # Fill in POST parameters
        for k in input_request.form:
            result[k] = input_request.form[k]

        # Fill in Files:
        for k in input_request.files:
            result[k] = input_request.files[k].read()

        return result

    def prepare_response(self, response):
        """
        Produce an HTTP response from a model output

        :param response: a model output
        :type response: dict[str, any]
        :return: bytes
        """
        return jsonify(response)


protocol_handler = HttpProtocolHandler()

blueprint = Blueprint('pyserve', __name__)


@blueprint.route('/')
def root():
    """
    Return static file for root query

    :return: :py:class:`Flask.Response` -- response index file
    """
    return redirect('index.html')


# TODO: Add model check
@blueprint.route('/api/model/<model_id>/info')
def model_info(model_id):
    """
    Get model description

    :param model_id: model id
    :type model_id: str
    :return: :py:class:`Flask.Response` -- model description
    """
    # assert model_id == app.config['MODEL_ID']

    model = app.config['model']

    return jsonify(model.description)


# TODO: Add model check
@blueprint.route('/api/model/<model_id>/invoke', methods=['POST', 'GET'])
def model_invoke(model_id):
    """
    Call model for calculation

    :param model_id: model name
    :type model_id: str
    :return: :py:class:`Flask.Response` -- result of calculation
    """
    # TODO single configuration for Flask/CLI
    # assert model_id == app.config['MODEL_ID']

    input_dict = protocol_handler.parse_request(request)

    model = app.config['model']

    output = model.apply(input_dict)

    return protocol_handler.prepare_response(output)


@blueprint.route('/healthcheck')
def healthcheck():
    """
    Check that model is OK

    :return: str -- status string
    """
    return 'OK'


def init_model(app):
    """
    Load model from app configuration

    :param app: Flask app
    :type app: :py:class:`Flask.app`
    :return: model instance
    """
    if 'MODEL_FILE' in app.config:
        file = app.config['MODEL_FILE']
        LOGGER.info("Loading model from %s", file)
        with drun.io.ModelContainer(file) as container:
            model = container.model
    else:
        LOGGER.info("Instantiated dummy model")
        model = mlmodel.DummyModel()
    return model


def create_application():
    """
    Create Flask application

    :return: :py:class:`Flask.app` -- Flask application instance
    """
    app = Flask(__name__, static_url_path='')
    app.config.from_pyfile('config_default.py')
#   Instance relative configuration
    instance_config = os.path.join(app.instance_path, 'config.py')
    if os.path.exists(instance_config):
        app.config.from_pyfile(instance_config)

    app.config['DEBUG'] = True

    cfg_addr = app.config['LEGION_ADDR']
    if cfg_addr == "" or cfg_addr == "0.0.0.0":
        app.config['LEGION_ADDR'] = utils.detect_ip()

    app.register_blueprint(blueprint)

    return app


def register_service(app):
    """
    Register application in Consul

    :param app: Flask application instance
    :type app: :py:class:`Flask.app`
    :return: None
    """
    client = consul.Consul(
        host=app.config['CONSUL_ADDR'],
        port=app.config['CONSUL_PORT'])

    service = app.config['MODEL_ID']

    addr = app.config['LEGION_ADDR']
    port = app.config['LEGION_PORT']

    LOGGER.info("Registering model service %s @ http://%s:%s", service, addr, port)
    client.agent.service.register(
        service,
        address=addr,
        port=port,
        tags=['legion', 'model']
    )


def apply_cli_args(flask_app, args):
    """
    Set Flask app instance configuration from arguments

    :param flask_app: Flask app instance
    :type flask_app: :py:class:`Flask.app`
    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    args_dict = vars(args)
    for k, v in args_dict.items():
        if v is not None:
            flask_app.config[k.upper()] = v


def init_application(args):
    """
    Initialize configured Flask application instance

    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`Flask.app` -- application instance
    """
    app = create_application()
    apply_cli_args(app, args)
    # Put a model object into application configuration
    app.config['model'] = init_model(app)
    return app


def serve_model(args):
    """
    Serve models
    Overall configuration priority: config_default.py, instance/config.py, CLI parameters

    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    logging.info("legion pyserve initializing")
    app = init_application(args)

    register_service(app)
    logging.info("consensus achieved")

    app.run(host=app.config['LEGION_ADDR'],
            port=app.config['LEGION_PORT'],
            use_reloader=False)
