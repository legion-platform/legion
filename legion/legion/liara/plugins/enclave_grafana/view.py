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
hello plugin package
"""
from flask import render_template

from legion.liara.plugins.enclave_plugin import EnclavePlugin


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
        for enclave in self.list_enclaves():
            grafana_service = self.list_enclave_services(enclave).get('services').get('grafana')
            self.grafanas[enclave] = grafana_service.get('public')


ENCLAVE_GRAFANA_PLUGIN = GrafanaView()


@ENCLAVE_GRAFANA_PLUGIN.blueprint.route('/<enclave>', methods=['GET'])
def grafana(enclave):
    """
    Render page

    :return: None
    """
    url = 'http://' + ENCLAVE_GRAFANA_PLUGIN.grafanas.get(enclave)
    return render_template('enclave-grafana.html', grafana_url=url)


ENCLAVE_GRAFANA_PLUGIN.register_plugin()
