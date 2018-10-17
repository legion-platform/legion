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
legion k8s exceptions
"""


class UnknownDeploymentForModelService(Exception):
    """
    Exception occurs when module cannot find K8S Deployment for existed K8SService
    """

    def __init__(self, model_service_name):
        """
        Build exception instance

        :param model_service_name: name of model service
        :type model_service_name: str
        """
        super().__init__('Cannot find deployment for model service {!r}'.format(model_service_name))
