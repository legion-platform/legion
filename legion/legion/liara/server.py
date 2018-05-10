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
from flask import Flask, Markup

import legion.config
import legion.external.grafana
import legion.http
import legion.io
import legion.liara
from legion.liara import plugins as plugins_module
from legion.liara.plugins.plugin import Plugin
from legion.liara.plugins.enclave_plugin import EnclavePlugin
from legion.containers import k8s


class Liara:
    """
    Liara server class
    """

    common_plugins = []
    enclave_plugins = []

    def add_plugin(self, custom_plugin: Plugin):
        """
        Add plugin to server

        :param custom_plugin: liara plugin
        :type custom_plugin: :py:class:`legion.liara.plugins.plugin.Plugin`
        :return: None
        """
        if isinstance(custom_plugin, EnclavePlugin):
            self.enclave_plugins.append(custom_plugin)
        else:
            self.common_plugins.append(custom_plugin)
        custom_plugin.register_plugin()

    def main_menu_items(self):
        """
        Return main menu items

        :return list[:py:class:`flask.Markup`] -- list of main menu items
        """
        result = []
        for plugin in self.common_plugins:
            item = plugin.get_menu_item()
            if item is not None:
                result.append(item)
        return result

    def enclave_menu_items(self):
        """
        Return enclave menu items

        :return list[:py:class:`flask.Markup`] -- list of enclave menu items
        """
        result = {}
        for enclave in k8s.list_enclaves():
            result[enclave] = []
            for plugin in self.enclave_plugins:
                result[enclave].append(plugin.get_menu_item(enclave))
        return result

    def start(self, args):
        """
        Start liara server

        :param args: arguments
        :type args: :py:class:`argparse.Namespace`
        :return: :py:class:`flask.Flask` -- liara web application
        """
        app = Flask(__name__)
        app.context_processor = lambda: dict(main_menu_label=Markup('<h2>Liara</h2>'),
                                             main_menu_items=self.main_menu_items(),
                                             enclaves_menu_items=self.enclave_menu_items())
        legion.http.configure_application(app, args)
        app.config['CLUSTER_SECRETS'] = k8s.load_secrets(app.config['CLUSTER_SECRETS_PATH'])
        app.config['CLUSTER_STATE'] = k8s.load_config(app.config['CLUSTER_CONFIG_PATH'])
        with app.app_context():
            for p in plugins_module.get_plugins():
                if isinstance(p, legion.liara.plugins.enclave_plugin.EnclavePlugin):
                    self.enclave_plugins.append(p)
                else:
                    self.common_plugins.append(p)
                p.register_plugin(app)
        app.run(host=app.config['LEGION_API_ADDR'],
                port=app.config['LEGION_API_PORT'],
                debug=app.config['DEBUG'],
                use_reloader=False)
        return app


LIARA = Liara()
