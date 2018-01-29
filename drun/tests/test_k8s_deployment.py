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
from __future__ import print_function

import unittest2
from argparse import Namespace

import drun.deploy as deploy
import drun.k8s as k8s
import drun.docker


class TestK8SDeployment(unittest2.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_k8s(self):
        arguments = Namespace(
            image='nexus.epm.kharlamov.biz/drun_model/a:10',
            image_for_k8s='nexus.local.epm.kharlamov.biz/drun_model/a:10',
            scale=2,
            namespace='default',
            deployment='drun',
            text_output=False
        )

        deployment = deploy.deploy_kubernetes(arguments)
        x = 10


if __name__ == '__main__':
    unittest2.main()
