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

from legion.console.plugins.enclave_plugin import EnclavePlugin


class HelloView(EnclavePlugin):
    """
    hello plugin
    """

    def __init__(self):
        """
        Construct per enclave 'hello' plugin(page)

        """
        super(HelloView, self).__init__(plugin_name='hello', url_prefix='/hello')


HELLO_PLUGIN = HelloView()


@HELLO_PLUGIN.blueprint.route('/<enclave>', methods=['GET'])
def hello(enclave):
    """
    Render page

    :return: None
    """
    return render_template('hello.html', enclave=enclave)
