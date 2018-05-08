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
liara enclave plugin module
"""
from flask import Markup

from legion.containers import k8s
from legion.liara.plugins.plugin import Plugin
from legion.liara.server import LIARA


class EnclavePlugin(Plugin):
    """
    Base enclave plugin
    """

    def __init__(self, plugin_name: str, url_prefix: str):
        """
        Construct enclaves specific liara plugin

        :param plugin_name: plugin name
        :type plugin_name: str
        :param url_prefix: plugin url prefix
        :type url_prefix: str
        """
        super(EnclavePlugin, self).__init__(plugin_name, url_prefix=url_prefix)
        self.add_enclave_menu_item()

    def add_enclave_menu_item(self):
        """
        Add item to enclave menu

        :return: None
        """
        for enclave_name in self.list_enclaves():
            item = self.create_link(label=self.plugin_name, href='{}/{}'.format(self.url_prefix, enclave_name))
            LIARA.add_enclave_menu_item(enclave_name, Markup(item))

    @staticmethod
    def list_enclaves():
        """
        List enclaves names

        :return: list of enclaves names
        """
        return k8s.list_enclaves()

    @staticmethod
    def list_enclave_services(enclave: str):
        """
        List enclave resources(services and models)

        :param enclave: enclave name
        :type enclave: str
        :return: {'services': services list, 'models': models list}
        """
        return k8s.list_enclave_resources(enclave)
