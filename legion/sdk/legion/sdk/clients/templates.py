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
List of templates
"""
import os
import typing

TEMPLATES = {}

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'examples')
_EXAMPLE_SUFFIX = ".legion.yaml"


def get_legion_template_names() -> typing.Set[str]:
    return {
        # Remove suffix from name
        f[:-len(_EXAMPLE_SUFFIX)] for _, _, filenames in os.walk(_TEMPLATE_DIR) for f in filenames
    }


def get_legion_template_content(template_name: str) -> str:
    full_file_name = os.path.join(_TEMPLATE_DIR, template_name + _EXAMPLE_SUFFIX)
    if not os.path.exists(full_file_name):
        raise ValueError(f'Cannot find {template_name} template')

    with open(full_file_name, 'r', encoding='utf8') as fp:
        return fp.read()
