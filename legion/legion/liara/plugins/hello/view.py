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

from legion.liara.plugin import Plugin


class HelloView(Plugin):
    """
    hello plugin
    """

    def __init__(self):
        super(HelloView, self).__init__('hello', url_prefix='/hello')


HELLO_PLUGIN = HelloView()
ITEM = 'submenu<ul><li><a href="{}">{}</a></li></ul>'.format('/hello', 'hello')
HELLO_PLUGIN.add_custom_menu_item(ITEM, 1)


@HELLO_PLUGIN.blueprint.route('/', methods=['GET'])
def hello():
    """
    Render page

    :return: None
    """
    return render_template('hello.html')


HELLO_PLUGIN.register_plugin()
