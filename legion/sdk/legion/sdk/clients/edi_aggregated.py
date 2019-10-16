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
Aggregated EDI client (can apply multiple resources)
"""
import asyncio
import json
import logging
import os
import typing

import yaml
from legion.sdk.clients.connection import ConnectionClient, AsyncConnectionClient
from legion.sdk.clients.deployment import ModelDeploymentClient, ModelDeployment, AsyncModelDeploymentClient
from legion.sdk.clients.edi import RemoteEdiClient, WrongHttpStatusCode, AsyncRemoteEdiClient
from legion.sdk.clients.packaging import ModelPackagingClient, AsyncModelPackagingClient
from legion.sdk.clients.packaging_integration import PackagingIntegrationClient, AsyncPackagingIntegrationClient
from legion.sdk.clients.route import ModelRoute, ModelRouteClient, AsyncModelRouteClient
from legion.sdk.clients.toolchain_integration import ToolchainIntegrationClient, AsyncToolchainIntegrationClient
from legion.sdk.clients.training import ModelTrainingClient, ModelTraining, AsyncModelTrainingClient
from legion.sdk.models import Connection, ToolchainIntegration, ModelPackaging, PackagingIntegration

LOGGER = logging.getLogger(__name__)


class InvalidResourceType(Exception):
    """
    Invalid resource type (unsupported) exception
    """

    pass


class LegionCloudResourceUpdatePair(typing.NamedTuple):
    """
    Information about resources to update
    """

    resource_id: str
    resource: object


class LegionCloudResourcesUpdateList(typing.NamedTuple):
    """
    Bulk update request (multiple resources)
    """

    changes: typing.Tuple[LegionCloudResourceUpdatePair] = tuple()


class ApplyResult(typing.NamedTuple):
    """
    Result of bulk applying
    """

    created: typing.Tuple[LegionCloudResourceUpdatePair] = tuple()
    removed: typing.Tuple[LegionCloudResourceUpdatePair] = tuple()
    changed: typing.Tuple[LegionCloudResourceUpdatePair] = tuple()
    errors: typing.Tuple[Exception] = tuple()


# pylint: disable=R0911
def build_client(resource: LegionCloudResourceUpdatePair, edi_client: RemoteEdiClient) -> typing.Optional[object]:
    """
    Build client for particular resource (e.g. it builds ModelTrainingClient for ModelTraining resource)

    :param resource: target resource
    :type resource: :py:class:LegionCloudResourceUpdatePair
    :param edi_client: base EDI client to extract connection options from
    :type edi_client: :py:class:RemoteEdiClient
    :return: typing.Optional[object] -- remote client or None
    """
    if isinstance(resource.resource, ModelTraining):
        return ModelTrainingClient.construct_from_other(edi_client)
    elif isinstance(resource.resource, ModelDeployment):
        return ModelDeploymentClient.construct_from_other(edi_client)
    elif isinstance(resource.resource, Connection):
        return ConnectionClient.construct_from_other(edi_client)
    elif isinstance(resource.resource, ToolchainIntegration):
        return ToolchainIntegrationClient.construct_from_other(edi_client)
    elif isinstance(resource.resource, ModelRoute):
        return ModelRouteClient.construct_from_other(edi_client)
    elif isinstance(resource.resource, ModelPackaging):
        return ModelPackagingClient.construct_from_other(edi_client)
    elif isinstance(resource.resource, PackagingIntegration):
        return PackagingIntegrationClient.construct_from_other(edi_client)
    else:
        raise InvalidResourceType('{!r} is invalid resource '.format(resource.resource))


# pylint: disable=R0911
def build_async_client(resource: LegionCloudResourceUpdatePair,
                       async_edi_client: AsyncRemoteEdiClient
                       ) -> typing.Optional[object]:
    """
    Build client for particular resource (e.g. it builds ModelTrainingClient for ModelTraining resource)

    :param resource: target resource
    :type resource: :py:class:LegionCloudResourceUpdatePair
    :param async_edi_client: base async EDI client to extract connection options from
    :type async_edi_client: :py:class:AsyncRemoteEdiClient
    :return: typing.Optional[object] -- remote client or None
    """
    if isinstance(resource.resource, ModelTraining):
        return AsyncModelTrainingClient.construct_from_other(async_edi_client)
    elif isinstance(resource.resource, ModelDeployment):
        return AsyncModelDeploymentClient.construct_from_other(async_edi_client)
    elif isinstance(resource.resource, Connection):
        return AsyncConnectionClient.construct_from_other(async_edi_client)
    elif isinstance(resource.resource, ToolchainIntegration):
        return AsyncToolchainIntegrationClient.construct_from_other(async_edi_client)
    elif isinstance(resource.resource, ModelRoute):
        return AsyncModelRouteClient.construct_from_other(async_edi_client)
    elif isinstance(resource.resource, ModelPackaging):
        return AsyncModelPackagingClient.construct_from_other(async_edi_client)
    elif isinstance(resource.resource, PackagingIntegration):
        return AsyncPackagingIntegrationClient.construct_from_other(async_edi_client)
    else:
        raise InvalidResourceType('{!r} is invalid resource '.format(resource.resource))


def build_resource(declaration: dict) -> LegionCloudResourceUpdatePair:
    """
    Build resource from it's declaration

    :param declaration: declaration of resource
    :type declaration: dict
    :return: object -- built resource
    """
    resource_type = declaration.get('kind')
    if resource_type is None:
        raise Exception('Kind of object {!r} must be not null'.format(declaration))

    if not isinstance(resource_type, str):
        raise Exception('Kind of object {!r} should be string'.format(declaration))

    target_classes = {
        'ModelTraining': ModelTraining,
        'ToolchainIntegration': ToolchainIntegration,
        'ModelDeployment': ModelDeployment,
        'ModelRoute': ModelRoute,
        'Connection': Connection,
        'ModelPackaging': ModelPackaging,
        'PackagingIntegration': PackagingIntegration,
    }

    if resource_type not in target_classes:
        raise Exception('Unknown kind of object: {!r}'.format(resource_type))

    resource = target_classes[resource_type].from_dict(declaration)

    return LegionCloudResourceUpdatePair(
        resource_id=resource.id,
        resource=resource
    )


def parse_resources_file(path: str) -> LegionCloudResourcesUpdateList:
    """
    Parse file (YAML/JSON) for Legion resources

    :param path: path to file (local)
    :type path: str
    :raises Exception: if parsing of file is impossible
    :raises ValueError: if invalid Legion resource detected
    :return: :py:class:LegionCloudResourcesUpdateList -- parsed resources
    """
    if not os.path.exists(path):
        raise FileNotFoundError('Resource file {!r} not found'.format(path))

    with open(path, 'r') as data_stream:
        items = None

        try:
            items = tuple(yaml.load_all(data_stream, Loader=yaml.SafeLoader))
        except yaml.YAMLError:
            try:
                items = json.load(data_stream)
            except json.JSONDecodeError:
                raise Exception('{!r} is not valid JSON or YAML file')

    if not isinstance(items, (list, tuple)):
        items = [items]

    if isinstance(items[0], (list, tuple)):
        items = items[0]

    result = []  # type: typing.List[LegionCloudResourceUpdatePair]

    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Invalid Legion resource in file: {!r}'.format(item))

        result.append(build_resource(item))

    return LegionCloudResourcesUpdateList(
        changes=tuple(result)
    )


def parse_resources_file_with_one_item(path: str) -> LegionCloudResourceUpdatePair:
    """
    Parse file (YAML/JSON) for Legion resource. Raise exception if it is more then one resource

    :param path: path to file (local)
    :type path: str
    :raises Exception: if parsing of file is impossible
    :raises Exception: if more then one resource found
    :raises ValueError: if invalid Legion resource detected
    :return: :py:class:LegionCloudResourceUpdatePair -- parsed resource
    """
    resources = parse_resources_file(path)
    if len(resources.changes) != 1:
        raise Exception('{!r} should contain 1 item, but {!r} founded'.format(path, len(resources)))
    return resources.changes[0]


async def async_apply(updates: LegionCloudResourcesUpdateList,
                      async_edi_client: AsyncRemoteEdiClient,
                      is_removal: bool) -> ApplyResult:
    """
    Apply changes on Legion cloud

    :param updates: changes to apply
    :type updates: :py:class:LegionCloudResourcesUpdateList
    :param async_edi_client: client to extract connection properties from
    :type async_edi_client: RemoteEdiClient
    :param is_removal: is it removal?
    :type is_removal: bool
    :return: :py:class:ApplyResult -- result of applying
    """
    created = []
    removed = []
    changed = []
    errors = []

    # Operate over all resources
    for idx, change in enumerate(updates.changes):
        resource_str_identifier = f'#{idx + 1}. {change.resource_id}' if change.resource_id else f'#{idx + 1}'

        LOGGER.debug('Processing resource %r', resource_str_identifier)
        # Build and check client
        try:
            client = build_async_client(change, async_edi_client)
        except Exception as general_exception:
            errors.append(Exception(f'Can not get build client for {resource_str_identifier}: {general_exception}'))
            continue

        # Check is resource exist or not
        try:
            await client.get(change.resource_id)
            resource_exist = True
        except WrongHttpStatusCode as http_exception:
            if http_exception.status_code == 404:
                resource_exist = False
            else:
                errors.append(Exception(f'Can not get status of resource '
                                        f'{resource_str_identifier}: {http_exception}'))
                continue
        except Exception as general_exception:
            errors.append(Exception(f'Can not get status of resource '
                                    f'{resource_str_identifier}: {general_exception}'))
            continue

        # Change resource (update/create/delete)
        try:
            # If not removal (creation / update)
            if not is_removal:
                if resource_exist:
                    LOGGER.info('Editing of #%d %s (name: %s)', idx + 1, change.resource, change.resource_id)
                    await client.edit(change.resource)
                    changed.append(change)
                else:
                    LOGGER.info('Creating of #%d %s (name: %s)', idx + 1, change.resource, change.resource_id)
                    await client.create(change.resource)
                    created.append(change)
            # If removal
            else:
                # Only if resource exists on a cluster
                if resource_exist:
                    LOGGER.info('Removing of #%d %s (name: %s)', idx + 1, change.resource, change.resource_id)
                    await client.delete(change.resource_id)
                    removed.append(change)
        except Exception as general_exception:
            errors.append(Exception(f'Can not update resource {resource_str_identifier}: {general_exception}'))
            continue

    return ApplyResult(tuple(created), tuple(removed), tuple(changed), tuple(errors))


def apply(updates: LegionCloudResourcesUpdateList,
          edi_client: typing.Union[AsyncRemoteEdiClient, RemoteEdiClient],
          is_removal: bool) -> ApplyResult:
    """
    Apply changes on Legion cloud (wrapper for async_apply). Used for not async client (For backward compatibility)

    :param updates: changes to apply
    :type updates: :py:class:LegionCloudResourcesUpdateList
    :param edi_client: client to extract connection properties from
    :type edi_client: RemoteEdiClient or AsyncRemoteEdiClient
    :param is_removal: is it removal?
    :type is_removal: bool
    :return: :py:class:ApplyResult -- result of applying
    """
    loop = asyncio.get_event_loop()

    feature = async_apply(updates, edi_client, is_removal)

    result = loop.run_until_complete(feature)

    return result
