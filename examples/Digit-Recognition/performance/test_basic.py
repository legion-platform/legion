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
import os

from legion.model import load_image, ModelClient

from locust import HttpLocust, task, TaskSet


class ModelTaskSet(TaskSet):
    @task()
    def invoke_nine_decode(self):
        image = load_image(os.path.join('files', 'nine.png'))
        self._model_client.invoke(image=image)

    def on_start(self):
        self._model_client = ModelClient('recognize_digits', '1.0', use_relative_url=True, http_client=self.client)


class TestLocust(HttpLocust):
    task_set = ModelTaskSet
    min_wait = 0
    max_wait = 0
