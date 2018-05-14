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
console plugins package
"""
import os
import importlib


def load():
    """
    Load all available plugins in package

    :return: None
    """
    plugins_path = os.path.dirname(os.path.abspath(__file__))
    for plugin_name in os.listdir(plugins_path):
        if os.path.isdir(os.path.join(plugins_path, plugin_name)):
            plugin_module = __name__ + '.' + plugin_name
            importlib.import_module(plugin_module)
