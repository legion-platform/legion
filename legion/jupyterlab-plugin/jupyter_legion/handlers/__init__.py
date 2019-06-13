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
Entry point for using Legion plugin handlers
"""
from notebook.utils import url_path_join

from .local import LocalBuildsHandler, LocalBuildStatusHandler, LocalDeploymentsHandler, LocalAllEntitiesHandler, \
    LocalMetricsHandler
from .cloud import CloudTrainingsHandler, CloudDeploymentsHandler, \
    CloudTrainingLogsHandler, CloudApplyFromFileHandler, \
    CloudAllEntitiesHandler, CloudDeploymentsScaleHandler, CloudTokenIssueHandler, CloudTrainingsFromFileHandler

"""
List of all back-end handlers with prefixes
"""
ALL_HANDLERS = (
    # Local
    (LocalBuildStatusHandler, ('local', 'builds', 'status')),
    (LocalBuildsHandler, ('local', 'builds')),
    (LocalDeploymentsHandler, ('local', 'deployments')),
    (LocalMetricsHandler, ('local', 'metrics')),
    (LocalAllEntitiesHandler, ('local',)),
    # Cloud
    (CloudTrainingsHandler, ('cloud', 'trainings')),
    (CloudTrainingLogsHandler, ('cloud', 'trainings', '(.*)', 'logs')),
    (CloudTrainingsFromFileHandler, ('cloud', 'local-file')),
    (CloudDeploymentsHandler, ('cloud', 'deployments')),
    (CloudDeploymentsScaleHandler, ('cloud', 'deployments', 'scale')),
    (CloudApplyFromFileHandler, ('cloud', 'apply')),
    (CloudTokenIssueHandler, ('cloud', 'security', 'token')),
    (CloudAllEntitiesHandler, ('cloud',)),
)


def register_handler(logger, web_app, host_pattern, handler, init_args, root_api, *suburl):
    """
    Register Legion plugin back-end handler

    :param logger: logger to log data to
    :param web_app: instance of Tornado application
    :param host_pattern: host pattern to register on
    :param handler: target handler for URL
    :param init_args: initial arguments for handler
    :param root_api: root API prefix
    :param suburl: URL to register on
    :return: None
    """
    url = url_path_join(root_api, *suburl)
    logger.debug('Installing handler for %s on %r', handler.__name__, url)
    web_app.add_handlers(host_pattern, [(url, handler, init_args)])


def register_all_handlers(logger, web_app, host_pattern, init_args, root_api):
    """
    Register all Legion plugin back-end handlers

    :param logger: logger to log data to
    :param web_app: instance of Tornado application
    :param host_pattern: host pattern to register on
    :param init_args: initial arguments for handler
    :param root_api: root API prefix
    :return: None
    """
    for handler, url_parts in ALL_HANDLERS:
        logger.debug('Processing handler %r', handler.__name__)
        register_handler(logger, web_app, host_pattern, handler, init_args, root_api, *url_parts)
