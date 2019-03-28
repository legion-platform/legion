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
from legion.robot import profiler_loader
from legion.robot.test_assets import get_test_bare_model_api_image


def get_variables(arg):
    """
    Gather and return all variables to robot

    :param arg: path to directory with profiles
    :type args: str
    :return: dict[str, Any] -- values for robot
    """
    variables = profiler_loader.get_variables(arg)
    variables['TEST_MODEL_IMAGE_1'] = get_test_bare_model_api_image(variables, 1)
    variables['TEST_MODEL_IMAGE_2'] = get_test_bare_model_api_image(variables, 2)
    variables['TEST_MODEL_IMAGE_3'] = get_test_bare_model_api_image(variables, 3)
    variables['TEST_MODEL_IMAGE_4'] = get_test_bare_model_api_image(variables, 4)
    variables['TEST_MODEL_IMAGE_5'] = get_test_bare_model_api_image(variables, 5)
    variables['TEST_MODEL_IMAGE_6'] = get_test_bare_model_api_image(variables, 6)

    return variables
