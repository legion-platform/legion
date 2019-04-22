#
#    Copyright 2018 EPAM Systems
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
legion k8s utils functions
"""
import json
import logging
import os
import re
from typing import NamedTuple

import kubernetes
import kubernetes.client
from kubernetes.client import V1Pod, V1ContainerStatus
import kubernetes.config
import kubernetes.config.config_exception
import urllib3
import urllib3.exceptions
import yaml
from docker_registry_client import DockerRegistryClient
from legion.sdk import config
from legion.sdk.containers import headers
from legion.sdk.containers.exceptions import IncompatibleLegionModelDockerImage
from legion.sdk.definitions import \
    LEGION_COMPONENT_LABEL, LEGION_COMPONENT_NAME_MODEL, \
    LEGION_SYSTEM_LABEL, LEGION_SYSTEM_VALUE, \
    ModelContainerMetaInformation, KUBERNETES_SERVICE_ACCOUNT_NAMESPACE_PATH
from legion.sdk.utils import normalize_name

LOGGER = logging.getLogger(__name__)
CONNECTION_CONTEXT = None
KUBERNETES_SERVICE_ACCOUNT_NAMESPACE_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
ImageAttributes = NamedTuple('ImageAttributes', [
    ('host', str),
    ('repo', str),
    ('ref', str)
])

CPU_REDUCE_PAT = re.compile(r"^(\d+)(m?)$")
MEM_REDUCE_PAT = re.compile(r"^(\d+)(E|P|T|G|M|K|Ei|Pi|Ti|Gi|Mi|Ki|)$")


def _calculate_request_res(value: int) -> int:
    """
    Calculate request for k8s resource

    :param value: k8s resource
    :type value: int
    :return: reduced k8s resource - int
    """
    return value * (100 - config.REDUCE_MODEL_REQUESTS_BY) // 100


def reduce_mem_resource(res: str):
    """
    Reduce memory k8s resource

    :param res: k8s memory
    :type res: str
    :return: k8s memory - str
    """
    matches = MEM_REDUCE_PAT.match(res)
    if not matches:
        raise ValueError('Malformed mem resource: {}'.format(res))

    num, res_type = int(matches.group(1)), matches.group(2)

    if res_type in ('G', 'Gi'):
        num, res_type = num * 1024, 'Mi'

    return '{}{}'.format(_calculate_request_res(num), res_type)


def reduce_cpu_resource(res: str):
    """
    Reduce cpu k8s resource

    :param res: k8s cpu
    :type res: str
    :return: k8s cpu - str
    """
    matches = CPU_REDUCE_PAT.match(res)
    if not matches:
        raise ValueError('Malformed cpu resource: {}'.format(res))

    num, res_type = int(matches.group(1)), matches.group(2)

    if not res_type:
        num, res_type = num * 1000, 'm'

    return '{}{}'.format(_calculate_request_res(num), res_type)


def build_client():
    """
    Configure and returns kubernetes client

    :return: :py:module:`kubernetes.client`
    """
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.config_exception.ConfigException:
        LOGGER.debug('Connecting to cluster using context {!r}'.format(CONNECTION_CONTEXT))
        kubernetes.config.load_kube_config(context=CONNECTION_CONTEXT)

    # Disable SSL warning for self-signed certificates
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return kubernetes.client.ApiClient()


def extract_container_id(container_id: str) -> str:
    """
    Extract from k8s containerID a real container id.
    For example:
        docker://40985bfadf82466b4241ef1f7c7c926c98d3943456 -> 40985bfadf82466b4241ef1f7c7c926c98d3943456

    :param container_id: k8s containerID
    :return: real docker container id
    """
    return container_id[len('docker://'):]


def get_container_id_of_current_pod(container_name: str) -> str:
    """
    Extract container id from current pod by container name

    :param container_name: k8s container name
    :return: container id
    """
    api = kubernetes.client.CoreV1Api(build_client())
    pod: V1Pod = api.read_namespaced_pod(config.POD_NAME, config.NAMESPACE)

    for container_status in pod.status.container_statuses:  # type: V1ContainerStatus
        if container_status.name == container_name:
            return extract_container_id(container_status.container_id)

    raise ValueError(f"Not found {container_name} in the {config.POD_NAME}")


def get_current_namespace():
    """
    Get current namespace [WORKS ONLY IN-CLUSTER]

    :return: str -- name of namespace
    """
    try:
        with open(KUBERNETES_SERVICE_ACCOUNT_NAMESPACE_PATH, 'r') as namespace_file:
            return namespace_file.read()
    except Exception as exception:
        raise Exception('Cannot get current namespace (it works only in cluster): {}'.format(exception))


def is_code_run_in_cluster():
    """
    Is current code run in a cluster

    :return: bool -- is code run in a cluster or not
    """
    return os.path.exists(KUBERNETES_SERVICE_ACCOUNT_NAMESPACE_PATH)


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
        return yaml.safe_load(stream)


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


def get_docker_image_labels(image):
    """
    Get labels from docker image
    :param image: docker image
    :type image: str
    :return: dict[str, Any] -- image labels
    """
    LOGGER.info('Getting labels for {} image'.format(image))
    image_attributes = parse_docker_image_url(image)

    # Get nexus registry host from ENV or image url
    try:
        if image_attributes.host == config.MODEL_IMAGES_REGISTRY_HOST:
            registry_host = config.DOCKER_REGISTRY
        else:
            registry_host = '{}://{}'.format(config.DOCKER_REGISTRY_PROTOCOL, image_attributes.host)
    except Exception as err:
        LOGGER.error('Can\'t get registry host neither from ENV nor from image URL: {}'.format(err))
        raise err

    try:
        registry_client = DockerRegistryClient(
            host=registry_host,
            username=config.DOCKER_REGISTRY_USER,
            password=config.DOCKER_REGISTRY_PASSWORD,
            api_version=2
        )
        manifest = registry_client.repository(image_attributes.repo).manifest(image_attributes.ref)
        labels = json.loads(
            manifest[0]["history"][0]["v1Compatibility"])["container_config"]["Labels"]

    except Exception as err:
        raise Exception('Can\'t get image labels for {} image: {}'.format(image, err))

    required_headers = [headers.DOMAIN_MODEL_ID, headers.DOMAIN_MODEL_VERSION, headers.DOMAIN_CONTAINER_TYPE]

    if any(header not in labels for header in required_headers):
        raise Exception('Missed one of %s labels. Available labels: %s' % (
            ', '.join(required_headers),
            ', '.join(tuple(labels.keys()))
        ))

    return labels


def get_meta_from_docker_labels(labels):
    """
    Build meta fields for kubernetes from docker labels.

    :param labels: docker image labels
    :type labels: dict[str, Any]
    :return: tuple[str, dict[str, str], str, str] -- k8s_name name, labels in DNS-1123 format, model id and version
    """
    model_id = labels.get(headers.DOMAIN_MODEL_ID)
    model_version = labels.get(headers.DOMAIN_MODEL_VERSION)

    if not model_id or not model_version:
        raise IncompatibleLegionModelDockerImage(
            'Legion docker labels for model image are missed: {}'.format(
                ', '.join((headers.DOMAIN_MODEL_ID,
                           headers.DOMAIN_MODEL_VERSION,)),
            ))

    kubernetes_labels = dict()
    kubernetes_labels[LEGION_COMPONENT_LABEL] = LEGION_COMPONENT_NAME_MODEL
    kubernetes_labels[LEGION_SYSTEM_LABEL] = LEGION_SYSTEM_VALUE
    kubernetes_labels[headers.DOMAIN_MODEL_ID] = model_id
    kubernetes_labels[headers.DOMAIN_MODEL_VERSION] = model_version

    return ModelContainerMetaInformation(
        k8s_name=normalize_k8s_name(model_id, model_version),
        model_id=model_id,
        model_version=model_version,
        kubernetes_labels=kubernetes_labels,
        kubernetes_annotations=labels
    )


def normalize_k8s_name(model_id, model_version):
    """
    Convert model id and version to normalize k8s name

    :param model_id: model id
    :type model_id: str or None
    :param model_version: model version
    :type model_version: str or None
    :return str - normalize k8s name
    """
    return normalize_name('model-{}-{}'.format(model_id, model_version), dns_1035=True)


def parse_docker_image_url(image_url):
    """
    Get Repository host address, image name and version from image url
    :param image_url: full docker image url
    :type image_url: str
    :return: namedtuple[str, Any]
    """
    image_attrs_regexp = r'(.*?)/([\w\-/]+):([\-\.\w]+)'
    try:
        image_attrs_list = re.search(image_attrs_regexp, image_url)

        try:
            host = image_attrs_list.group(1)
        except Exception as err:
            LOGGER.error('Image url doesn\'t contain host pattern: {}'.format(err))
            raise err
        try:
            repo = image_attrs_list.group(2)
        except Exception as err:
            LOGGER.error('Image url doesn\'t contain repo pattern: {}'.format(err))
            raise err
        try:
            ref = image_attrs_list.group(3)
        except Exception as err:
            LOGGER.error('Image url doesn\'t contain ref pattern: {}'.format(err))
            raise err

        image_attributes = ImageAttributes(
            host=host,
            repo=repo,
            ref=ref
        )

        LOGGER.info('Image attributes: {}'.format(image_attributes))

    except Exception as err:
        LOGGER.error('Can\'t get image attributes from image url {}: {}.'.format(
            image_url,
            err))
        raise err

    return image_attributes
