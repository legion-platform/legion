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
liara plugin module
"""
import sys
import os

from flask import Blueprint, Markup, current_app

from legion.liara.server import liara


class Plugin:
    """
    Base plugin class
    """

    plugin_name = None
    url_prefix = None
    blueprint = None

    def __init__(self, plugin_name, template_folder='templates', static_folder='static', url_prefix='/'):
        self.plugin_name = plugin_name
        self.url_prefix = url_prefix

        plugin_home = os.path.dirname(sys.modules[self.__class__.__module__].__file__)
        templates = os.path.join(plugin_home, template_folder)
        static = os.path.join(plugin_home, static_folder)
        self.blueprint = Blueprint(plugin_name, __name__,
                                   template_folder=templates, static_folder=static, url_prefix=url_prefix)

    @staticmethod
    def add_menu_item(item: Markup):
        if item is not None:
            liara.add_menu_item(item)

    @staticmethod
    def create_link(label: str, href: str):
        """
        Create link(html tag <a>)

        :param label: str -- label
        :param href: str -- href
        :return: :py:class:`flask.Markup` -- link
        """
        link = '<a href="{}">{}</a>'.format(href, label)
        return Markup(link)

    def register_plugin(self):
        """
        Register liara plugin

        :return: None
        """
        self.blueprint.context_processor(current_app.context_processor)
        current_app.register_blueprint(self.blueprint)
