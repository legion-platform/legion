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
Template helper
"""
from os import path
from pathlib import Path
from typing import Any, Dict, Optional

import pydantic
from jinja2 import Environment, FileSystemLoader

# Looks like Jinja PackageLoader does not work with a namespaced package
# Because of this we should use FileSystemLoader here
REST_PACKAGER_RES_DIR: Path = Path(path.realpath(__file__)).parent.joinpath('resources')
REST_PACKAGER_ENV = Environment(loader=FileSystemLoader(str(REST_PACKAGER_RES_DIR)))


class DockerTemplateContext(pydantic.BaseModel):
    """
    Main Docker template context
    """

    model_name: str
    model_version: str
    legion_version: str
    packager_version: str
    path: str
    path_docker: str
    conda_env_name: str
    gunicorn_bin: str
    gunicorn_bin_docker: str
    timeout: str
    host: str
    port: str
    workers: str
    threads: str
    pythonpath: str
    wsgi_handler: str
    model_location: str
    entrypoint_target: str
    handler_file: str
    base_image: str
    conda_installation_content: str
    conda_file_name: str
    entrypoint_docker: str


def render_packager_template(template_name: str, values: Optional[Dict[str, Any]] = None) -> str:
    """
    Helper function to read template from a file and render it

    :param template_name: name of a rest packager template
    :param values: template values
    :return: rendered template
    """
    template = REST_PACKAGER_ENV.get_template(template_name)

    return template.render(values if values else {})
