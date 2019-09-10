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
Tool constants
"""
import os

PROJECT_FILE = 'legion.project.yaml'
LEGION_SUB_PATH_NAME = 'legion_model'
CONDA_FILE_NAME = 'conda.yaml'
RESOURCES_FOLDER = os.path.join(os.path.dirname(__file__), 'resources')
ENTRYPOINT_TEMPLATE = 'entrypoint.sh'
DESCRIPTION_TEMPLATE = 'description.txt'
ENTRYPOINT_DOCKER_TEMPLATE = 'entrypoint.docker.sh'
DOCKERFILE_TEMPLATE = 'Dockerfile'
DOCKERFILE_CONDA_INST_INSTRUCTIONS_TEMPLATE = 'conda.Dockerfile'
HANDLER_MODULE = 'legion_handler'
HANDLER_APP = 'app'

TARGET_DOCKER_REGISTRY = 'docker-push'
PULL_DOCKER_REGISTRY = 'docker-pull'
TARGET_ARCHIVE_STORAGE = 'archive-storage'

DOCKER_IMAGE_RESULT = 'image'
RESULT_FILE_NAME = 'result.json'
