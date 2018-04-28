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
liara web application
"""
import logging

from flask import Flask, Markup

import legion.config
import legion.containers.k8s
import legion.external.grafana
import legion.http
import legion.io
from legion.liara import plugins

LOGGER = logging.getLogger(__name__)
MENU_ITEMS = []


def add_menu_item(label: str, href: str, index: int):
    """
    Add link as item to menu

    :param label: link name to display
    :type label: str
    :param href: href to resource
    :type href: str
    :param index: item index in menu
    :type index: int
    :return: None
    """
    MENU_ITEMS.insert(index, Markup('<a href="{}">{}</a>'.format(href, label)))


def add_custom_menu_item(item: str, index: int):
    """
    Add custom html as item to menu

    :param item: html code
    :type item: str
    :param index: item index in menu
    :type index: int
    :return: None
    """
    MENU_ITEMS.insert(index, Markup(item))


def serve(args):
    """
    Start liara server

    :param args: arguments
    :type args: :py:class:`argparse.Namespace`
    :return: :py:class:`flask.Flask` -- liara web application
    """
    application = Flask(__name__)
    application.context_processor = lambda: dict(menu_items=MENU_ITEMS)
    legion.http.configure_application(application, args)
    with application.app_context():
        plugins.load()
    application.run(host=application.config['LEGION_API_ADDR'],
                    port=application.config['LEGION_API_PORT'],
                    debug=application.config['DEBUG'],
                    use_reloader=False)
    return application
