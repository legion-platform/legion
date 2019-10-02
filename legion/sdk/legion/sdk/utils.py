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
legion utils functional
"""
import inspect
import logging
import time

from jinja2 import Environment, PackageLoader, select_autoescape

LOGGER = logging.getLogger(__name__)


def render_template(template_name, values=None):
    """
    Render template with parameters

    :param template_name: name of template without path (all templates should be placed in legion.templates directory)
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



def get_function_description(callable_object):
    """
    Gather information about callable object to string

    :param callable_object: callable object to analyze
    :type callable_object: Callable[[], any]
    :return: str -- object description
    """
    object_class_name = callable_object.__class__.__name__
    if not callable(callable_object):
        return '<not callable object: {}>'.format(object_class_name)

    object_name = callable_object.__name__
    module_name = inspect.getmodule(callable_object)
    return '<{} {} in {}>'.format(object_class_name, object_name, module_name)


def ensure_function_succeed(function_to_call, retries, timeout, boolean_check=False):
    """
    Try to call function till it will return not None object.
    Raise if there are no retries left

    :param function_to_call: function to be called
    :type function_to_call: Callable[[], any]
    :param retries: count of retries
    :type retries: int
    :param timeout: timeout between retries
    :type timeout: int
    :param boolean_check: (Optional) check function for True-able value (by default value is checked for not None value)
    :type boolean_check: bool
    :return: Any -- result of successful function call or None if no retries left
    """
    function_description = get_function_description(function_to_call)
    for no in range(retries):
        LOGGER.debug('Calling {}'.format(function_description))
        result = function_to_call()

        if boolean_check:
            if result:
                return result
        else:
            if result is not None:
                return result

        if no < retries:
            LOGGER.debug('Retry {}/{} was failed'.format(no + 1, retries))
        if no < retries - 1:
            LOGGER.debug('Waiting {}s before next retry analysis'.format(timeout))
            time.sleep(timeout)

    LOGGER.error('No retries left for function {}'.format(function_description))
    return False if boolean_check else None
