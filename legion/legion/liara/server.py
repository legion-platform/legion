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
from legion.liara import plugins
from legion.containers import k8s


class Liara:
    """
    Liara server class
    """

    main_menu_items = []
    enclaves_menu_items = {}
    for enclave in k8s.list_enclaves():
        enclaves_menu_items[enclave] = []

    def start(self, args):
        """
        Start liara server

        :param args: arguments
        :type args: :py:class:`argparse.Namespace`
        :return: :py:class:`flask.Flask` -- liara web application
        """
        app = Flask(__name__)
        app.context_processor = lambda: dict(main_menu_label=Markup('<h2>Liara</h2>'),
                                             main_menu_items=self.main_menu_items,
                                             enclaves_menu_items=self.enclaves_menu_items)
        legion.http.configure_application(app, args)
        app.config['CLUSTER_SECRETS'] = k8s.load_secrets(app.config['CLUSTER_SECRETS_PATH'])
        with app.app_context():
            plugins.load()
        app.run(host=app.config['LEGION_API_ADDR'],
                port=app.config['LEGION_API_PORT'],
                debug=app.config['DEBUG'],
                use_reloader=False)
        return app

    def add_menu_item(self, menu_item: Markup):
        self.main_menu_items.append(menu_item)

    def add_enclave_menu_item(self, enclave_name: str, menu_item: Markup):
        self.enclaves_menu_items[enclave_name].append(menu_item)


liara = Liara()
