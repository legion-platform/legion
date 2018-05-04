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
homepage plugin package
"""
from flask import render_template, current_app

from legion.liara.plugins.plugin import Plugin


class HomepageView(Plugin):
    """
    homepage plugin
    """

    def __init__(self):
        super(HomepageView, self).__init__('homepage', url_prefix='/')


HOMEPAGE_PLUGIN = HomepageView()
HOMEPAGE_PLUGIN.blueprint.static_url_path = 'homepage'
DASHBOARD_URL = 'http://' + current_app.config['CLUSTER_SECRETS']['dashboard.public']


@HOMEPAGE_PLUGIN.blueprint.route('/', methods=['GET'])
def homepage():
    """
    Render page

    :return: None
    """
    return render_template('homepage.html', dashboard_url=DASHBOARD_URL)


HOMEPAGE_PLUGIN.register_plugin()
