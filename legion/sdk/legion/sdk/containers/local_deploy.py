#
#    Copyright 2019 EPAM Systems
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
import logging

import docker
import docker.errors

from legion.sdk import config
from legion.sdk import definitions
from legion.sdk.clients import model
from legion.sdk.containers import definitions as container_definitions
from legion.sdk.containers import headers
from legion.sdk.containers.exceptions import IncompatibleLegionModelDockerImage

LOGGER = logging.getLogger(__name__)


def get_models(client, name=None, model_id=None, model_version=None):
    """
    Get models that fit match criterions (model id and model version, model id may be *, model version may be *)

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param name: name of deployment
    :type name: str
    :param model_id: model id or */None for all models
    :type model_id: str or None
    :param model_version: (Optional) model version or */None for all
    :type model_version: str or None
    :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
    """
    # Gather all deployments (valid)
    containers = [container
                  for container in client.containers.list()
                  if container.labels
                  and headers.DOMAIN_MODEL_ID in container.labels
                  and headers.DOMAIN_MODEL_VERSION in container.labels
    ]

    # First - filter by deployment name, if it exist
    if name:
        containers = [
            container
            for container in containers
            if container.name == name
        ]

    # Next - filter by model_id & model_version, it they are present
    if model_id or model_version:
        containers = [container
                      for container in containers
                      if model_id in (None, '*', container.labels[headers.DOMAIN_MODEL_ID])
                      and model_version in (None, '*', container.labels[headers.DOMAIN_MODEL_VERSION])
                      ]

    prepared_containers = []

    for container in containers:
        prepared_containers.append(
            container_definitions.ModelDeploymentDescription.build_from_docker_container_info(
                container
            ))

    return sorted(prepared_containers, key=lambda ms: ms.deployment_name)


def get_models_strict(client, name=None, model_id=None, model_version=None, ignore_not_found=False):
    """
    Get models that fit match criterions (model id and model version, model id may be *, model version may be *)
    If more that one model would be found with unstrict criterion - exception would be raised
    If no one model would be found - exception would be raised

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param name: (Optional) name of deployment
    :type name: str
    :param model_id: (Optional) model id or * for all models
    :type model_id: str
    :param model_version: (Optional) model version
    :type model_version: str
    :param ignore_not_found: (Optional) ignore exception if cannot find any model
    :type ignore_not_found: bool
    :return: list[:py:class:`legion.k8s.ModelService`] -- founded model services
    """
    model_services = get_models(client, name, model_id, model_version)

    ignore_strictness = model_id == '*' or model_version == '*'

    if len(model_services) > 1:
        LOGGER.info('More than one model was found for filter: id={!r} version={!r}'
                    .format(model_id, model_version))
        if not ignore_strictness and not model_version:
            raise Exception('Please specify version of model')

    if not model_services:
        if not ignore_not_found:
            raise Exception('No one model can be found')
        else:
            LOGGER.info('Cannot find any model - ignoring due to ignore-not-found parameter')

    return model_services


def deploy_model(client, name, image, local_port=0):
    """
    Deploy legion image locally

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param name: name of deployment
    :type name: str
    :param image: Docker image to deploy
    :type image: str
    :param local_port: port to deploy on
    :type local_port: int
    :return: list[:py:class:`legion.k8s.ModelService`] -- affected model services
    """
    LOGGER.debug('Trying to find image {}'.format(image))
    try:
        docker_image = client.images.get(image)
        LOGGER.debug('Image {} has been founded locally'.format(image))
    except docker.errors.ImageNotFound:
        LOGGER.debug('Image {} can not be founded locally, pulling'.format(image))
        docker_image = client.images.pull(image)
        LOGGER.debug('Image {} has been pulled'.format(image))

    model_id = docker_image.labels.get(headers.DOMAIN_MODEL_ID)
    model_version = docker_image.labels.get(headers.DOMAIN_MODEL_VERSION)

    if not model_id or not model_version:
        raise IncompatibleLegionModelDockerImage(
            'Legion docker labels for model image are missed: {}'.format(
                ', '.join((headers.DOMAIN_MODEL_ID,
                           headers.DOMAIN_MODEL_VERSION,)),
            ))

    LOGGER.debug('Image {} contains model: {!r} version {!r}'.format(image, model_id, model_version))

    if get_models(client, name):
        raise Exception('Model with same id and version already has been deployed')

    port_configuration = {
        config.LEGION_PORT: None if not local_port else local_port
    }
    LOGGER.debug('Creating container with image {!r} and port configuration {!r}'.format(image,
                                                                                         port_configuration))

    docker_labels = {f'{definitions.LEGION_COMPONENT_LABEL}.model_id': model_id,
                     f'{definitions.LEGION_COMPONENT_LABEL}.model_version': model_version}

    container = client.containers.run(docker_image,
                                      name=name,
                                      ports=port_configuration,
                                      labels=docker_labels,
                                      detach=True,
                                      remove=True)
    LOGGER.debug('Container {} has been stared'.format(container.id))

    return get_models(client, name)


def undeploy_model(client, name, model_id, model_version, ignore_not_found):
    """
    Undeploy local deployed image

    :param client: Docker client
    :type client: :py:class:`docker.client.DockerClient`
    :param name: name of model deployment
    :type name: (Optional) str
    :param model_id: model id
    :type model_id: (Optional) str
    :param model_version: (Optional) specific model version
    :type model_version: str or None
    :param ignore_not_found: (Optional) ignore exception if cannot find models
    :type ignore_not_found: bool
    :return: list[:py:class:`legion.k8s.ModelService`] -- affected model services
    """
    target_deployments = get_models_strict(client, name, model_id, model_version, ignore_not_found)
    for deployment in target_deployments:
        container = client.containers.get(deployment.container_id)
        container.stop()

    return target_deployments
