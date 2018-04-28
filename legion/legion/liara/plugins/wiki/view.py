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
wiki plugin package
"""
from flask import render_template

from legion.liara.plugin import Plugin


class WikiView(Plugin):
    """
    wiki plugin
    """

    def __init__(self):
        super(WikiView, self).__init__('wiki', url_prefix='/wiki')


WIKI_PLUGIN = WikiView()
WIKI_PLUGIN.add_menu_item('wiki', '/wiki', 2)


@WIKI_PLUGIN.blueprint.route('/', methods=['GET'])
def wiki():
    """
    Render page

    :return: None
    """
    return render_template('wiki.html')


WIKI_PLUGIN.register_plugin()
