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
Extensions for robot framework API
"""

import robot.libraries.Process
import robot.running


def get_imported_library_instance(name):
    """
    Get library instance from storage

    :param name: name of library
    :type name: str
    :return: library instance or None (e.g. robot.libraries.Process.Process instance)
    """
    context = robot.running.context.EXECUTION_CONTEXTS.current
    namespace = context.namespace
    imported = namespace._kw_store.libraries
    if name not in imported:
        return None
    return imported[name]._libinst
