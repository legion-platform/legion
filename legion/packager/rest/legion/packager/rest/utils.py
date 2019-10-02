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
import uuid

import pydantic
from jinja2 import Template


class TemplateNameValues(pydantic.BaseModel):
    """
    This structure contains values for name template of the rest packager
    """

    # Model name of a trained artifact
    Name: str
    # Model version of a trained artifact
    Version: str
    # Some random UUID. If you should leave it empty
    RandomUUID: str = ""


def build_image_name(name_template: str, values: TemplateNameValues) -> str:
    """
    Generate name for a model docker image

    :param name_template: Jinja template for name
    :param values: set of values for template name
    :return: docker image name
    """
    if not values.RandomUUID:
        values.RandomUUID = str(uuid.uuid4())

    return Template(name_template).render(values.dict())


def build_archive_name(model_name: str, model_version: str) -> str:
    return f'{model_name}-{model_version}.zip'
