#!/usr/bin/env python3
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

import requests
import datetime
import argparse
import re
import logging
import sys
from typing import NamedTuple, List


Options = NamedTuple('Options', [
    ('nexus_url', str),
    ('user', str),
    ('password', str),
    ('dry_run', bool),
    ('remaining_days', int),
    ('repositories', list),
    ('build_name', str),
    ('version_filter', str)
])

NEXUS_SEARCH_URL = '{host}/service/rest/v1/components'
NEXUS_DELETE_URL = '{host}/service/rest/v1/components/{resource}'
NEXUS_DEFAULT_RESOURCE_REPOSITORIES = 'jenkins_plugins', 'main-docker', 'pypi-hosted', 'helm-main'
FIELDS_TO_ANALYZE = 'version', 'name'
VERSION_SEARCH_REGEX = r'\d{12,14}'
ALLOWED_RESPONSE_CODES = [200, 201, 202, 204]


def get_builds(repository: str, options: Options):
    """
    Get list of Legion artifacts at Nexus repo matching search filters

    :param repository: Nexus repository name
    :type repository: str
    :param options: configuration options
    :type options: :py:class:`Options`
    :return: list[dict] List of Nexus components
    """
    search_filters = {'repository': repository}
    if options.build_name:
        search_filters['name'] = options.build_name

    builds = []
    try:
        url = NEXUS_SEARCH_URL.format(host=options.nexus_url)
        log.debug('Fetching Nexus artifacts from URL {}'.format(url))
        response = requests.get(url, params=search_filters, auth=(options.user, options.password))
        if response.status_code not in ALLOWED_RESPONSE_CODES:
            raise Exception('Invalid response: {!r} - {!r}'.format(response.status_code, response.text))
        response_data = response.json()
        builds.extend(response_data.get('items'))

        continuation_token = response_data.get('continuationToken')

        while continuation_token is not None:
            log.debug('Fetching Nexus artifacts from URL {} (from {})'.format(url, continuation_token))
            search_filters['continuationToken'] = continuation_token
            response = requests.get(url, params=search_filters, auth=(options.user, options.password))
            if response.status_code not in ALLOWED_RESPONSE_CODES:
                raise Exception('Invalid response: {!r} - {!r}'.format(response.status_code, response.text))
            response_data = response.json()
            builds.extend(response_data.get('items'))
            continuation_token = response_data.get('continuationToken')

    except Exception as fetching_error:
        log.error('Error fetching Nexus artifacts: {}'.format(fetching_error))
        raise

    return builds


def filter_builds_by_date(builds: List[dict], remaining_days: int):
    """
    Filter builds based on date in version string

    :param builds: List of Nexus components
    :type builds: list
    :param remaining_days: Number of days to leave the builds
    :type remaining_days: int
    :return: list[dict, dict] List of Nexus components older than remaining_days
    """
    remaining_date = datetime.datetime.now() - datetime.timedelta(remaining_days)
    builds_to_del = []
    for build in builds:
        try:
            build_date = [
                re.search(VERSION_SEARCH_REGEX, build.get(field) if build.get(field) else '')
                for field in FIELDS_TO_ANALYZE
            ]
            if not any(build_date):
                log.warning('Can\'t find build date for {!r}'.format(build))
                continue

            regex_date = next(regex.group() for regex in build_date if regex)

            if len(regex_date) == 12:
                regex_pattern = '%y%m%d%H%M%S'
            elif len(regex_date) == 14:
                regex_pattern = '%Y%m%d%H%M%S'
            else:
                log.warning('Unknown length of matched date {!r}'.format(regex_date))
                continue

            resources_date = datetime.datetime.strptime(regex_date, regex_pattern)

            if resources_date < remaining_date:
                builds_to_del.append(build)
        except Exception as version_analyze_exception:
            print('Cannot analyze build {!r}: {}'.format(build, version_analyze_exception))

    return builds_to_del


def filter_builds_by_version(builds: List[dict], version_filter: str):
    """
    Filter builds based version string regex

    :param builds: List of Nexus components
    :type builds: list
    :param version_filter: version string filter regex
    :type version_filter: str
    :return: list[dict, dict] List of Nexus components with version matching version_filter regex
    """
    builds_to_del = []
    for build in builds:
        try:
            regex_return = [
                re.search(version_filter, build.get(field) if build.get(field) else '')
                for field in FIELDS_TO_ANALYZE
            ]
            regex_founded = any(result.group() for result in regex_return)
            if regex_founded:
                builds_to_del.append(build)

        except Exception as version_analyze_exception:
            print('Cannot analyze build {!r}: {}'.format(build, version_analyze_exception))

    return builds_to_del


def delete_builds(builds: List[dict], options: Options):
    """
    Delete artifacts from Nexus repository

    :param builds: List of Nexus components
    :type builds: list
    :param options: configuration options
    :type options: :py:class:`Options`
    :return: None
    """
    log.info('List of artifacts to delete: {}'.format(
        [('{}-{}'.format(build.get('name'), build.get('version'))) for build in builds]))
    if options.dry_run:
        log.info('Dry run mode selected, no actions to be performed.')
    else:
        for build in builds:
            try:
                log.debug('Deleting {}-{}-{}-{}...'.format(
                        build.get('name'),
                        build.get('version'),
                        build.get('id'),
                        build.get('group')
                ))
                response = requests.delete(NEXUS_DELETE_URL.format(
                    host=options.nexus_url,
                    resource=build.get('id')),
                    auth=(options.user, options.password))
                if response.status_code not in ALLOWED_RESPONSE_CODES:
                    raise Exception('Invalid response: {!r} - {!r}'.format(response.status_code, response.text))
            except Exception as e:
                log.error('Error deleting artifact from Nexus: {}'.format(e))
                raise


def work(options: Options):
    """
    Get Legion artifacts matching build_name (if specified) from Nexus repository
    and delete those who older than remaining_days

    :param options: configuration options
    :type options: :py:class:`Options`
    :return: None
    """
    for repo in options.repositories:
        log.info('Cleaning up Nexus repository {!r}'.format(repo))

        nexus_builds = get_builds(repo, options)

        try:
            if options.version_filter and options.remaining_days:
                log.error('Only one of \'version_filter\' or \'remaining_days\' must be specified')
                sys.exit(1)
            elif options.version_filter: 
                builds_to_del = filter_builds_by_version(nexus_builds, options.version_filter)
            elif options.remaining_days:
                builds_to_del = filter_builds_by_date(nexus_builds, options.remaining_days)
            else:
                log.warning('No artifacts matching the filter found in {} repository'.format(repo))
                continue

            try:
                delete_builds(builds_to_del, options)
            except Exception as removal_error:
                log.error('Can\'t delete artifacts for {} repository: {}'.format(repo, removal_error))
                raise
        except Exception as fetching_error:
            log.error('Error fetching list of builds for {} repository: {} '.format(repo, fetching_error))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for Legion artifacts cleanup at Nexus repository')
    parser.add_argument('nexus_url', type=str, help='Nexus repo url')
    parser.add_argument('--user', '-u', type=str, default='admin', help='Nexus admin user')
    parser.add_argument('--password', '-p', type=str, default='admin123', help='Nexus admin password')
    parser.add_argument('--remaining-days', type=int, help='Number of days to remain builds')
    parser.add_argument('--build-name', '-n', type=str, help='Build name to delete')
    parser.add_argument('--version-filter', '-f', type=str, help='Delete builds with version matching the regex')
    parser.add_argument('--repositories', '-r', default=NEXUS_DEFAULT_RESOURCE_REPOSITORIES,
                        help='List of repositories to cleanup', nargs='+')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Do not perform any actions')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose log output')

    args = parser.parse_args()
    arguments = Options(
        nexus_url=args.nexus_url,
        user=args.user,
        password=args.password,
        dry_run=args.dry_run,
        remaining_days=args.remaining_days,
        build_name=args.build_name,
        version_filter=args.version_filter,
        repositories=args.repositories
    )

    log = logging.getLogger(__name__)
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        work(arguments)
    except Exception as e:
        log.error('Error removing Nexus artifacts: {}'.format(e))
        sys.exit(1)
