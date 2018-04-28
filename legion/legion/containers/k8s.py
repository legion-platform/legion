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
legion k8s functions
"""
import os
import os.path
import typing

import legion
import legion.containers.docker
import legion.containers.headers
import legion.config
import legion.external.grafana
from legion.model import ModelClient

import docker
import docker.errors
import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception
import urllib3
import urllib3.exceptions
import yaml
from legion.utils import normalize_name

ModelDeploymentDescription = typing.NamedTuple('ModelDeploymentDescription', [
    ('status', str),
    ('model', str),
    ('version', str),
    ('image', str),
    ('scale', int),
    ('ready_replicas', int),
    ('namespace', str),
    ('deployment', str),
    ('model_api_ok', bool),
    ('model_api_info', dict),
])


def build_client():
    """
    Configure and returns kubernetes client

    :return: :py:module:`kubernetes.client`
    """
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.config_exception.ConfigException:
        kubernetes.config.load_kube_config()

    # Disable SSL warning for self-signed certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return kubernetes.client.ApiClient()


def load_config(path_to_config):
    """
    Load cluster config

    :param path_to_config: path to cluster config file
    :type path_to_config: str
    :return: dict -- cluster config
    """
    if not os.path.exists(path_to_config):
        raise Exception('config path %s not exists' % path_to_config)

    if not os.path.isfile(path_to_config):
        raise Exception('config path %s is not a file' % path_to_config)

    with open(path_to_config, 'r') as stream:
        return yaml.load(stream)


def load_secrets(path_to_secrets):
    """
    Load all secrets from folder to dict

    :param path_to_secrets: path to secrets directory
    :type path_to_secrets: str
    :return: dict[str, str] -- dict of secret name => secret value
    """
    if not os.path.exists(path_to_secrets):
        raise Exception('secrets path %s not exists' % path_to_secrets)

    if not os.path.isdir(path_to_secrets):
        raise Exception('secrets path %s is not a directory' % path_to_secrets)

    files = [
        (file, os.path.abspath(os.path.join(path_to_secrets, file))) for file
        in os.listdir(path_to_secrets)
        if os.path.isfile(os.path.join(path_to_secrets, file))
    ]

    secrets = {}

    for name, path in files:
        try:
            with open(path, 'r') as stream:
                secrets[name] = stream.read()
                if isinstance(secrets[name], bytes):
                    secrets[name] = secrets[name].decode('utf-8')
        except IOError:
            pass
    return secrets


def find_model_deployment(model_id, namespace='default'):
    """
    Find model deployment by model id

    :param model_id: model id
    :type model_id: str
    :param namespace: namespace
    :type namespace: str
    :return: :py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    all_deployments = extension_api.list_namespaced_deployment(namespace)

    type_label_name = normalize_name(legion.containers.headers.DOMAIN_CONTAINER_TYPE)
    type_label_value = 'model'

    model_id_name = normalize_name(legion.containers.headers.DOMAIN_MODEL_ID)
    model_id_value = normalize_name(model_id)

    for deployment in all_deployments.items:
        if deployment.metadata.labels.get(type_label_name) == type_label_value \
                and deployment.metadata.labels.get(model_id_name) == model_id_value:
            return deployment

    return None


def find_model_service(model_id, model_version=None, namespace='default'):
    """
    Find model service by model id

    :param model_id: model id
    :type model_id: str
    :param model_version: version (Optional)
    :type model_version: str
    :param namespace: namespace
    :type namespace: str
    :return: :py:class:`kubernetes.client.models.v1_service.V1Service`
    """
    client = build_client()

    client_api = kubernetes.client.CoreV1Api(client)
    all_services = client_api.list_namespaced_service(namespace)

    model_id_name = normalize_name(legion.containers.headers.DOMAIN_MODEL_ID)
    model_id_value = normalize_name(model_id)

    model_version_name = normalize_name(legion.containers.headers.DOMAIN_MODEL_VERSION)
    model_version_value = normalize_name(model_version) if model_version is not None else None

    for service in all_services.items:
        if service.metadata.labels.get(model_id_name) == model_id_value \
                and (model_version is None
                     or service.metadata.labels.get(model_version_name) == model_version_value):
            return service

    return None


def find_all_models_deployments(namespace='default'):
    """
    Find all models deployments

    :param namespace: namespace
    :type namespace: str or none for all
    :return: list[:py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`]
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    if namespace:
        all_deployments = extension_api.list_namespaced_deployment(namespace)
    else:
        all_deployments = extension_api.list_deployment_for_all_namespaces()

    type_label_name = normalize_name(legion.containers.headers.DOMAIN_CONTAINER_TYPE)
    type_label_value = 'model'

    model_deployments = [
        deployment
        for deployment in all_deployments.items
        if deployment.metadata.labels.get(type_label_name) == type_label_value
    ]

    return model_deployments


def find_all_services(namespace='', component=''):
    """
    Find all services details
    :param namespace: namespace
    :type namespace: str or none for all
    :type component: filter by specified component value, or none for all
    :return: list[V1Service]
    """
    client = build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    if namespace:
        all_services = core_api.list_namespaced_service(namespace)
    else:
        all_services = core_api.list_service_for_all_namespaces()

    type_label_name = 'legion.component'
    if component:
        all_services = [
            service
            for service in all_services.items
            if service.metadata.labels.get(type_label_name) == component
        ]
    else:
        all_services = all_services.items

    return all_services


def watch_all_services(namespace=''):
    """
    Generate which returns events for services updates
    :param namespace: (optional) Namespace name to follow by
    :return: A tuple (event type [ADDED, DELETED, MODIFIED], service object)
    :rtype: (str, V1Service)
    """
    client = build_client()

    core_api = kubernetes.client.CoreV1Api(client)

    while True:
        try:
            w = kubernetes.watch.Watch()
            if namespace:
                stream = w.stream(core_api.list_namespaced_service, namespace, _request_timeout=60)
            else:
                stream = w.stream(core_api.list_service_for_all_namespaces, _request_timeout=60)
            for event in stream:
                service = event['object']
                event_type = event['type']
                yield (event_type, service)
        except urllib3.exceptions.ReadTimeoutError:
            # Caught ReadTimeoutError
            continue


def find_all_ingresses(namespace=''):
    """
    Find all ingress details
    :param namespace: namespace
    :type namespace: str or none for all
    :type component: filter by specified component value, or none for all
    :return: list[V1beta1Ingress]
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    if namespace:
        all_ingresses = extension_api.list_namespaced_ingress(namespace)
    else:
        all_ingresses = extension_api.list_ingress_for_all_namespaces()

    return all_ingresses.items


def scale_deployment(deployment, new_scale, namespace='default'):
    """
    Scale existed deployment

    :param deployment: deployment which we want to scale
    :type deployment: :py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`
    :param new_scale: new scale
    :type new_scale: int
    :param namespace: namespace
    :type namespace: str
    :return: None
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)

    body = deployment
    deployment.spec.replicas = new_scale

    extension_api.patch_namespaced_deployment(deployment.metadata.name, namespace, body)


def remove_deployment(deployment, namespace='default', grace_period=0):
    """
    Remove existed deployment

    :param deployment: deployment which we want to remove
    :type deployment: `kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`
    :param namespace: namespace
    :type namespace: str
    :param grace_period: The duration in seconds before the object should be deleted.
    Value must be non-negative integer. The value zero indicates delete immediately.
    If this value is nil, the default grace period for the specified type will be used.
    Defaults to a per object value if not specified. zero means delete immediately.
    :type grace_period: int
    :return: None
    """
    client = build_client()

    api_instance = kubernetes.client.AppsV1beta1Api(client)

    body = kubernetes.client.V1DeleteOptions(propagation_policy='Foreground', grace_period_seconds=grace_period)

    api_instance.delete_namespaced_deployment(deployment.metadata.name, namespace, body,
                                              grace_period_seconds=grace_period)


def remove_service(service, namespace='default'):
    """
    Remove existed service

    :param service: service which we want to remove
    :type service: `kubernetes.client.models.v1_service.V1Service`
    :param namespace: namespace
    :type namespace: str
    :return: None
    """
    client = build_client()

    api_instance = kubernetes.client.CoreV1Api(client)

    api_instance.delete_namespaced_service(service.metadata.name, namespace)


def deploy(cluster_config, cluster_secrets, image, k8s_image=None, count=1, register_on_grafana=True):
    """
    Deploy model to kubernetes

    :param cluster_config: cluster configuration
    :type cluster_config: dict
    :param cluster_secrets: secrets with credentials
    :type cluster_secrets: dict[str, str]
    :param image: docker image with model
    :type image: str
    :param k8s_image: specific image for kubernetes cluster
    :type k8s_image: str or None
    :param count: count of pods
    :type count: int
    :param register_on_grafana: register model in grafana (create dashboard)
    :type register_on_grafana: bool
    :return: :py:class:`docker.model.Container` new instance
    """
    namespace = cluster_config.get('namespace')
    client = kubernetes.client

    build_client()

    if k8s_image:
        kubernetes_image = k8s_image
    else:
        kubernetes_image = image

    deployment_name, compatible_labels, model_id, model_version = get_meta_from_docker_image(image)

    if register_on_grafana:
        grafana_url = 'http://%s:%d' % (cluster_config['grafana']['domain'], cluster_config['grafana']['port'])
        grafana_client = legion.external.grafana.GrafanaClient(grafana_url,
                                                               cluster_secrets['grafana.user'],
                                                               cluster_secrets['grafana.password'])

        grafana_client.create_dashboard_for_model(model_id, model_version)

    container_env_variables = {
        legion.config.STATSD_HOST[0]: cluster_config['graphite']['domain'],
        legion.config.STATSD_PORT[0]: str(cluster_config['graphite']['port'])
    }

    container = client.V1Container(
        name='model',
        image=kubernetes_image,
        image_pull_policy='Always',
        env=[
            client.V1EnvVar(name=k, value=v)
            for k, v in container_env_variables.items()
        ],
        ports=[client.V1ContainerPort(container_port=5000, name='api', protocol='TCP')])

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=compatible_labels),
        spec=client.V1PodSpec(containers=[container]))

    deployment_spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=count,
        template=template)

    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name, labels=compatible_labels),
        spec=deployment_spec)

    extensions_v1beta1 = client.ExtensionsV1beta1Api()

    api_response_deployment = extensions_v1beta1.create_namespaced_deployment(
        body=deployment,
        namespace=namespace)

    # Creating a service

    core_v1api = client.CoreV1Api()

    service_selector = {k: v for k, v in compatible_labels.items()
                        if k in [legion.containers.headers.DOMAIN_MODEL_ID,
                                 legion.containers.headers.DOMAIN_MODEL_VERSION]}  # Id and Version
    service_name = "model-%s" % normalize_name(model_id)

    service_spec = client.V1ServiceSpec(
        selector=service_selector,
        ports=[client.V1ServicePort(name='api', protocol='TCP', port=5000, target_port='api')])

    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=service_name, labels=compatible_labels),
        spec=service_spec)

    api_response_service = core_v1api.create_namespaced_service(
        body=service,
        namespace=namespace)

    return [api_response_deployment, api_response_service]


def inspect(cluster_config, cluster_secrets):
    """
    Get model deployments information

    :param cluster_config: cluster configuration
    :type cluster_config: dict
    :param cluster_secrets: secrets with credentials
    :type cluster_secrets: dict[str, str]
    :return: list[:py:class:`legion.containers.k8s.ModelDeploymentDescription`]
    """
    namespace = cluster_config.get('namespace')
    deployments = find_all_models_deployments(namespace)
    models = []

    edge_url = 'http://%s:%d' % (cluster_config['edge']['domain'], cluster_config['edge']['port'])

    for deployment in deployments:
        ready_replicas = deployment.status.ready_replicas
        if not ready_replicas:
            ready_replicas = 0
        replicas = deployment.status.replicas
        if not replicas:
            replicas = 0
        status = 'ok'

        if ready_replicas == 0:
            status = 'fail'
        elif replicas > ready_replicas > 0:
            status = 'warning'

        container_image = deployment.spec.template.spec.containers[0].image

        model_name = deployment.metadata.labels.get(
            normalize_name(legion.containers.headers.DOMAIN_MODEL_ID), '?'
        )
        model_version = deployment.metadata.labels.get(
            normalize_name(legion.containers.headers.DOMAIN_MODEL_VERSION), '?'
        )

        model_api_info = {
            'host': edge_url
        }

        try:
            model_client = ModelClient(model_name, host=edge_url)
            model_api_info['result'] = model_client.info()
            model_api_ok = True
        except Exception as model_api_exception:
            model_api_info['exception'] = str(model_api_exception)
            model_api_ok = False

        model_information = ModelDeploymentDescription(
            status=status,
            model=model_name,
            version=model_version,
            image=container_image,
            scale=replicas,
            ready_replicas=ready_replicas,
            namespace=deployment.metadata.namespace,
            deployment='deployment',
            model_api_ok=model_api_ok,
            model_api_info=model_api_info
        )
        models.append(model_information)

    return models


def undeploy(cluster_config, cluster_secrets, model_id, grace_period=0, register_on_grafana=True):
    """
    Undeploy model pods

    :param cluster_config: cluster configuration
    :type cluster_config: dict
    :param cluster_secrets: secrets with credentials
    :type cluster_secrets: dict[str, str]
    :param model_id: model id
    :type model_id: str
    :param grace_period: grace period time in seconds
    :type grace_period: int
    :param register_on_grafana: has been model register?
    :type register_on_grafana: bool
    :return: None
    """
    namespace = cluster_config.get('namespace')

    service = find_model_service(model_id, namespace)
    if not service:
        raise Exception('Cannot find service for model %s in namespace %s' % (model_id, namespace))
    else:
        remove_service(service, namespace)

    deployment = find_model_deployment(model_id, namespace)
    if not deployment:
        raise Exception('Cannot find deployment for model %s in namespace %s' % (model_id, namespace))
    else:
        remove_deployment(deployment, namespace, grace_period)

    if register_on_grafana:
        grafana_url = 'http://%s:%d' % (cluster_config['grafana']['domain'], cluster_config['grafana']['port'])
        grafana_client = legion.external.grafana.GrafanaClient(grafana_url,
                                                               cluster_secrets['grafana.user'],
                                                               cluster_secrets['grafana.password'])

        if grafana_client.is_dashboard_exists(model_id):
            grafana_client.remove_dashboard_for_model(model_id)


def scale(cluster_config, cluster_secrets, model_id, count):
    """
    Change count of model pods

    :param cluster_config: cluster configuration
    :type cluster_config: dict
    :param cluster_secrets: secrets with credentials
    :type cluster_secrets: dict[str, str]
    :param model_id: model id
    :type model_id: str
    :param count: new count of pods
    :type count: int
    :return: None
    """
    namespace = cluster_config.get('namespace')
    deployment = find_model_deployment(model_id, namespace)
    if not deployment:
        raise Exception('Cannot find deployment for model %s in namespace %s' % (model_id, namespace))
    else:
        scale_deployment(deployment, count, namespace)


def get_meta_from_docker_image(image):
    """
    Build meta fields for kubernetes from docker image. Docker image will be pulled automatically.

    :param image: docker image
    :type image: str
    :return: tuple[str, dict[str, str], str, str] -- deployment name, labels in DNS-1123 format, model id and version
    """
    docker_client = legion.containers.docker.build_docker_client(None)
    try:
        docker_image = docker_client.images.get(image)
    except docker.errors.ImageNotFound:
        docker_image = docker_client.images.pull(image)

    required_headers = [
        legion.containers.headers.DOMAIN_MODEL_ID,
        legion.containers.headers.DOMAIN_MODEL_VERSION,
        legion.containers.headers.DOMAIN_CONTAINER_TYPE
    ]

    model_id = docker_image.labels[legion.containers.headers.DOMAIN_MODEL_ID]
    model_version = docker_image.labels[legion.containers.headers.DOMAIN_MODEL_VERSION]

    if any(header not in docker_image.labels for header in required_headers):
        raise Exception('Missed on of %s labels. Available labels: %s' % (
            ', '.join(required_headers),
            ', '.join(tuple(docker_image.labels.keys()))
        ))

    deployment_name = "model.%s.%s.deployment" % (
        normalize_name(model_id),
        normalize_name(model_version)
    )

    compatible_labels = {
        normalize_name(k): normalize_name(v)
        for k, v in
        docker_image.labels.items()
    }

    return deployment_name, compatible_labels, model_id, model_version
