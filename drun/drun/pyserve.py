import os
import logging
import consul
from flask import Flask, Blueprint, request, jsonify, redirect
from flask import current_app as app

import drun.model as mlmodel
import drun.utils as utils

log = logging.getLogger('pyserve')

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


@blueprint.route('/api/model/<model_id>/info')
def model_info(model_id):
    assert model_id == app.config['MODEL_ID']

    model = app.config['model']

    return jsonify(model.description())


@blueprint.route('/api/model/<model_id>/invoke', methods=['POST', 'GET'])
def model_invoke(model_id):
    assert model_id == app.config['MODEL_ID']

    input_dict = protocol_handler.parse_request(request)

    model = app.config['model']

    vector = model.transform(input_dict)

    output = model.apply(vector)

    return protocol_handler.prepare_response(output)


@blueprint.route('/healthcheck')
def healthcheck():
    return 'OK'


def init_model(app):
    if 'model_bundle_file' in app.config:
        model = mlmodel.load_model(app.config['model_bundle_file'])
    else:
        model = mlmodel.DummyModel()
    return model


def init_application():
    app = Flask(__name__, static_url_path='/')
    app.config.from_pyfile('config_default.py')
#   Instance relative configuration
    instance_config = os.path.join(app.instance_path, 'config.py')
    if os.path.exists(instance_config):
        app.config.from_pyfile(instance_config)

    app.config['DEBUG'] = True

    cfg_addr = app.config['LEGION_ADDR']
    if cfg_addr == "" or cfg_addr == "0.0.0.0":
        app.config['LEGION_ADDR'] = utils.detect_ip()

    # Put a model object into application configuration
    app.config['model'] = init_model(app)

    app.register_blueprint(blueprint)

    return app


def register_service(app):

    client = consul.Consul(
        host=app.config['CONSUL_ADDR'],
        port=app.config['CONSUL_PORT'])

    service = app.config['MODEL_ID']

    addr = app.config['LEGION_ADDR']
    port = app.config['LEGION_PORT']

    client.agent.service.register(
        service,
        address=addr,
        port=port,
        tags=['legion', 'model']
    )


def serve_model(args):
    logging.basicConfig(level=logging.DEBUG)
    logging.info("legion pyserve initializing")
    app = init_application()
    logging.info("legion ready")

    register_service(app)

    app.run(host=app.config['LEGION_ADDR'],
            port=app.config['LEGION_PORT'],
            use_reloader=False
            )
