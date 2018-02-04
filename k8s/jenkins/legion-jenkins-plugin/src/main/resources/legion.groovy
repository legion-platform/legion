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

def dockerArgs() {
    def envToPass = ["LEGION_PACKAGE_VERSION", "LEGION_PACKAGE_REPOSITORY", "LEGION_BASE_IMAGE_TAG",
                     "LEGION_BASE_IMAGE_REPOSITORY", "MODEL_SERVER_URL", "EDI_URL", "EDI_USER",
                     "EDI_PASSOWRD", "EDI_TOKEN", "EXTERNAL_RESOURCE_PROTOCOL", "EXTERNAL_RESOURCE_HOST",
                     "EXTERNAL_RESOURCE_USER", "EXTERNAL_RESOURCE_PASSWORD", "MODEL_IMAGES_REGISTRY",
                     "GRAPHITE_HOST", "STATSD_HOST", "STATSD_PORT", "CONSUL_ADDR", "CONSUL_PORT"
    ]

    def envParameters = envToPass.collect({ name -> "-e \"${name}=${System.getenv(name)}\"" }).join(" ")
    data = new File('/etc/resolv.conf').text

    nameserver = (data =~ /nameserver ([0-9\.]+)/)[0][1]
    search = (data =~ /search ([^$\n]+)/)[0][1].split(" ")

    searchArguments = search.collect({ name -> "--dns-search=$name" }).join(" ")

    dnsArguments = "--dns=$nameserver $searchArguments "

    return "-v legion:/legion -v /var/run/docker.sock:/var/run/docker.sock $dnsArguments -u 0:0 $envParameters"
}

def modelId() {
    def modelId = legionProperties()['modelId']

    return (modelId == null) ? '<Model-Id is not defined>' : modelId
}

def modelVersion() {
    def modelVersion = legionProperties()['modelVersion']

    return (modelVersion == null) ? 'undefined' : modelVersion
}

def modelFileName() {
    def fileName = legionProperties()['modelPath']

    if (fileName == null) {
        return '<Model-Path is not defined>'
    } else {
        return fileName
    }
}

def defaultModelId(notebookName) {
    return (notebookName.indexOf('.') >= 0) ?
            notebookName.substring(0, notebookName.lastIndexOf('.')) : notebookName
}

def getDefaultImageName(){
    return System.getenv("LEGION_BASE_IMAGE_REPOSITORY") + ":" + System.getenv("LEGION_BASE_IMAGE_TAG")
}

def container(myImageName, Closure body) {
    if (myImageName == null)
        myImageName = getDefaultImageName()

    docker.image(myImageName).inside(dockerArgs(), body)
}

def rootDir() {
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

def runNotebook(notebookName) {
    env.ROOT_DIR = rootDir()
    env.NOTEBOOK_NAME = notebookName
    env.MODEL_ID = defaultModelId(notebookName)

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'NOTEBOOK_NAME = ' + env.NOTEBOOK_NAME
    echo 'MODEL_ID = ' + env.MODEL_ID

    sh '''
    pip install --extra-index-url ${LEGION_PACKAGE_REPOSITORY} legion==${LEGION_PACKAGE_VERSION}
    export CONTAINER_DIR="`pwd`"
    cd ${ROOT_DIR}
    jupyter nbconvert --execute "${NOTEBOOK_NAME}" --stdout > notebook.html
    cp notebook.html "${CONTAINER_DIR}"
    '''

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts 'notebook.html'
}

def generateModelTemporaryImageName(modelId, modelVersion){
    Random random = new Random()
    randInt = random.nextInt(3000)
    return "legion_ci_${modelId}_${modelVersion}_${randInt}"
}

def build() {
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()

    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    baseDockerImage = getDefaultImageName()
    modelVersion = modelVersion()

    // TODO: What to use for version of model image?
    modelImageVersion = modelVersion
    temporaryDockerImageName = generateModelTemporaryImageName(env.MODEL_ID, modelVersion)
    externalImageName = "${env.MODEL_IMAGES_REGISTRY}${env.MODEL_ID}:${modelImageVersion}"
    env.EXTERNAL_IMAGE_NAME = externalImageName

    // TODO: Move to Dockerfile ?
    sh """
    apt-get update && apt-get install --yes apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian jessie stable"
    apt-get update && apt-get install --yes docker-ce
    """

    sh """
    legionctl build --python-package-version ${env.LEGION_PACKAGE_VERSION} \
    --python-repository ${env.LEGION_PACKAGE_REPOSITORY} --base-docker-image $baseDockerImage \
    --docker-image-tag ${temporaryDockerImageName} \
    ${env.MODEL_FILE_NAME}
    """

    sh """
    docker login -u ${env.EXTERNAL_RESOURCE_USER} -p ${env.EXTERNAL_RESOURCE_PASSWORD} ${env.MODEL_IMAGES_REGISTRY}

    docker tag ${temporaryDockerImageName} ${externalImageName}
    docker push ${externalImageName}

    docker rmi ${temporaryDockerImageName}
    docker rmi ${externalImageName}
    """
}

def deploy() {
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()

    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    sh '''
    legionctl deploy $EXTERNAL_IMAGE_NAME
    '''

    sleep time: 10, unit: 'SECONDS'

    sh '''
    legionctl inspect
    '''
}

def runTests() {
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

def runPerformanceTests(testScript) {
    env.ROOT_DIR = rootDir()
    env.TEST_SCRIPT = testScript

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'TEST_SCRIPT = ' + env.TEST_SCRIPT

    modelApiHost = (params.host && params.host.length() > 0) ? params.host : env.MODEL_SERVER_URL

    sh """
    pip install --extra-index-url ${env.LEGION_PACKAGE_REPOSITORY} legion==${env.LEGION_PACKAGE_VERSION}
    cd ${env.ROOT_DIR}/performance/ && locust -f ${env.TEST_SCRIPT} --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${modelApiHost} --only-summary --logfile locust.log
    """

    archiveArtifacts rootDir() + '/performance/locust.log'
}

return this
