from drun.model_tests import LocustTaskSet, load_image
from locust import HttpLocust, task
import os


class TaskSet(LocustTaskSet):
    @task()
    def invoke_nine_decode(self):
        image = load_image(os.path.join('files', 'nine.png'))
        self._invoke_model(image=image)

    def on_start(self):
        self.setup_model('recognize_digits')


class TestLocust(HttpLocust):
    task_set = TaskSet
    min_wait = 0
    max_wait = 0
