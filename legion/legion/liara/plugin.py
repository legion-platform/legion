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
from flask import Blueprint, current_app
from legion.liara import server


class Plugin:
    """
    Base plugin class
    """

    blueprint = None

    def __init__(self, name, template_folder='templates', static_folder='static', url_prefix='/'):
        plugin_home = os.path.dirname(sys.modules[self.__class__.__module__].__file__)
        templates = os.path.join(plugin_home, template_folder)
        static = os.path.join(plugin_home, static_folder)
        self.blueprint = Blueprint(name, __name__,
                                   template_folder=templates, static_folder=static, url_prefix=url_prefix)

    def register_plugin(self):
        """
        Register liara plugin

        :return: None
        """
        self.blueprint.context_processor(current_app.context_processor)
        current_app.register_blueprint(self.blueprint)

    @staticmethod
    def add_menu_item(label: str, href: str, index: int):
        """
        Add link as item to menu

        :param label: link label to display
        :type label: str
        :param href: href to resource
        :type href: str
        :param index: item index in menu
        :type index: int
        :return: None
        """
        server.add_menu_item(label, href, index)

    @staticmethod
    def add_custom_menu_item(item: str, index: int):
        """
        Add custom html as item to menu

        :param item: html code
        :type item: str
        :param index: item index in menu
        :type index: int
        :return: None
        """
        server.add_custom_menu_item(item, index)
