#!/usr/bin/env python
#
#   Copyright 2017 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import argparse
import time

import jenkins


class LogicException(Exception):
    def __init__(self, message):
        super(LogicException, self).__init__(message)
        self._message = message

    @property
    def message(self):
        return self._message


def is_server_busy(server):
    """
    Check if server busy
    :param server: jenkins.Server
    :return: bool is server busy with any build
    """
    queue = server.get_queue_info()
    builds = server.get_running_builds()
    nodes = server.get_nodes()
    executors_busy = False

    for node in nodes:
        node_name = node['name']
        if node_name == 'master':
            node_name = '(master)'

        node_info = server.get_node_info(node_name, 3)
        executors = node_info.get('executors', [])
        for executor_info in executors:
            current_executable = executor_info.get('currentExecutable', None)
            is_idle = executor_info.get('idle')
            if current_executable or not is_idle:
                executors_busy = True

    return len(builds) > 0 or len(queue) > 0 or executors_busy


def work(args):
    """
    Perform work on Jenkins server: run build, wait until all build will be finished, analyze build statuses
    :param args: arguments
    :return: None
    """

    server = jenkins.Jenkins(args.jenkins_url,
                             username=args.jenkins_user,
                             password=args.jenkins_password,
                             timeout=args.socket_timeout)

    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > args.connection_timeout:
            break

        try:
            server.get_all_jobs()
            break
        except Exception:
            print('Reconnecting...')
            time.sleep(args.socket_reconnect_sleep)

    if args.jenkins_run_job:
        if not is_server_busy(server):
            server.build_job(args.jenkins_run_job)
            time.sleep(args.run_sleep_sec)
        else:
            print('Server is busy. Skipping run')

    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > args.run_timeout:
            break

        if not is_server_busy(server):
            break

        print('Waiting...')
        time.sleep(args.iterate_sleep_sec)

    jobs = {j['fullname']: server.get_job_info(j['fullname']) for j in server.get_all_jobs()}

    if args.jenkins_check_job_prefix:
        jobs = {k:v for k,v in jobs.items() if k.startswith(args.jenkins_check_job_prefix)}

    for job_name, job in jobs.items():
        last_successful_build = job['lastSuccessfulBuild']['number'] if job['lastSuccessfulBuild'] else None
        last_build = job['lastBuild']['number'] if job['lastBuild'] else None
        if not last_successful_build:
            raise LogicException('For Job %s: Cannot found successful build' % (job_name, ))
        if last_successful_build and last_build and last_successful_build < last_build:
            raise LogicException('For Job %s: Last successful build # less that last build #' % (job_name, ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Jenkins job checker')
    parser.add_argument('--jenkins-url', type=str, default='http://parallels/jenkins')
    parser.add_argument('--jenkins-user', type=str, default='admin')
    parser.add_argument('--jenkins-password', type=str, default='admin')
    parser.add_argument('--jenkins-run-job', type=str)
    parser.add_argument('--jenkins-check-job-prefix', type=str)
    parser.add_argument('--connection-timeout', type=int, default=120)
    parser.add_argument('--iterate-sleep-sec', type=int, default=5)
    parser.add_argument('--run-sleep-sec', type=int, default=10)
    parser.add_argument('--run-timeout', type=int, default=120)
    parser.add_argument('--socket-timeout', type=int, default=10)
    parser.add_argument('--socket-reconnect-sleep', type=int, default=10)

    args = parser.parse_args()

    try:
        work(args)
    except LogicException as logic_exception:
        print('Error: %s' % logic_exception.message)
        exit(1)
    except KeyboardInterrupt:
        print('Interrupt')
        exit(2)
    except Exception as exception:
        print('Exception')
        print(exception)
        exit(3)
