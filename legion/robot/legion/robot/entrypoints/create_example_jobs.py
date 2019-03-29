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
Tool for scan local folders and add jobs on remote Jenkins instance
"""
import argparse
import glob
import os
import time
from typing import NamedTuple
from urllib.parse import quote

import jenkins
from legion.robot import profiler_loader
from legion.robot.libraries import dex_client
from legion.robot.template import render_template

Options = NamedTuple('Options', [
    ('jenkins_url', str),
    ('base_directory', str),
    ('git_directory', str),
    ('git_url', str),
    ('git_branch', str),
    ('git_root_key', str),
    ('model_host', str),
    ('dynamic_model_prefix', str),
    ('perf_test_prefix', str),
    ('profiles_dir', str),
    ('profile', str),
    ('connection_timeout', int),
    ('socket_reconnect_sleep', int),
    ('plain_tasks', bool),
])


def find_jobs_jenkins_files(base_directory, git_directory, jenkins_file_name, plain_jobs=False):
    """
    Find Jenkins files in subdirectories of target directory

    :param base_directory: target directory
    :type base_directory: str
    :param base_directory: git root directory (paths will be returned relative to this directory)
    :type base_directory: str
    :param jenkins_file_name: name of Jenkins file
    :type jenkins_file_name: str
    :param plain_jobs: create plain jobs (from Jenkinsfile and script templates)
    :type plain_jobs: bool
    :return: dict[str, str] -- map of job name => job's Jenkinsfile
    """
    root = os.path.abspath(base_directory)
    git_root = os.path.abspath(git_directory)
    jenkins_files = glob.glob('%s/**/%s' % (root, jenkins_file_name), recursive=True)
    jenkins_files_map = {}

    print('Root: %s' % root)
    print('Git root: %s' % git_root)

    for file in jenkins_files:
        print('Analyzing Jenkinsfile %s' % file)
        if not file.startswith(root) or not file.startswith(git_root):
            print('Ignoring due to incorrect path prefix')
            continue

        job_template = None
        stored_directory = os.path.dirname(file)

        if plain_jobs:
            job_template = os.path.join(stored_directory, 'job.xml')
            if not os.path.exists(job_template):
                print('Ignoring due to impossible to found job.xml in %s directory' % stored_directory)
                continue

        relative_path = file[len(git_root) + 1:]
        paths = relative_path.split(os.sep)

        if len(paths) > 1:
            name = paths[-2]
            jenkins_files_map[name] = (relative_path, job_template)
            print('Registered %s as %s' % (relative_path, name))
        else:
            print('Ignoring due to impossible to found name from path')

    return jenkins_files_map


def create_plain_jobs(client, options):
    """
    Create plain jobs

    :param client: Jenkins client
    :param options: CLI options
    :return: None
    """
    founded_external_jobs = {job['name']: job for job in client.get_all_jobs()}
    # Build jobs
    founded_local_jobs = find_jobs_jenkins_files(options.base_directory,
                                                 options.git_directory,
                                                 'Jenkinsfile', True)

    for job_name, (jenkins_file, job_xml) in founded_local_jobs.items():
        data = {
            'GIT_URL': options.git_url,
            'GIT_BRANCH': options.git_branch,
            'GIT_ROOT_KEY': options.git_root_key,
            'JENKINS_FILE': jenkins_file
        }
        xml_data = render_template(job_xml, data, use_filesystem_loader=True)
        if job_name not in founded_external_jobs:
            client.create_job(job_name, xml_data)
        else:
            client.reconfig_job(job_name, xml_data)


def create_dynamic_models_jobs(client, options):
    """
    Create jobs for building models

    :param client: Jenkins client
    :param options: CLI options
    :return: None
    """
    founded_external_jobs = {job['name']: job for job in client.get_all_jobs()}
    # Build jobs
    founded_local_models = find_jobs_jenkins_files(options.base_directory,
                                                   options.git_directory,
                                                   'Jenkinsfile')

    for model_name, (jenkins_file, _) in founded_local_models.items():
        job_name = '%s %s' % (options.dynamic_model_prefix, model_name)
        data = {
            'MODEL_NAME': job_name,
            'MODEL_NAME_ESCAPED': quote(job_name),
            'DESCRIPTION': 'Automatically created job for model %s' % model_name,
            'GIT_URL': options.git_url,
            'GIT_BRANCH': options.git_branch,
            'GIT_ROOT_KEY': options.git_root_key,
            'JENKINS_FILE': jenkins_file
        }
        xml_data = render_template('jenkins_job.tmpl', data)

        if job_name not in founded_external_jobs:
            client.create_job(job_name, xml_data)
        else:
            client.reconfig_job(job_name, xml_data)

    # Performance jobs
    founded_local_perf_tests = find_jobs_jenkins_files(options.base_directory,
                                                       options.git_directory,
                                                       'performance.Jenkinsfile')

    for model_name, (jenkins_file, _) in founded_local_perf_tests.items():
        job_name = '%s %s' % (options.perf_test_prefix, model_name)
        if job_name not in founded_external_jobs:
            data = {
                'MODEL_NAME': job_name,
                'MODEL_NAME_ESCAPED': quote(job_name),
                'DESCRIPTION': 'Automatically created performance test for model %s' % model_name,
                'GIT_URL': options.git_url,
                'GIT_BRANCH': options.git_branch,
                'GIT_ROOT_KEY': options.git_root_key,
                'JENKINS_PERFORMANCE_FILE': jenkins_file,
                'MODEL_HOST': options.model_host
            }
            xml_data = render_template('jenkins_performance_job.tmpl', data)
            client.create_job(job_name, xml_data)


def get_jenkins_credentials(profile_dir: str, profile: str):
    """
    Perform Jenkins Dex Client action

    :param profile_dir: (Optional) path to profiles. By default env variable PATH_TO_PROFILES_DIR is used
    :param profile: profile name
    :return jenkins credentials
    """
    profiler_loader.get_variables(profile_dir, profile)

    credentials = dex_client.get_jenkins_credentials()
    if not credentials:
        raise ValueError(f"Can't find jenkins credentials")

    username, password = credentials
    cookies = ';'.join(['{}={}'.format(k, v) for (k, v) in dex_client.get_session_cookies().items()])

    return username, password, cookies


def work(options: Options):
    """
    Connect to Jenkins, check that all jobs for models is existed

    :param options: options
    :return: None
    """
    jenkins_user, jenkins_password, jenkins_token = get_jenkins_credentials(options.profiles_dir, options.profile)
    if os.getenv('PYTHONHTTPSVERIFY', None) == '0':
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context

    client = jenkins.Jenkins(options.jenkins_url, username=jenkins_user, password=jenkins_password)

    if jenkins_token:
        client.crumb = {'crumbRequestField': 'Cookie', 'crumb': jenkins_token}

    start = time.time()

    connected = False

    while not connected:
        elapsed = time.time() - start
        if elapsed > options.connection_timeout:
            break

        try:
            client.get_all_jobs()
            connected = True
        except Exception as connection_exception:
            print('Reconnecting... %s' % connection_exception)
            time.sleep(options.socket_reconnect_sleep)

    if not connected:
        print('Failed to connect to %s' % options.jenkins_url)
        exit(1)

    print('Connection established')

    if options.plain_tasks:
        create_plain_jobs(client, options)
    else:
        create_dynamic_models_jobs(client, options)


def main():
    """
    CLI entrypoint
    """
    parser = argparse.ArgumentParser('Jenkins job creator')
    parser.add_argument('jenkins_url', type=str, help='Jenkins server url')
    parser.add_argument('base_directory', type=str, help='Base find directory')
    parser.add_argument('git_directory', type=str, help='Git directory')
    parser.add_argument('git_url', type=str, help='Default GIT url')
    parser.add_argument('git_branch', type=str, help='Default GIT branch')
    parser.add_argument('--git-root-key', type=str, help='Git credentials ID', default='legion-root-key')
    parser.add_argument('--model-host', type=str, help='Host with model', default='http://edge:80')
    parser.add_argument('--dynamic-model-prefix', type=str, help='Dynamic model job prefix', default='DYNAMIC MODEL')
    parser.add_argument('--perf-test-prefix', type=str, help='Performance test prefix', default='PERF TEST')
    parser.add_argument('--connection-timeout', type=int, default=120)
    parser.add_argument('--socket-reconnect-sleep', type=int, default=10)
    parser.add_argument('--profiles-dir', type=str)
    parser.add_argument('--profile', type=str)
    parser.add_argument('--plain-tasks', action='store_true', help='Create plain jenkins tasks '
                                                                   '(not for dynamic model using founded template)')

    args = parser.parse_args()
    arguments = Options(
        jenkins_url=args.jenkins_url,
        base_directory=args.base_directory,
        git_directory=args.git_directory,
        git_url=args.git_url,
        git_branch=args.git_branch,
        git_root_key=args.git_root_key,
        model_host=args.model_host,
        dynamic_model_prefix=args.dynamic_model_prefix,
        perf_test_prefix=args.perf_test_prefix,
        connection_timeout=args.connection_timeout,
        profiles_dir=args.profiles_dir,
        profile=args.profile,
        socket_reconnect_sleep=args.socket_reconnect_sleep,
        plain_tasks=args.plain_tasks,
    )
    work(arguments)
