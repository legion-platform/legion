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
from legion.model import ModelClient

from locust import HttpLocust, task, TaskSet


class ModelTaskSet(TaskSet):
    @task()
    def invoke_nine_decode(self):
        dataset = {'age': 31,
                   'capital-gain': 14084,
                   'capital-loss': 0,
                   'education': 'Bachelors',
                   'education-num': 13,
                   'fnlwgt': 77516,
                   'hours-per-week': 40,
                   'marital-status': 'Married-civ-spouse',
                   'native-country': 'United-States',
                   'occupation': 'Exec-managerial',
                   'race': 'White',
                   'relationship': 'Husband',
                   'sex': 'Male',
                   'workclass': 'Private'}
        self._model_client.invoke(**dataset)

    def on_start(self):
        self._model_client = ModelClient('income', '1.1', use_relative_url=True, http_client=self.client)


class TestLocust(HttpLocust):
    task_set = ModelTaskSet
    min_wait = 0
    max_wait = 0
