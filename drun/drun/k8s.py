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
import logging
import os

import drun
import drun.env
import drun.headers

import kubernetes
import kubernetes.client
#import kubernetes.client.apis.batch_v1_api
import kubernetes.config
import kubernetes.config.config_exception

K8S_LABEL_PREFIX = 'drun/'
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


def find_service(service_name, namespace='default', search_without_system_filter=False):
    """
    Find service in cluster

    :param service_name: service name
    :type service_name: str
    :param namespace: namespace
    :type namespace: str
    :param search_without_system_filter: search services that not contains K8S_LABEL_PREFIX + 'component'
    :param search_without_system_filter: bool
    :return: :py:class:`kubernetes.client.models.v1_service.V1Service` or None
    """
    client = build_client()

    core_api = kubernetes.client.CoreV1Api(client)
    all_services = core_api.list_namespaced_service(namespace)

    service_filter = lambda service: service.metadata.labels \
                                     and service.metadata.labels.get(K8S_LABEL_PREFIX + 'component') == service_name

    if search_without_system_filter:
        service_filter = lambda service: service_name in service.metadata.name

    valid_services = [
        service
        for service in all_services.items
        if service_filter(service)
    ]

    if len(valid_services) > 1:
        raise Exception('Founded more that one valid service for %s' % service_name)

    if len(valid_services) == 0:
        raise Exception('Cannot found valid service for %s' % service_name)

    return valid_services[0]
