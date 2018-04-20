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

import legion.config
import legion.containers.k8s
import legion.external.grafana
import legion.http
import legion.io
from flask import Flask, Blueprint
from flask import current_app as app

LOGGER = logging.getLogger(__name__)
blueprint = Blueprint('apiserver', __name__)

EDI_VERSION = '1.0'
EDI_ROOT = '/'
EDI_DEPLOY = '/api/{version}/deploy'
EDI_UNDEPLOY = '/api/{version}/undeploy'
EDI_SCALE = '/api/{version}/scale'
EDI_INSPECT = '/api/{version}/inspect'
EDI_INFO = '/api/{version}/info'

ALL_EDI_API_ENDPOINTS = EDI_DEPLOY, EDI_UNDEPLOY, EDI_SCALE, EDI_INSPECT, EDI_INFO


def build_blueprint_url(endpoint_url_template):
    """
    Build endpoint url from template

    :param endpoint_url_template: endpoint url template
    :type endpoint_url_template: str
    :return: str -- builded url
    """
    return endpoint_url_template.format(version=EDI_VERSION)


def authenticate(user, password):
    """
    Authenticate validator. For token auth use 'token' as user and token value as password

    :param user: user or 'token' (for token auth)
    :type user: str or None
    :param password: password or token value
    :type password: str or None
    :raises Exception: if something wrong with authentication process
    :return: bool -- is user authenticated for performing any operations
    """
    if not app.config['AUTH_ENABLED']:
        return True

    if user == 'token':
        if app.config['AUTH_TOKEN_ENABLED']:
            return password == app.config['AUTH_TOKEN']

        return False

    # TODO: Add LDAP authorisation
    return False


@blueprint.route(build_blueprint_url(EDI_ROOT), methods=['GET'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
def root():
    """
    Root API endpoint

    :return: dict -- root information
    """
    return {
        'component': 'EDI server',
        'version': EDI_VERSION,
        'endpoints': [build_blueprint_url(url) for url in ALL_EDI_API_ENDPOINTS]
    }


@blueprint.route(build_blueprint_url(EDI_DEPLOY), methods=['POST'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
@legion.http.populate_fields(image=str, count=int, k8s_image=str)
@legion.http.requested_fields('image')
def deploy(image, count=1, k8s_image=None):
    """
    Deploy API endpoint

    :param image: Docker image for deploy (for jybernetes deployment and local pull)
    :type image: str
    :param count: count of pods to create
    :type count: int
    :param k8s_image: Docker image for kubernetes deployment
    :type k8s_image: str or None
    :return: bool -- True
    """
    register_on_grafana = app.config['REGISTER_ON_GRAFANA']
    legion.containers.k8s.deploy(app.config['CLUSTER_STATE'], app.config['CLUSTER_SECRETS'],
                                 image, k8s_image, count,
                                 register_on_grafana)
    return True


@blueprint.route(build_blueprint_url(EDI_UNDEPLOY), methods=['POST'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
@legion.http.populate_fields(model=str, grace_period=int)
@legion.http.requested_fields('model')
def undeploy(model, grace_period=0):
    """
    Undeploy API endpoint

    :param model: model id
    :type model: str
    :param grace_period: grace period for removing
    :type grace_period: int
    :return: bool -- True
    """
    register_on_grafana = app.config['REGISTER_ON_GRAFANA']
    legion.containers.k8s.undeploy(app.config['CLUSTER_STATE'], app.config['CLUSTER_SECRETS'],
                                   model, grace_period,
                                   register_on_grafana)
    return True


@blueprint.route(build_blueprint_url(EDI_SCALE), methods=['POST'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
@legion.http.populate_fields(model=str, count=int)
@legion.http.requested_fields('model')
def scale(model, count):
    """
    Scale API endpoint

    :param model: model id
    :type model: str
    :param count: count of pods to create
    :type count: int
    :return: bool -- True
    """
    legion.containers.k8s.scale(app.config['CLUSTER_STATE'], app.config['CLUSTER_SECRETS'],
                                model, count)
    return True


@blueprint.route(build_blueprint_url(EDI_INSPECT), methods=['GET'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
def inspect():
    """
    Inspect API endpoint

    :return: dict -- state of cluster models
    """
    model_deployments = legion.containers.k8s.inspect(app.config['CLUSTER_STATE'], app.config['CLUSTER_SECRETS'])
    # TODO: Change transform to dict algorithm
    return [{f: getattr(x, f) for f in x._fields} for x in model_deployments]


@blueprint.route(build_blueprint_url(EDI_INFO), methods=['GET'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
def info():
    """
    Info API endpoint

    :return: dict -- state of cluster
    """
    return app.config['CLUSTER_STATE']


def create_application():
    """
    Create Flask application and register blueprints

    :return: :py:class:`Flask.app` -- Flask application instance
    """
    application = Flask(__name__, static_url_path='')

    application.register_blueprint(blueprint)

    return application


def load_cluster_config(application):
    """
    Load cluster configuration into Flask

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :return: None
    """
    application.config['CLUSTER_SECRETS'] = legion.containers.k8s.load_secrets(
        application.config['CLUSTER_SECRETS_PATH'])
    application.config['CLUSTER_STATE'] = legion.containers.k8s.load_config(application.config['CLUSTER_CONFIG_PATH'])


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
    load_cluster_config(application)

    return application


def serve(args):
    """
    Serve apiserver

    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: None
    """
    logging.info('Legion api server initializing')
    application = init_application(args)

    application.run(host=application.config['LEGION_API_ADDR'],
                    port=application.config['LEGION_API_PORT'],
                    debug=application.config['DEBUG'],
                    use_reloader=False)

    return application
