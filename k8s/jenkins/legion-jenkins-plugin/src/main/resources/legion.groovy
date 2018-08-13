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


def modelId() {
    def modelId = legionProperties()['modelId']

    return (modelId == null) ? '<Model-Id is not defined>' : modelId
}

def modelVersion() {
    def modelVersion = legionProperties()['modelVersion']

    fileName = modelFileName()
    extendedVersionSubstring = (fileName =~ /\+(.+)\.model/)

    if (extendedVersionSubstring)
        extendedVersionSubstring = '-' + extendedVersionSubstring[0][1]
    else
        extendedVersionSubstring = ''

    return ((modelVersion == null) ? 'undefined' : modelVersion) + extendedVersionSubstring
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

def pod(Map podParams=null, Closure body) {
    if (podParams == null)
        podParams = [:]

    image = podParams.get('image', getDefaultImageName())
    cpu = podParams.get('cpu', '330m')
    ram = podParams.get('ram', '4Gi')

    envToPass = [
            "LEGION_PACKAGE_VERSION", "LEGION_PACKAGE_REPOSITORY", "LEGION_BASE_IMAGE_TAG",
            "LEGION_BASE_IMAGE_REPOSITORY",
            "EDI_USER", "EDI_PASSOWRD", "EDI_TOKEN",
            "EXTERNAL_RESOURCE_PROTOCOL", "EXTERNAL_RESOURCE_HOST", "EXTERNAL_RESOURCE_USER", "EXTERNAL_RESOURCE_PASSWORD",
            "MODEL_IMAGES_REGISTRY", "MODEL_IMAGES_REGISTRY_HOST", "DOCKER_REGISTRY_USER", "DOCKER_REGISTRY_PASSWORD",
            "GRAPHITE_HOST", "STATSD_HOST", "STATSD_PORT",
            "AIRFLOW_S3_URL", "AIRFLOW_REST_API", "AIRFLOW_DAGS_DIRECTORY", "DAGS_VOLUME_PVC"
    ]

    envVars = envToPass.collect({ name -> envVar(key: name, value: System.getenv(name)) })
    envVars << envVar(key: 'ENCLAVE_DEPLOYMENT_PREFIX', value: "${env.ENCLAVE_DEPLOYMENT_PREFIX}")
    envVars << envVar(key: 'MODEL_SERVER_URL', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${params.Enclave}-edge.${params.Enclave}")
    envVars << envVar(key: 'EDI_URL', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${params.Enclave}-edi.${params.Enclave}")

    label = "jenkins-build-${UUID.randomUUID().toString()}"

    def tolerations = """
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "jenkins-slave"
    effect: "NoSchedule"
"""

    podTemplate(
            label: label, yaml: tolerations,
            namespace: "${params.Enclave}",
            containers: [
                    containerTemplate(
                            name: 'model',
                            image: image,
                            resourceLimitMemory: ram,
                            resourceLimitCpu: cpu,
                            ttyEnabled: true,
                            command: 'cat',
                            envVars: envVars),
            ],
            volumes: [
                    hostPathVolume(hostPath: '/var/run/docker.sock', mountPath: '/var/run/docker.sock'),
                    persistentVolumeClaim(claimName: env.DAGS_VOLUME_PVC, mountPath: env.AIRFLOW_DAGS_DIRECTORY)

            ]) {
        node(label){
            container('model', body)
        }
    }
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

    sh """
    echo \$GRAPHITE_HOST

    pip3 install --extra-index-url \$LEGION_PACKAGE_REPOSITORY legion==\$LEGION_PACKAGE_VERSION
    export CONTAINER_DIR="`pwd`"
    cd ${env.ROOT_DIR}
    jupyter nbconvert --execute "${env.NOTEBOOK_NAME}" --stdout > notebook.html
    cp notebook.html "\$CONTAINER_DIR"
    """

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts 'notebook.html'
}

def runScript(scriptPath){
    env.ROOT_DIR = rootDir()
    env.TARGET_SCRIPT_PATH = scriptPath
    env.MODEL_ID = defaultModelId(scriptPath)

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'TARGET_SCRIPT_PATH = ' + env.TARGET_SCRIPT_PATH
    echo 'MODEL_ID = ' + env.MODEL_ID

    sh """
    pip3 install --extra-index-url \$LEGION_PACKAGE_REPOSITORY legion==\$LEGION_PACKAGE_VERSION
    export CONTAINER_DIR="`pwd`"
    cd ${env.ROOT_DIR}
    python3.6 "${env.TARGET_SCRIPT_PATH}" | tee script-log.txt

    echo "<html><body><h2>Script output</h2><pre>" > notebook.html
    cat script-log.txt >> notebook.html
    echo "</pre></body></html>" >> notebook.html

    cp script-log.txt "\$CONTAINER_DIR" || true
    cp notebook.html "\$CONTAINER_DIR" || true
    sleep 15
    """

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts 'script-log.txt'
    archiveArtifacts 'notebook.html'
}

def generateModelTemporaryImageName(modelId, modelVersion){
    Random random = new Random()
    randInt = random.nextInt(3000)
    return "legion_ci_${modelId}_${modelVersion}_${randInt}"
}

def build() {
    env.ROOT_DIR = rootDir()
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    baseDockerImage = getDefaultImageName()
    modelVersion = modelVersion()

    modelImageVersion = modelVersion
    env.TEMPORARY_DOCKER_IMAGE_NAME = generateModelTemporaryImageName(env.MODEL_ID, modelVersion)
    env.EXTERNAL_IMAGE_NAME = "${System.getenv('MODEL_IMAGES_REGISTRY')}${env.MODEL_ID}:${modelImageVersion}"

    sh """
    cd ${env.ROOT_DIR}
    legionctl build  \
    --docker-image-tag ${env.TEMPORARY_DOCKER_IMAGE_NAME} \
    --push-to-registry  ${env.EXTERNAL_IMAGE_NAME} \
    ${env.MODEL_FILE_NAME}
    """

}
def deploy(Map deployParams=null) {
    if (deployParams == null)
    deployParams = [:]

    count = deployParams.get('count', 1)
    livenesstimeout = deployParams.get('livenesstimeout', 2)
    readinesstimeout = deployParams.get('readinesstimeout', 2)
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()

    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    sh """
    legionctl undeploy --ignore-not-found ${env.MODEL_ID}
    legionctl deploy ${env.EXTERNAL_IMAGE_NAME} --livenesstimeout=${livenesstimeout} --readinesstimeout=${readinesstimeout}
    legionctl inspect
    """
}

def runTests() {
    env.ROOT_DIR = rootDir()
    env.MODEL_ID = modelId()

    echo 'MODEL_ID = ' + env.MODEL_ID

    sh """
    cd "${env.ROOT_DIR}/tests"
    MODEL_ID="${env.MODEL_ID}" nosetests --with-xunit
    """

    junit rootDir() + '/tests/nosetests.xml'
}

def runPerformanceTests(testScript) {
    env.ROOT_DIR = rootDir()
    env.TEST_SCRIPT = testScript
    env.ENCLAVE_DEPLOYMENT_PREFIX = sh(returnStdout: true, script: 'echo $ENCLAVE_DEPLOYMENT_PREFIX').trim()

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'TEST_SCRIPT = ' + env.TEST_SCRIPT

    modelApiHost = (params.host && params.host.length() > 0) ? params.host : "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${params.Enclave}-edge.${params.Enclave}"

    sh """
    echo "Starting quering ${modelApiHost}"
    pip3 install --extra-index-url \$LEGION_PACKAGE_REPOSITORY legion==\$LEGION_PACKAGE_VERSION
    cd ${env.ROOT_DIR}/performance/ && locust -f ${env.TEST_SCRIPT} --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${modelApiHost} --only-summary --logfile locust.log
    """

    archiveArtifacts rootDir() + '/performance/locust.log'
}

return this
