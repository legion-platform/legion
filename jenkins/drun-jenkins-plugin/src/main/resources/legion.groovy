#!groovy

/**
 *   Copyright 2017 EPAM Systems
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

def dockerArgs(){
    return '-v drun:/drun -u 0:0' +
        ' --network=drun_drun_root' +
        ' -e "DOCKER_TLS_VERIFY=1"'+
        ' -e "DOCKER_HOST=${DOCKER_HOST}"'+
        ' -e "DOCKER_CERT_PATH=${DOCKER_CERT_PATH}"'+
        ' -e "MODEL_SERVER_URL=${DRUN_MODEL_SERVER_URL}"'
}

def modelId(){
    def modelId = legionProperties()['modelId']

    return (modelId == null) ? '<Model-Id is not defined>' : modelId
}

def modelFileName(){
    def fileName = legionProperties()['modelPath']

    if (fileName == null) {
        return '<Model-Path is not defined>'
    } else {
        return (fileName.indexOf('/') >= 0) ?
                fileName.substring(fileName.lastIndexOf('/') + 1) : fileName
    }
}

def defaultModelId(notebookName) {
    return (notebookName.indexOf('.') >= 0) ?
        notebookName.substring(0, notebookName.lastIndexOf('.')) : notebookName
}

def container(myImageName, Closure body){
    docker.image(myImageName).inside(dockerArgs(), body)
}

def rootDir(){
    def result = '.'

    try {
        def scriptFile = Jenkins.instance.getItemByFullName(env.JOB_NAME).definition.getScriptPath()
        if (scriptFile.indexOf('/') >= 0) {
            result = scriptFile.substring(0, scriptFile.lastIndexOf('/'))
        }
    } catch (groovy.lang.MissingMethodException ex) {
        echo 'No script path, perhaps inline pipeline'
    }

    return result
}

def runNotebook(notebookName){
    env.ROOT_DIR = rootDir()
    env.NOTEBOOK_NAME = notebookName
    env.MODEL_ID = defaultModelId(notebookName)

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'NOTEBOOK_NAME = ' + env.NOTEBOOK_NAME
    echo 'MODEL_ID = ' + env.MODEL_ID

    sh '''
    pip install -i https://drun.kharlamov.biz/pypi/ drun
    export CONTAINER_DIR="`pwd`"
    cd ${ROOT_DIR}
    jupyter nbconvert --execute "${NOTEBOOK_NAME}" --stdout > notebook.html
    cp notebook.html "${CONTAINER_DIR}"
    mkdir -p "${CONTAINER_DIR}"/release-models
    cp -rf /drun/* "${CONTAINER_DIR}"/release-models/
    '''

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts 'release-models/' + modelFileName()
    archiveArtifacts 'notebook.html'
}

def build(){
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()

    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    sh '''
    legion build release-models/${MODEL_FILE_NAME}
    '''
}

def deploy(){
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()

    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    sh '''
    legion deploy --model-id ${MODEL_ID}
    '''

    sleep time: 20, unit: 'SECONDS'
}

def runTests(){
    env.ROOT_DIR = rootDir()
    env.MODEL_ID = modelId()

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'MODEL_ID = ' + env.MODEL_ID

    sh '''
    cd "${ROOT_DIR}/tests"
    nosetests --with-xunit
    '''

    junit rootDir() + '/tests/nosetests.xml'
}

def runPerformanceTests(testScript){
    env.ROOT_DIR = rootDir()
    env.MODEL_ID = modelId()
    env.TEST_SCRIPT = testScript

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'TEST_SCRIPT = ' + env.TEST_SCRIPT

    sh '''
    pip install -i https://drun.kharlamov.biz/pypi/ drun
    cd ${rootDir}/performance/ && locust -f ${TEST_SCRIPT} --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${params.host} --only-summary --logfile locust.log
    '''

    archiveArtifacts rootDir() + '/performance/locust.log'
}

return this
