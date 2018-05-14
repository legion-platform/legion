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
console plugin module
"""
import sys
import os

from flask import Flask, Blueprint, Markup


class Plugin:
    """
    Base plugin class
    """

    plugin_name = None
    url_prefix = None
    blueprint = None

    def __init__(self, plugin_name: str,
                 template_folder: str = 'templates', static_folder: str = 'static', url_prefix: str = '/'):
        """
        Construct plugin

        :param plugin_name: plugin name
        :type plugin_name: str
        :param template_folder: folder for pages templates
        :type template_folder: str
        :param static_folder: folder for static content
        :type static_folder: str
        :param url_prefix: plugin url prefix
        :type url_prefix: str
        """
        self.plugin_name = plugin_name
        self.url_prefix = url_prefix

        plugin_home = os.path.dirname(sys.modules[self.__class__.__module__].__file__)
        templates = os.path.join(plugin_home, template_folder)
        static = os.path.join(plugin_home, static_folder)
        self.blueprint = Blueprint(plugin_name, __name__,
                                   template_folder=templates, static_folder=static, url_prefix=url_prefix)

    def get_menu_item(self):
        """
        Return plugin menu item

        :return: :py:class:`flask.Markup`
        """
        return self.create_link(self.plugin_name, self.url_prefix)

    def register_plugin(self, current_app: Flask):
        """
        Register plugin

        :return: None
        """
        self.blueprint.context_processor(current_app.context_processor)
        current_app.register_blueprint(self.blueprint)

    @staticmethod
    def create_link(label: str, href: str):
        """
        Create link(html tag <a>)

        :param label: label(text)
        :type label: str
        :param href: hyper-reference
        :type href: str
        :return: :py:class:`flask.Markup` -- link
        """
        link = '<a href="{}">{}</a>'.format(href, label)
        return Markup(link)
