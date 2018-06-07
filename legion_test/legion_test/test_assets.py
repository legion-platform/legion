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


BASE_VERSION_ENVIRON_KEY = 'BASE_VERSION'
LOCAL_VERSION_ENVIRON_KEY = 'LOCAL_VERSION'


def get_k8s_repository(variables):
    """
    Get k8s images repository

    :param variables: loaded variables from file
    :type variables: dict
    :return: str -- k8s images repository
    """
    return '{}/legion'.format(variables['NEXUS_DOCKER_REPO'])


def get_k8s_version():
    """
    Get k8s image version from env. variables

    :return: str -- k8s image version
    """
    base_version = os.getenv(BASE_VERSION_ENVIRON_KEY)
    local_version = os.getenv(LOCAL_VERSION_ENVIRON_KEY)

    if not base_version or not local_version:
        raise Exception('Cannot get version info: {} or {} undefined'
                        .format(BASE_VERSION_ENVIRON_KEY, LOCAL_VERSION_ENVIRON_KEY))

    return '{}-{}'.format(base_version, local_version)


def get_test_bare_model_api_image(variables):
    """
    Get model api test image

    :param variables: loaded variables from file
    :type variables: dict
    :return: str -- model image name
    """
    return '{}/test-bare-model-api:{}'.format(get_k8s_repository(variables), get_k8s_version())
