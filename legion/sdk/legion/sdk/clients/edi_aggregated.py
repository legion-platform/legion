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
import logging
import os
import typing
import json

import yaml

from legion.sdk.clients.edi import RemoteEdiClient, WrongHttpStatusCode
from legion.sdk.clients.training import ModelTrainingClient, ModelTraining
from legion.sdk.clients.deployment import ModelDeploymentClient, ModelDeployment
from legion.sdk.clients.vcs import VcsClient, VCSCredential

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

    resource_name: str
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
    elif isinstance(resource.resource, VCSCredential):
        return VcsClient.construct_from_other(edi_client)
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
    if not isinstance(resource_type, str):
        raise Exception('Kind of object {!r} should be string'.format(declaration))

    target_classes = {
        'ModelTraining': ModelTraining,
        'ModelDeployment': ModelDeployment,
        'VCSCredential': VCSCredential
    }

    if resource_type not in target_classes:
        raise Exception('Unknown kind of object: {!r}'.format(resource_type))

    resource = target_classes[resource_type].from_json(declaration)

    return LegionCloudResourceUpdatePair(
        resource_name=resource.name,
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

    if not isinstance(items, list) and not isinstance(items, tuple):
        items = [items]

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
    if len(resources) != 1:
        raise Exception('{!r} should contain 1 item, but {!r} founded'.format(path, len(resources)))
    return resources[0]


def apply(updates: LegionCloudResourcesUpdateList, edi_client: RemoteEdiClient, is_removal: bool) -> ApplyResult:
    """
    Apply changes on Legion cloud

    :param updates: changes to apply
    :type updates: :py:class:LegionCloudResourcesUpdateList
    :param edi_client: client to extract connection properties from
    :type edi_client: RemoteEdiClient
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
        resource_str_identifier = f'#{idx+1}. {change.resource_name}' if change.resource_name else f'#{idx+1}'

        LOGGER.debug('Processing resource %r', resource_str_identifier)
        # Build and check client
        try:
            client = build_client(change, edi_client)
        except Exception as general_exception:
            errors.append(Exception(f'Can not get build client for {resource_str_identifier}: {general_exception}'))

        # Check is resource exist or not
        try:
            client.get(change.resource_name)
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
                    LOGGER.info('Editing of #%d %s (name: %s)', idx+1, change.resource, change.resource_name)
                    client.edit(change.resource)
                    changed.append(change)
                else:
                    LOGGER.info('Creating of #%d %s (name: %s)', idx+1, change.resource, change.resource_name)
                    client.create(change.resource)
                    created.append(change)
            # If removal
            else:
                # Only if resource exists on a cluster
                if resource_exist:
                    LOGGER.info('Removing of #%d %s (name: %s)', idx+1, change.resource, change.resource_name)
                    client.delete(change.resource_name)
                    removed.append(change)
        except Exception as general_exception:
            errors.append(Exception(f'Can not update resource {resource_str_identifier}: {general_exception}'))
            continue

    return ApplyResult(tuple(created), tuple(removed), tuple(changed), tuple(errors))
