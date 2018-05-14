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
console web application
"""
from flask import Flask

import legion.config
import legion.external.grafana
import legion.http
import legion.io
import legion.console
from legion.console.plugins import load as load_plugins, plugin, enclave_plugin
from legion.containers import explorer


class Console:
    """
    Console server class
    """

    __common_plugins = []
    __enclave_plugins = []

    def add_plugin(self, custom_plugin: plugin.Plugin):
        """
        Add plugin to server

        :param custom_plugin: console plugin
        :type custom_plugin: :py:class:`legion.console.plugins.plugin.Plugin`
        :return: None
        """
        if isinstance(custom_plugin, enclave_plugin.EnclavePlugin):
            self.__enclave_plugins.append(custom_plugin)
        else:
            self.__common_plugins.append(custom_plugin)

    def __main_menu_items(self):
        """
        Return main menu items

        :return list[:py:class:`flask.Markup`] -- list of main menu items
        """
        result = []
        for pl in self.__common_plugins:
            item = pl.get_menu_item()
            index = pl.get_menu_item_index()
            if item is not None:
                result.insert(index, item)
        return result

    def __enclave_menu_items(self):
        """
        Return enclave menu items

        :return list[:py:class:`flask.Markup`] -- list of enclave menu items
        """
        result = {}
        for enclave in explorer.find_enclaves():
            result[enclave.name] = []
            for pl in self.__enclave_plugins:
                item = pl.get_menu_item(enclave.name)
                index = pl.get_menu_item_index()
                if item is not None:
                    result[enclave.name].insert(index, item)
        return result

    def start(self, args):
        """
        Start console server

        :param args: arguments
        :type args: :py:class:`argparse.Namespace`
        :return: :py:class:`flask.Flask` -- console web application
        """
        app = Flask(__name__)
        app.context_processor = lambda: dict(main_menu_items=self.__main_menu_items(),
                                             enclaves_menu_items=self.__enclave_menu_items())
        legion.http.configure_application(app, args)
        with app.app_context():
            load_plugins()
            for plug in self.__common_plugins + self.__enclave_plugins:
                plug.register_plugin(app)
        app.run(host=app.config['LEGION_API_ADDR'],
                port=app.config['LEGION_API_PORT'],
                debug=app.config['DEBUG'],
                use_reloader=False)
        return app


CONSOLE = Console()
