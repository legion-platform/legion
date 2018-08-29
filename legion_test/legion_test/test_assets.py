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
Docker image loader
"""
import os


LEGION_VERSION_ENVIRON_KEY = 'LEGION_VERSION'


def get_k8s_repository(variables):
    """
    Get k8s images repository

    :param variables: loaded variables from file
    :type variables: dict
    :return: str -- k8s images repository
    """
    return '{}'.format(variables['NEXUS_DOCKER_REPO'])


def get_k8s_version():
    """
    Get k8s image version from env. variables

    :return: str -- k8s image version
    """
    legion_version = os.getenv(LEGION_VERSION_ENVIRON_KEY)

    if not legion_version:
        raise Exception('Can\'t get version info: {} undefined'
                        .format(LEGION_VERSION_ENVIRON_KEY))

    return '{}'.format(legion_version)


def get_test_bare_model_api_image(variables, model_num=1):
    """
    Get model api test image

    :param variables: loaded variables from file
    :type variables: dict
    :param model_num: (Optional) test model num
    :type model_num: int
    :return: str -- model image name
    """

    return '{}/test-bare-model-api-model-{}:{}'.format(get_k8s_repository(variables), model_num, get_k8s_version())
