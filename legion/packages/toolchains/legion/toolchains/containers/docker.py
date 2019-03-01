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
import legion.core


def generate_docker_labels_for_image(model_file, model_id):
    """
    Generate docker image labels from model file

    :param model_file: path to model file
    :type model_file: str
    :param model_id: model id
    :type model_id: str
    :return: dict[str, str] of labels
    """
    container = legion.toolchains.python.pymodel.Model.load(model_file)

    base = {
        legion.core.containers.headers.DOMAIN_MODEL_ID: model_id,
        legion.core.containers.headers.DOMAIN_MODEL_VERSION: container.model_version,
        legion.core.containers.headers.DOMAIN_CLASS: 'pyserve',
        legion.core.containers.headers.DOMAIN_CONTAINER_TYPE: 'model',
        legion.core.containers.headers.DOMAIN_MODEL_PROPERTY_VALUES: container.properties.serialize_data_to_string()
    }

    for key, value in container.meta_information.items():
        if hasattr(value, '__iter__') and not isinstance(value, str):
            formatted_value = ', '.join(item for item in value)
        else:
            formatted_value = str(value)

        base[legion.core.containers.headers.DOMAIN_PREFIX + key] = formatted_value

    return base
