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
Template generator
"""

from jinja2 import Environment, PackageLoader, FileSystemLoader, select_autoescape


def render_template(template_name, values=None, use_filesystem_loader=False):
    """
    Render template with parameters

    :param template_name: name of template without path (all templates should be placed in legion.templates directory)
    or path if use_filesystem_loader enabled
    :type template_name: str
    :param values: dict template variables or None
    :type values: dict
    :param use_filesystem_loader: use filesystem loader and load templates from any location
    :type use_filesystem_loader: bool
    :return: str rendered template
    """
    environment = PackageLoader(__name__, 'templates')
    if use_filesystem_loader:
        environment = FileSystemLoader('/')

    env = Environment(
        loader=environment,
        autoescape=select_autoescape(['tmpl'])
    )

    if not values:
        values = {}

    template = env.get_template(template_name)
    return template.render(values)
