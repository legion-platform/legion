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
Variables loader (from profiles/{env.PROFILE}.ansible.yml files)
"""

import legion_test.profiler_loader
import legion_test.test_assets


def get_variables(arg):
    """
    Gather and return all variables to robot

    :param arg: path to directory with profiles
    :type args: str
    :return: dict[str, Any] -- values for robot
    """
    variables = legion_test.profiler_loader.get_variables(arg)
    variables['TEST_MODEL_IMAGE'] = legion_test.test_assets.get_test_bare_model_api_image(variables)

    return variables
