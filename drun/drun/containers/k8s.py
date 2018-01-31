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
DRun k8s functions
"""
import urllib3
import urllib3.exceptions
import typing

import drun
import drun.const.env
import drun.const.headers
import drun.containers.docker
from drun.utils import normalize_name_to_dns_1123

import docker
import docker.errors
import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception

K8S_LOCAL_CLUSTER_DOMAIN = 'cluster.local'


ModelDeploymentDescription = typing.NamedTuple('ModelDeploymentDescription', [
    ('status', str),
    ('model', str),
    ('version', str),
    ('image', str),
    ('scale', int),
    ('ready_replicas', int),
    ('namespace', str),
    ('deployment', str),
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


def get_service_url(service, port_name):
    """
    Get service's url for specific port name

    :param service: service object
    :type service: :py:class:`kubernetes.client.models.v1_service.V1Service`
    :param port_name: name of port
    :type port_name: str
    :return: str -- url to service's port
    """
    ports = {port.name: port for port in service.spec.ports}
    if port_name not in ports:
        raise Exception('Cannot found port named %s in %s service' % (port_name, service.metadata.name))

    url = '%s.%s.svc.%s:%d' % (service.metadata.name,
                               service.metadata.namespace,
                               K8S_LOCAL_CLUSTER_DOMAIN,
                               ports[port_name].port)
    return url


def find_service(service_name, deployment, namespace='default'):
    """
    Find service in cluster

    :param service_name: service name
    :type service_name: str
    :param deployment: deployment name
    :type deployment: str
    :param namespace: namespace
    :type namespace: str
    :return: :py:class:`kubernetes.client.models.v1_service.V1Service` or None
    """
    client = build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    all_services = core_api.list_namespaced_service(namespace)

    valid_services = [
        service
        for service in all_services.items
        if service.metadata.name == '%s-%s' % (deployment, service_name)
    ]

    if len(valid_services) > 1:
        raise Exception('Founded more that one valid service for %s' % service_name)

    if len(valid_services) == 0:
        raise Exception('Cannot found valid service for %s' % service_name)

    return valid_services[0]


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

    type_label_name = normalize_name_to_dns_1123(drun.const.headers.DOMAIN_CONTAINER_TYPE)
    type_label_value = 'model'

    model_id_name = normalize_name_to_dns_1123(drun.const.headers.DOMAIN_MODEL_ID)
    model_id_value = model_id

    for deployment in all_deployments.items:
        if deployment.metadata.labels.get(type_label_name) == type_label_value \
                and deployment.metadata.labels.get(model_id_name) == model_id_value:
            return deployment

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

    type_label_name = normalize_name_to_dns_1123(drun.const.headers.DOMAIN_CONTAINER_TYPE)
    type_label_value = 'model'

    model_deployments = [
        deployment
        for deployment in all_deployments.items
        if deployment.metadata.labels.get(type_label_name) == type_label_value
    ]

    return model_deployments


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


def deploy(namespace, deployment, image, k8s_image=None, scale=1):
    """
    Deploy model to kubernetes

    :param namespace: namespace
    :type namespace: str
    :param deployment: deployment name
    :type deployment: str
    :param image: docker image with model
    :type image: str
    :param k8s_image: specific image for kubernetes cluster
    :type k8s_image: str or None
    :param scale: count of pods
    :type scale: int
    :return: :py:class:`docker.model.Container` new instance
    """
    client = kubernetes.client

    docker_client = drun.containers.docker.build_docker_client(None)
    # grafana_client = build_grafana_client(args)

    graphite_service = find_service('graphite', deployment, namespace)
    graphite_endpoint = get_service_url(graphite_service, 'statsd').split(':')

    grafana_service = find_service('grafana', deployment, namespace)
    grafana_endpoint = get_service_url(grafana_service, 'http')

    consul_service = find_service('consul', deployment, namespace)
    consul_endpoint = get_service_url(consul_service, 'http').split(':')

    # TODO: Question. What do?
    build_client()

    if k8s_image:
        kubernetes_image = k8s_image
    else:
        kubernetes_image = image

    deployment_name, compatible_labels = get_meta_from_docker_image(image)

    container_env_variables = {
        drun.const.env.STATSD_HOST[0]: graphite_endpoint[0],
        drun.const.env.STATSD_PORT[0]: graphite_endpoint[1],
        drun.const.env.GRAFANA_URL[0]: 'http://%s' % grafana_endpoint,
        drun.const.env.CONSUL_ADDR[0]: consul_endpoint[0],
        drun.const.env.CONSUL_PORT[0]: consul_endpoint[1],
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
        replicas=scale,
        template=template)

    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name, labels=compatible_labels),
        spec=deployment_spec)

    extensions_v1beta1 = client.ExtensionsV1beta1Api()

    api_response = extensions_v1beta1.create_namespaced_deployment(
        body=deployment,
        namespace=namespace)

    return api_response


def inspect(namespace=None):
    """
    Get model deployments information

    :param namespace:
    :return: list[:py:class:`drun.containers.k8s.ModelDeploymentDescription`]
    """
    deployments = find_all_models_deployments(namespace)
    models = []

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
            normalize_name_to_dns_1123(drun.const.headers.DOMAIN_MODEL_ID), '?'
        )
        model_version = deployment.metadata.labels.get(
            normalize_name_to_dns_1123(drun.const.headers.DOMAIN_MODEL_VERSION), '?'
        )

        model_information = ModelDeploymentDescription(
            status=status,
            model=model_name,
            version=model_version,
            image=container_image,
            scale=replicas,
            ready_replicas=ready_replicas,
            namespace=deployment.metadata.namespace,
            deployment='deployment'
        )
        models.append(model_information)

    return models


def undeploy(namespace, model_id, grace_period=0):
    """
    Undeploy model pods

    :param namespace: namespace
    :type namespace: str
    :param model_id: model id
    :type model_id: str
    :param grace_period: grace period time in seconds
    :type grace_period: int
    :return: None
    """
    deployment = find_model_deployment(model_id, namespace)
    if not deployment:
        raise Exception('Cannot find deployment for model %s in namespace %s' % (model_id, namespace))
    else:
        remove_deployment(deployment, namespace, grace_period)


def scale(namespace, model_id, count):
    """
    Change count of model pods

    :param namespace: namespace
    :type namespace: str
    :param model_id: model id
    :type model_id: str
    :param count: new count of pods
    :type count: int
    :return: None
    """
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
    :return: tuple[str, dict[str, str]] -- deployment name and labels in DNS-1123 format
    """
    docker_client = drun.containers.docker.build_docker_client(None)
    try:
        docker_image = docker_client.images.get(image)
    except docker.errors.ImageNotFound:
        docker_image = docker_client.images.pull(image)

    required_headers = [
        drun.const.headers.DOMAIN_MODEL_ID,
        drun.const.headers.DOMAIN_MODEL_VERSION,
        drun.const.headers.DOMAIN_CONTAINER_TYPE
    ]

    if any(header not in docker_image.labels for header in required_headers):
        raise Exception('Missed on of %s labels. Available labels: %s' % (
            ', '.join(required_headers),
            ', '.join(tuple(docker_image.labels.keys()))
        ))

    deployment_name = "model.%s.%s.deployment" % (
        normalize_name_to_dns_1123(docker_image.labels[drun.const.headers.DOMAIN_MODEL_ID]),
        normalize_name_to_dns_1123(docker_image.labels[drun.const.headers.DOMAIN_MODEL_VERSION])
    )

    compatible_labels = {
        normalize_name_to_dns_1123(k): normalize_name_to_dns_1123(v)
        for k, v in
        docker_image.labels.items()
    }

    return deployment_name, compatible_labels
