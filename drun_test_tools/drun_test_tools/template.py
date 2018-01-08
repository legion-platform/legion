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

from jinja2 import Environment, PackageLoader, select_autoescape


def render_template(template_name, values=None):
    """
    Render template with parameters

    :param template_name: name of template without path (all templates should be placed in drun.templates directory)
    :param values: dict template variables or None
    :return: str rendered template
    """
    env = Environment(
        loader=PackageLoader(__name__, 'templates'),
        autoescape=select_autoescape(['tmpl'])
    )

    if not values:
        values = {}

    template = env.get_template(template_name)
    return template.render(values)
