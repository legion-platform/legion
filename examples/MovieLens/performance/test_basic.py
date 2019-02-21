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
from requests.exceptions import RequestException

from legion.model import ModelClient

from locust import HttpLocust, task, TaskSet
from legion.external.edi import build_client


class ModelTaskSet(TaskSet):
    @task()
    def invoke_nine_decode(self):
        self._model_client.invoke(uid=1)

    def on_start(self):
        self._model_client = ModelClient('movie-lens', '1.0', use_relative_url=True, http_client=self.client,
                                         http_exception=RequestException,
                                         token=build_client().get_token('movie-lens', '1.0'))


class TestLocust(HttpLocust):
    task_set = ModelTaskSet
    min_wait = 0
    max_wait = 0
