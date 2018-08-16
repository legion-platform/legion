#
#    Copyright 2018 EPAM Systems
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
IO Notifier module for Legion Template
"""
import logging
import os

import aionotify
import yaml

LOGGER = logging.getLogger(__name__)


async def file_change_monitor(template_system, filepath, is_yaml=False, var_name='file'):
    """
     On file change updates template context with a file content
     and renders it.

     Example #1 (Yaml file) :
        {{ load_module('legion.ltemplate.render', filepath='config.yml', is_yaml=True, var_name='conf') }}
        <b>Hosts values:</b>
        <ul>
        {% for item in conf:  %}
        <li>{{ item.hosts }}</li>
        {% endfor %}
        </ul>

    Example #2 (Txt file) :
        {{ load_module('legion.io.render', filepath='config.txt') }}
        <h1>Config file Context:</h1>
        <pre>{{ file }}</pre>

    :param template_system: Object, that contains 'render' callback function
    :param filepath: Path to a File, relative to template file or absolute
    :type filepath: str
    :param is_yaml_file: Indicates if file is in yaml format and it should be parsed
    :type is_yaml_file: bool
    :param var_name: variable name, used to store file content in context
    :type var_name: str
    :return: None
    """
    if not os.path.isabs(filepath):
        filepath = os.path.join(os.path.dirname(template_system.template_file_path), filepath)

    LOGGER.info('Starting file change monitor for file {}, is_yaml={} as variable={}'
                .format(filepath, is_yaml, var_name))

    with open(filepath) as f:
        if is_yaml:
            template_system.render(**{var_name: yaml.load(f)})
        else:
            template_system.render(**{var_name: f.read()})

    LOGGER.debug('Initializing watcher for file {}'.format(filepath))
    watcher = aionotify.Watcher()
    watcher.watch(path=filepath, flags=aionotify.Flags.MODIFY)

    LOGGER.debug('Awaiting setup of watcher for file {}'.format(filepath))
    await watcher.setup(template_system._loop)

    LOGGER.debug('Starting aionotify loop')
    while True:
        await watcher.get_event()

        LOGGER.info('Got update event for file {}'.format(filepath))
        with open(filepath) as f:
            if is_yaml:
                template_system.render(**{var_name: yaml.load(f)})
            else:
                template_system.render(**{var_name: f.read()})
