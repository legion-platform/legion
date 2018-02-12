import time
import json

import jenkins
from six.moves.urllib.request import Request, install_opener, build_opener, urlopen
from six.moves.urllib.error import HTTPError
from six.moves.urllib.error import URLError

JOB_MODEL_ID = '%(folder_url)sjob/%(short_name)s/%(build_number)s/model/json'


def fetch_model_meta_from_jenkins(client, job_name):
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
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'

    def __init__(self):
        self._client = None  # type: jenkins.Jenkins

    def connect_to_jenkins(self, domain, user, password, timeout=10):
        self._client = jenkins.Jenkins(domain,
                                       username=user,
                                       password=password,
                                       timeout=int(timeout))

        self._client.get_all_jobs()

    def run_jenkins_job(self, job_name, **parameters):
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

        self._client.build_job(job_name, parameters=parameters)

    def wait_jenkins_job(self, job_name, timeout=0, sleep=5):
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        timeout = int(timeout)
        sleep = int(sleep)

        start = time.time()
        while True:
            job_info = self._client.get_job_info(job_name)
            if not job_info['lastBuild'] and not job_info['inQueue']:
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
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        job_info = self._client.get_job_info(job_name, 4)
        artifacts = job_info['lastBuild']['artifacts']

        if not any(artifact['fileName'] == artifact_name for artifact in artifacts):
            raise Exception('Cannot find artifact named {} if artifacts of last build'.format(artifact_name))

    def jenkins_log_meta_information(self, job_name):
        if not self._client:
            raise Exception('Jenkins client has not been initialized')

        data = fetch_model_meta_from_jenkins(self._client, job_name)

        required_keys = {'modelId', 'modelVersion', 'modelPath'}
        missed_keys = required_keys - set(data.keys())
        if len(missed_keys) > 0:
            raise Exception('Missed model meta information keys: {}'.format(', '.join(missed_keys)))

        return data
