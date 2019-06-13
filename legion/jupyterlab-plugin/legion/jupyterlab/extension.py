#
#    Copyright 2019 EPAM Systems
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
Main extension module
"""
from notebook.utils import url_path_join

from legion.jupyterlab.api_state import ApiState
from legion.jupyterlab.handlers import register_all_handlers

LEGION_API_ROOT = 'legion', 'api'


def load_jupyter_server_extension(nb_server_app):
    """
    Call when the extension is loaded.

    :param nb_server_app: handle to the Notebook webserver instance.
    :type nb_server_app: NotebookWebApplication
    :return None
    """
    web_app = nb_server_app.web_app
    logger = nb_server_app.log

    host_pattern = '.*$'
    base_url = web_app.settings['base_url']

    root_api = url_path_join(base_url, *LEGION_API_ROOT)
    logger.info('Using %r as root for Legion plugin API', root_api)

    state = ApiState()

    init_args = {
        'logger': logger,
        'state': state
    }

    register_all_handlers(logger, web_app, host_pattern, init_args, root_api)
