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
Robot test library - jenkins
"""
import time
import json

import jenkins
from six.moves.urllib.request import Request
from six.moves.urllib.error import HTTPError
from legion_test.robot.dex_client import get_session_cookies, get_jenkins_credentials

JOB_MODEL_ID = '%(folder_url)sjob/%(short_name)s/%(build_number)s/model/json'


def fetch_model_meta_from_jenkins(client, job_name):
    """
    Fetch model meta information (that been gathered from console logs and server by our plugin at /model/json endpoint)

    :param client: Jenkins client
    :type client: :py:class:`jenkins.Jenkins`
    :param job_name: Jenkins job name
    :type job_name: str
    :raises: Exception
    :return: dict[str, str] -- model meta headers
    """
    job_info = client.get_job_info(job_name, 4)
    folder_url, short_name = client._get_job_folder(job_name)
    build_number = job_info['lastBuild']['id']

    try:
        response = client.jenkins_open(Request(
            client._build_url(JOB_MODEL_ID, locals())
        ))
        if response:
            return json.loads(response)
        else:
            raise Exception('job[{}] does not exist'.format(job_name))
    except HTTPError:
        raise Exception('job[{}] does not exist'.format(job_name))
    except ValueError:
        raise Exception('Could not parse JSON for job[{}]'.format(job_name))


class Jenkins:
    """
    Jenkins client for robot tests
    """

    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        """
        Init client
        """
        self._client = None  # type: jenkins.Jenkins

    def connect_to_jenkins(self, domain, user=None, password=None, add_dex_cookies=True, timeout=10):
        """
        Connect to Jenkins server

        :param domain: domain name
        :type domain: str
        :param user: login
        :type user: str
        :param password: password
        :type password: str
        :param timeout: timeout for connection process in seconds
        :type timeout: int or str
        :param add_dex_cookies: if Dex Cookies should be added to request
        :type add_dex_cookies: bool
        :return: None
        """
        if get_jenkins_credentials():
            user, password = get_jenkins_credentials()
        self._client = jenkins.Jenkins(domain,
                                       username=user,
                                       password=password,
                                       timeout=int(timeout))
        if add_dex_cookies:
            self._client.crumb = {'crumbRequestField': 'Cookie',
                            'crumb': ';'.join(['{}={}'.format(k,v)
                                          for (k,v) in get_session_cookies().items()])}

        user = self._client.get_whoami()
        print('Hello %s from Jenkins' % (user['fullName']))
        self._client.wait_for_normal_op(10)
        self._client.get_all_jobs()

    def run_jenkins_job(self, job_name, **parameters):
        """
        Run Jenkins job

        :param job_name: Jenkins job name
        :type job_name: str
        :param parameters: Jenkins job run parameters. Defaults uses is nothing specified
        :raises: Exception
        :return: None
        """
        if not self._client:
            raise Exception('Jenkins client has not been initialized')
        job_info = self._client.get_job_info(job_name, 4)

        if len(parameters) == 0:
            properties = job_info['property']
            parameters = [x for x in properties if x['_class'] == 'hudson.model.ParametersDefinitionProperty']
            if len(parameters) != 1:
                raise Exception('Cannot find only single ParametersDefinitionProperty. Found: {}'
                                .format(len(parameters)))

            parameters = [x['defaultParameterValue'] for x in parameters[0]['parameterDefinitions']]
            parameters = {x['name']: x['value'] for x in parameters}
        response = self._client.build_job(job_name, parameters=parameters)
        print('Result of Job run: {!r}'.format(response))

    def wait_jenkins_job(self, job_name, timeout=0, sleep=5):
        """
        Wait finish of last job build

        :param job_name: Jenkins job name
        :type job_name: str
        :param timeout: waiting timeout in seconds. 0 for disable (infinite)
        :type timeout: str or int
        :param sleep: sleep between checks in seconds
        :type sleep: str ot int
        :raises: Exception
        :return: None
        """
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        timeout = int(timeout)
        sleep = int(sleep)

        start = time.time()
        time.sleep(sleep)
        while True:
            job_info = self._client.get_job_info(job_name)
            if not job_info['lastBuild'] and not job_info['inQueue']:
                print('Job info: {}'.format(repr(job_info)))
                raise Exception('Cannot find any build and not in queue')

            if job_info['lastCompletedBuild'] and \
                    job_info['lastCompletedBuild']['number'] == job_info['lastBuild']['number'] and \
                    not job_info['inQueue']:
                return True

            elapsed = time.time() - start
            if elapsed > timeout > 0:
                raise Exception('Timeout')

            time.sleep(sleep)

    def last_jenkins_job_is_successful(self, job_name):
        """
        Check that latest job build is successful

        :param job_name: Jenkins job name
        :type job_name: str
        :raises: Exception
        :return: None
        """
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        job_info = self._client.get_job_info(job_name)
        if not job_info['lastSuccessfulBuild']:
            raise Exception('Cannot find any successful build')

        successful_build_number = job_info['lastSuccessfulBuild']['number']
        last_build_number = job_info['lastCompletedBuild']['number']

        if successful_build_number != last_build_number:
            raise Exception('Last successful build #{} but last build #{}'
                            .format(successful_build_number, last_build_number))

    def jenkins_artifact_present(self, job_name, artifact_name):
        """
        Check that specific artifact has been created by latest job build

        :param job_name: Jenkins job name
        :type job_name: str
        :param artifact_name: artifact name
        :type artifact_name: str
        :raises: Exception
        :return: None
        """
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        job_info = self._client.get_job_info(job_name, 4)
        artifacts = job_info['lastBuild']['artifacts']

        if not any(artifact['fileName'] == artifact_name for artifact in artifacts):
            raise Exception('Cannot find artifact named {} if artifacts of last build'.format(artifact_name))

    def jenkins_log_meta_information(self, job_name):
        """
        Gather model meta information (model headers) from console of last job build

        :param job_name: Jenkins job name
        :type job_name: str
        :raises: Exception
        :return: dict[str, str] -- model meta headers
        """
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        data = fetch_model_meta_from_jenkins(self._client, job_name)

        required_keys = {'modelId', 'modelVersion', 'modelPath'}
        missed_keys = required_keys - set(data.keys())
        if len(missed_keys) > 0:
            raise Exception('Missed model meta information keys: {}'.format(', '.join(missed_keys)))

        return data
