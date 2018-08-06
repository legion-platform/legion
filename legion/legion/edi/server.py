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
import legion.k8s
import legion.external.grafana
import legion.http
import legion.model
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
@legion.http.populate_fields(image=str, count=int)
@legion.http.requested_fields('image')
def deploy(image, count=1):
    """
    Deploy API endpoint

    :param image: Docker image for deploy (for jybernetes deployment and local pull)
    :type image: str
    :param count: count of pods to create
    :type count: int
    :return: bool -- True
    """
    LOGGER.info('Command: deploy image {} with {} replicas'.format(image, count))
    model_service = app.config['ENCLAVE'].deploy_model(image, count)

    if app.config['REGISTER_ON_GRAFANA']:
        if not app.config['GRAFANA_CLIENT'].is_dashboard_exists(model_service.id, model_service.version):
            app.config['GRAFANA_CLIENT'].create_dashboard_for_model(model_service.id, model_service.version)
    return True


@blueprint.route(build_blueprint_url(EDI_UNDEPLOY), methods=['POST'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
@legion.http.populate_fields(model=str, version=str, grace_period=int)
@legion.http.requested_fields('model')
def undeploy(model, version=None, grace_period=0):
    """
    Undeploy API endpoint

    :param model: model id
    :type model: str
    :param version: (Optional) specific model version
    :type version: str or None
    :param grace_period: grace period for removing
    :type grace_period: int
    :return: bool -- True
    """
    # TODO: Add tests for multiple versions (parallel models)
    LOGGER.info('Command: undeploy model with id={}, version={} with grace period {}s'
                .format(model, version, grace_period))
    model_services = app.config['ENCLAVE'].get_models_strict(model, version)

    for model_service in model_services:
        if app.config['REGISTER_ON_GRAFANA']:
            if app.config['GRAFANA_CLIENT'].is_dashboard_exists(model, model_service.version):
                app.config['GRAFANA_CLIENT'].remove_dashboard_for_model(model, model_service.version)

        model_service.delete(grace_period)

    return True


@blueprint.route(build_blueprint_url(EDI_SCALE), methods=['POST'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
@legion.http.populate_fields(model=str, count=int, version=str)
@legion.http.requested_fields('model', 'count')
def scale(model, count, version=None):
    """
    Scale API endpoint

    :param model: model id
    :type model: str
    :param count: count of pods to create
    :type count: int
    :param version: (Optional) specific model version
    :type version: str or None
    :return: bool -- True
    """
    LOGGER.info('Command: scale model with id={}, version={} to {} replicas'.format(model, version, count))
    model_services = app.config['ENCLAVE'].get_models_strict(model, version)

    for model_service in model_services:
        model_service.scale = count

    return True


@blueprint.route(build_blueprint_url(EDI_INSPECT), methods=['GET'])
@legion.http.provide_json_response
@legion.http.authenticate(authenticate)
@legion.http.populate_fields(model=str, version=str)
def inspect(model=None, version=None):
    """
    Inspect API endpoint

    :return: dict -- state of cluster models
    """
    LOGGER.info('Command: inspect with model={}, version={}'.format(model, version))
    model_deployments = []
    model_services = app.config['ENCLAVE'].get_models(model, version)

    for model_service in model_services:
        model_api_info = {}

        model_client = legion.model.ModelClient(
            model_id=model_service.id,
            model_version=model_service.version,
            host=model_service.url_with_ip,
            timeout=3
        )
        LOGGER.info('Building model client: {!r}'.format(model_client))

        try:
            model_api_info['result'] = model_client.info()
            model_api_ok = True
        except Exception as model_api_exception:
            LOGGER.error('Cannot connect to model <{}> endpoint to get info: {}'.format(model_service,
                                                                                        model_api_exception))
            model_api_info['exception'] = str(model_api_exception)
            model_api_ok = False

        model_deployments.append(
            legion.k8s.ModelDeploymentDescription(
                status=model_service.status,
                model=model_service.id,
                version=model_service.version,
                image=model_service.image,
                scale=model_service.desired_scale,
                ready_replicas=model_service.scale,
                namespace=model_service.namespace,
                model_api_ok=model_api_ok,
                model_api_info=model_api_info,
            )
        )

    return [x._asdict() for x in model_deployments]


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
    Load cluster configuration into Flask config

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :return: None
    """
    if not application.config['NAMESPACE']:
        application.config['NAMESPACE'] = legion.k8s.get_current_namespace()

    application.config['ENCLAVE'] = legion.k8s.Enclave(application.config['NAMESPACE'])

    application.config['CLUSTER_SECRETS'] = legion.k8s.load_secrets(
        application.config['CLUSTER_SECRETS_PATH'])
    application.config['CLUSTER_STATE'] = legion.k8s.load_config(application.config['CLUSTER_CONFIG_PATH'])

    grafana_client = legion.external.grafana.GrafanaClient(application.config['ENCLAVE'].grafana_service.url,
                                                           application.config['CLUSTER_SECRETS']['grafana.user'],
                                                           application.config['CLUSTER_SECRETS']['grafana.password'])
    application.config['GRAFANA_CLIENT'] = grafana_client


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

    try:
        application.run(host=application.config['LEGION_API_ADDR'],
                        port=application.config['LEGION_API_PORT'],
                        debug=application.config['DEBUG'],
                        use_reloader=False)

        return application
    except Exception as run_exception:
        LOGGER.exception('EDI server exited with exception', exc_info=run_exception)
