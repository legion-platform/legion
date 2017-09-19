import os
import logging
import consul
import json
from flask import Flask, Blueprint, request, jsonify, redirect
from flask import current_app as app

import drun.io
import drun.model as mlmodel
import drun.utils as utils


logger = logging.getLogger('pyserve')


class HttpProtocolHandler:

    def parse_request(self, input_request):
        """
        Produces a model input dictionary from HTTP request
        :param input_request: flash.request object
        :return: a dictionary
        """
        # TODO Handle JSON and image upload over MIME multipart
        result = {}

        # Fill in URL parameters
        for k in input_request.args:
            result[k] = input_request.args[k]

        # Fill in POST parameters
        for k in input_request.form:
            result[k] = input_request.form[k]

        return result

    def prepare_response(self, response):
        """
        Produces an HTTP response from a model output
        :param response: a model output
        :return: bytes
        """
        return jsonify(response)


protocol_handler = HttpProtocolHandler()

blueprint = Blueprint('pyserve', __name__)


@blueprint.route('/')
def root():
    return redirect('index.html')

@blueprint.route('/api/model/<model_id>/info')
def model_info(model_id):
#    assert model_id == app.config['MODEL_ID']

    model = app.config['model']

    return jsonify(model.description())


@blueprint.route('/api/model/<model_id>/invoke', methods=['POST', 'GET'])
def model_invoke(model_id):
    # TODO single configuration for Flask/CLI
#    assert model_id == app.config['MODEL_ID']

    input_dict = protocol_handler.parse_request(request)

    model = app.config['model']

    output = model.apply(input_dict)

    return protocol_handler.prepare_response(output)


@blueprint.route('/healthcheck')
def healthcheck():
    return 'OK'


def init_model(app):
    if 'MODEL_FILE' in app.config:
        file = app.config['MODEL_FILE']
        logger.info("Loading model from %s", file)
        model = drun.io.load_model(file)
    else:
        logger.info("Instantiated dummy model")
        model = mlmodel.DummyModel()
    return model


def create_application():
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

    client = consul.Consul(
        host=app.config['CONSUL_ADDR'],
        port=app.config['CONSUL_PORT'])

    service = app.config['MODEL_ID']

    addr = app.config['LEGION_ADDR']
    port = app.config['LEGION_PORT']

    logger.info("Registering model service %s @ http://%s:%s", service, addr, port)
    client.agent.service.register(
        service,
        address=addr,
        port=port,
        tags=['legion', 'model']
    )


def apply_cli_args(flask_app, args):
    v = vars(args)
    for k in v:
        if v[k] is not None:
            flask_app.config[k.upper()] = v[k]


def init_application(args):
    app = create_application()
    apply_cli_args(app, args)
    # Put a model object into application configuration
    app.config['model'] = init_model(app)
    return app


def serve_model(args):
    # Overall configuration priority: config_default.py, instance/config.py, CLI parameters
    logging.info("legion pyserve initializing")
    app = init_application(args)

    register_service(app)
    logging.info("consensus achieved")

    app.run(host=app.config['LEGION_ADDR'],
            port=app.config['LEGION_PORT'],
            use_reloader=False
            )
