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

node {
    def legion = load legion()

    legion.container('drun.kharlamov.biz/drun/base-python-image:latest') {
        stage('clone'){
            git url: 'https://github.com/akharlamov/drun-examples.git'
            sh '''
            pip install -i https://drun.kharlamov.biz/pypi/ drun
            '''
        }
        stage('run performance tests'){
            sh "cd Digit-Recognition/performance/ && locust -f test_basic.py --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${params.host} --only-summary --logfile locust.log"
            archiveArtifacts 'Digit-Recognition/performance/locust.log'
        }
    }
}
