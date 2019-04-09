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
from datetime import datetime, timedelta

import jwt
from flask import Flask, Blueprint, render_template, request
from flask import current_app as app

from legion.sdk.clients.model import ModelClient
from legion.sdk.containers.definitions import ModelDeploymentDescription
from legion.sdk.definitions import EDI_INFO, EDI_GENERATE_TOKEN, EDI_DEPLOY, EDI_UNDEPLOY, EDI_SCALE, EDI_INSPECT, \
    EDI_VERSION, EDI_ROOT, EDI_API_ROOT
from legion.services.k8s.enclave import Enclave
from legion.services.k8s.exceptions import UnknownDeploymentForModelService
from legion.services.k8s.utils import load_secrets
from legion.services.k8s import utils
from legion.services.edi import http
from legion.services.edi.http import configure_application

LOGGER = logging.getLogger(__name__)
blueprint = Blueprint('apiserver', __name__)
TEMPLATES_FOLDER = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir, 'static', 'edi')
)
AUTH_COOKIE_NAME = '_oauth2_proxy'

ALL_EDI_API_ENDPOINTS = EDI_DEPLOY, EDI_UNDEPLOY, EDI_SCALE, EDI_INSPECT, EDI_INFO, EDI_GENERATE_TOKEN


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


def return_model_deployments(model_deployments):
    """
    Return JSON serializable information about deployments

    :param model_deployments: list of model deployment descriptions to return
    :type model_deployments: list[:py:class:`legion.k8s.definitions.ModelDeploymentDescription`]
    :return:
    """
    return [deployment.as_dict() for deployment in model_deployments]


@blueprint.route(build_blueprint_url(EDI_ROOT), methods=['GET'])
def root():
    """
    Root endpoint for authorisation

    :return: dict -- root information
    """
    token = request.cookies.get(AUTH_COOKIE_NAME, 'INVALID COOKIE')
    return render_template('index.html', token=token)


@blueprint.route(build_blueprint_url(EDI_API_ROOT), methods=['GET'])
@http.provide_json_response
@http.authenticate(authenticate)
def api_root():
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
@http.provide_json_response
@http.authenticate(authenticate)
@http.populate_fields(image=str, model_iam_role=str, count=int, livenesstimeout=int, readinesstimeout=int,
                      memory=str, cpu=str)
@http.requested_fields('image')
def deploy(image, model_iam_role=None, count=1, livenesstimeout=2, readinesstimeout=2, memory=None, cpu=None):
    """
    Deploy API endpoint

    K8S API functions will be invoked in the next order:
    - CoreV1Api.list_namespaced_service (to get information about actual model services)
    If there is deployed model with same image:
      - AppsV1Api.list_namespaced_deployment (to get information of service's deployment)
    if there is no any deployed model with same image:
      - CoreV1Api.list_namespaced_service (to check is there any model with same model id / version)
      - AppsV1Api.create_namespaced_deployment (to create model deployment)
      - AppsV1Api.list_namespaced_deployment (to ensure that model deployment has been created)
      - CoreV1Api.create_namespaced_service (to create model service)
      - CoreV1Api.list_namespaced_service (to ensure that model service has been created)

    :param image: Docker image for deploy (for kubernetes deployment and local pull)
    :type image: str
    :param model_iam_role: IAM role to be used at model pod
    type model_iam_role: str
    :param count: count of pods to create
    :type count: int
    :param livenesstimeout: time in seconds for liveness check
    :type livenesstimeout: int
    :param readinesstimeout: time in seconds for readiness check
    :type readinesstimeout: int
    :param memory: limit memory for model deployment
    :type memory: str
    :param cpu: limit cpu for model deployment
    :type cpu: str
    :return: bool -- True
    """
    LOGGER.info('Command: deploy image {} with {} replicas, livenesstimeout={!r}, readinesstimeout={!r},'
                'memory={}, cpu={} and {!r} IAM role'.format(image, count, livenesstimeout, readinesstimeout, memory,
                                                             cpu, model_iam_role))

    _, model_service = app.config['ENCLAVE'].deploy_model(
        image, model_iam_role, count, livenesstimeout, readinesstimeout, memory, cpu
    )

    return return_model_deployments([ModelDeploymentDescription.build_from_model_service(model_service)])


@blueprint.route(build_blueprint_url(EDI_UNDEPLOY), methods=['POST'])
@http.provide_json_response
@http.authenticate(authenticate)
@http.populate_fields(model=str, version=str, grace_period=int, ignore_not_found=bool)
@http.requested_fields('model')
def undeploy(model, version=None, grace_period=0, ignore_not_found=False):
    """
    Undeploy API endpoint

    K8S API functions will be invoked in the next order:
    - CoreV1Api.list_namespaced_service (to get information about actual model services)
    Per each service that should be undeployed (N-times):
      - AppsV1Api.list_namespaced_deployment (to get information of service's deployment)
      - CoreV1Api.delete_namespaced_service (to remove model service)
      - CoreV1Api.list_namespaced_service (to ensure that service has been removed)
      - AppsV1beta1Api.delete_namespaced_deployment (to remove deployment)
      - AppsV1Api.list_namespaced_deployment (to ensure that deployment has been removed)


    :param model: model id
    :type model: strset jinja folder
    :param version: (Optional) specific model version
    :type version: str or None
    :param grace_period: grace period for removing
    :type grace_period: int
    :param ignore_not_found: (Optional) ignore exception if cannot find models
    :type ignore_not_found: bool
    :return: bool -- True
    """
    LOGGER.info('Command: undeploy model with id={}, version={} with grace period {}s'
                .format(model, version, grace_period))
    model_deployments = []
    LOGGER.info('Gathering information about models with id={} version={}'
                .format(model, version))
    model_services = app.config['ENCLAVE'].get_models_strict(model, version, ignore_not_found)

    for model_service in model_services:
        model_deployments.append(
            ModelDeploymentDescription.build_from_model_service(model_service)
        )

        model_service.delete(grace_period)

    return return_model_deployments(model_deployments)


@blueprint.route(build_blueprint_url(EDI_SCALE), methods=['POST'])
@http.provide_json_response
@http.authenticate(authenticate)
@http.populate_fields(model=str, count=int, version=str)
@http.requested_fields('model', 'count')
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
    model_deployments = []
    LOGGER.info('Gathering information about models with id={} version={}'
                .format(model, version))
    model_services = app.config['ENCLAVE'].get_models_strict(model, version)

    for model_service in model_services:
        LOGGER.info('Changing scale for model (id={}, version={}) from {} to {}'
                    .format(model_service.id, model_service.version, model_service.scale, count))
        model_service.scale = count

        model_deployments.append(
            ModelDeploymentDescription.build_from_model_service(model_service)
        )

    return return_model_deployments(model_deployments)


@blueprint.route(build_blueprint_url(EDI_INSPECT), methods=['GET'])
@http.provide_json_response
@http.authenticate(authenticate)
@http.populate_fields(model=str, version=str)
def inspect(model=None, version=None):
    """
    Inspect API endpoint

    :return: dict -- state of cluster models
    """
    LOGGER.info('Command: inspect with model={}, version={}'.format(model, version))
    model_deployments = []
    LOGGER.info('Gathering information about models with id={} version={}'
                .format(model, version))
    model_services = app.config['ENCLAVE'].get_models(model, version)

    for model_service in model_services:
        try:
            model_api_info = {}

            model_client = ModelClient.build_from_model_service(model_service)

            try:
                model_api_info['result'] = model_client.info()
                model_api_ok = True
            except Exception as model_api_exception:
                LOGGER.error('Cannot connect to model <{}> endpoint to get info: {}'.format(model_service,
                                                                                            model_api_exception))
                model_api_info['exception'] = str(model_api_exception)
                model_api_ok = False

            model_deployments.append(ModelDeploymentDescription.build_from_model_service(
                model_service,
                model_api_ok, model_api_info
            ))
        except UnknownDeploymentForModelService:
            LOGGER.debug('Ignoring error about unknown deployment for model service {!r}'.format(model_service))

    return return_model_deployments(model_deployments)


@blueprint.route(build_blueprint_url(EDI_INFO), methods=['GET'])
@http.provide_json_response
@http.authenticate(authenticate)
def info():
    """
    Info API endpoint.

    DEPRECATED. WILL BE REMOVED IN MAJOR RELEASE
    TODO: Remove in major release

    :return: dict -- state of cluster
    """
    return {}


@blueprint.route(build_blueprint_url(EDI_GENERATE_TOKEN), methods=['POST'])
@http.provide_json_response
@http.authenticate(authenticate)
@http.populate_fields(model_id=str, model_version=str, expiration_date=str)
@http.requested_fields('model_id', 'model_version')
def generate_token(model_id, model_version, expiration_date=None):
    """
    Generate JWT token

    :return: dict -- state of cluster
    """
    jwt_secret = app.config['JWT_CONFIG']['jwt.secret']
    jwt_exp_date = None
    jwt_exp_date_str = None
    if expiration_date:
        jwt_exp_date_str = expiration_date
    elif 'jwt.exp.datetime' in app.config['JWT_CONFIG']:
        jwt_exp_date_str = app.config['JWT_CONFIG']['jwt.exp.datetime']

    if jwt_exp_date_str:
        try:
            jwt_exp_date = datetime.strptime(jwt_exp_date_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

    max_jwt_exp_date = datetime.utcnow() + timedelta(minutes=int(app.config['JWT_CONFIG']['jwt.max.length.minutes']))
    if jwt_exp_date and jwt_exp_date > max_jwt_exp_date:
        jwt_exp_date = max_jwt_exp_date
        LOGGER.info('Maximum token TTL exceeded. Token expiration date set to %s', max_jwt_exp_date)
    elif not jwt_exp_date or jwt_exp_date < datetime.now():
        jwt_life_length = timedelta(minutes=int(app.config['JWT_CONFIG']['jwt.length.minutes']))
        jwt_exp_date = datetime.utcnow() + jwt_life_length
    token = jwt.encode({'exp': jwt_exp_date,
                        'model_id': [model_id],
                        'model_version': [model_version]},
                       jwt_secret, algorithm='HS256').decode('utf-8')
    return {'token': token, 'exp': jwt_exp_date}


def create_application():
    """
    Create Flask application, register blueprints and templates folder

    :return: :py:class:`Flask.app` -- Flask application instance
    """
    application = Flask(__name__,
                        static_url_path='',
                        template_folder=TEMPLATES_FOLDER)

    application.register_blueprint(blueprint)
    application.create_jinja_environment()

    return application


def get_application_enclave(application):
    """
    Build enclave's object

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :return :py:class:`legion.k8s.enclave.Enclave`
    """
    return Enclave(application.config['NAMESPACE'])


def load_cluster_config(application):
    """
    Load cluster configuration into Flask config

    :param application: Flask app instance
    :type application: :py:class:`Flask.app`
    :return: None
    """
    if not application.config['NAMESPACE']:
        application.config['NAMESPACE'] = utils.get_current_namespace()

    application.config['ENCLAVE'] = get_application_enclave(application)
    application.config['CLUSTER_SECRETS'] = load_secrets(application.config['CLUSTER_SECRETS_PATH'])
    application.config['JWT_CONFIG'] = load_secrets(application.config['JWT_CONFIG_PATH'])


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
