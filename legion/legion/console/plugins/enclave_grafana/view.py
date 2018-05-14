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
hello plugin package
"""
from flask import render_template

from legion.containers import explorer
from legion.console.plugins.enclave_plugin import EnclavePlugin
from legion.console.server import CONSOLE


class GrafanaView(EnclavePlugin):
    """
    Enclave`s grafana plugin
    """

    grafanas = {}

    def __init__(self):
        """
        Construct 'grafana per enclave' plugin(page)

        """
        super(GrafanaView, self).__init__(plugin_name='enclave-grafana', url_prefix='/enclave-grafana')

    def get_menu_item_index(self):
        """
        Return menu item index

        :return: int -- menu item index
        """
        return 1


ENCLAVE_GRAFANA_PLUGIN = GrafanaView()


@ENCLAVE_GRAFANA_PLUGIN.blueprint.route('/<enclave_name>', methods=['GET'])
def grafana(enclave_name):
    """
    Render page

    :return: None
    """
    for enclave in explorer.find_enclaves(enclave_name):
        grafana_url = 'https://{}'.format(enclave.grafana_hostname)
        return render_template('enclave-grafana.html', grafana_url=grafana_url)
    return render_template('enclave-grafana.html', grafana_url='')


CONSOLE.add_plugin(ENCLAVE_GRAFANA_PLUGIN)
