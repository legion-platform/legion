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
homepage plugin package
"""
from flask import render_template

from legion.containers import explorer
from legion.console.plugins.plugin import Plugin
from legion.console.server import CONSOLE


class HomepageView(Plugin):
    """
    homepage plugin
    """

    def __init__(self):
        """
        Construct 'home page' plugin(page)

        """
        super(HomepageView, self).__init__('homepage', url_prefix='/')

    def get_menu_item_index(self):
        """
        Return menu item index. Zero(0) as default.

        :return: int -- menu item index
        """
        return 0


HOMEPAGE_PLUGIN = HomepageView()
HOMEPAGE_PLUGIN.blueprint.static_url_path = 'homepage'


@HOMEPAGE_PLUGIN.blueprint.route('/', methods=['GET'])
def homepage():
    """
    Render page

    :return: None
    """
    dashboard_url = 'https://{}'.format(explorer.get_public_dashboard_hostname())
    return render_template('homepage.html', dashboard_url=dashboard_url)


CONSOLE.add_plugin(HOMEPAGE_PLUGIN)
