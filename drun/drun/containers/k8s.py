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

import drun
import drun.const.env
import drun.const.headers
from drun.utils import normalize_name_to_dns_1123

import kubernetes
import kubernetes.client
import kubernetes.config
import kubernetes.config.config_exception

K8S_LOCAL_CLUSTER_DOMAIN = 'cluster.local'


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
    :type namespace: str
    :return: list[:py:class:`kubernetes.client.models.extensions_v1beta1_deployment.ExtensionsV1beta1Deployment`]
    """
    client = build_client()

    extension_api = kubernetes.client.ExtensionsV1beta1Api(client)
    all_deployments = extension_api.list_namespaced_deployment(namespace)

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
