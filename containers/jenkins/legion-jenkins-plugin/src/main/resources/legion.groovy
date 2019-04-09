#!groovy

/**
 *   Copyright 2019 EPAM Systems
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

    return (modelVersion == null) ? '<Model-Version is not defined>' : modelVersion
}

def modelExtendedVersion() {
    def modelVersionString = modelVersion()

    fileName = modelFileName()
    extendedVersionSubstring = (fileName =~ /\+(.+)\.model/)

    if (extendedVersionSubstring)
        extendedVersionSubstring = '-' + extendedVersionSubstring[0][1]
    else
        extendedVersionSubstring = ''

    return ((modelVersionString == null) ? 'undefined' : modelVersionString) + extendedVersionSubstring
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

    if ( params.Enclave == "" ) {
        echo '[FAILURE] Parameter Enclave not defined!'
        currentBuild.result = 'FAILURE'
        return
    }

    def annotations = []

    model_image = podParams.get('image', getDefaultImageName())
    builder_image = "${System.getenv('LEGION_EDI_IMAGE')}"
    cpu = podParams.get('cpu', '330m')
    ram = podParams.get('ram', '4Gi')
    iamRole = podParams.get('iamRole', "${System.getenv('CLUSTER_NAME')}-${params.Enclave}-jslave-role")
    annotations << podAnnotation(key: 'iam.amazonaws.com/role', value: iamRole)

    envToPass = [
            "LEGION_PACKAGE_VERSION", "LEGION_PACKAGE_REPOSITORY", "LEGION_BASE_IMAGE_TAG",
            "LEGION_BASE_IMAGE_REPOSITORY",
            "EXTERNAL_RESOURCE_PROTOCOL", "EXTERNAL_RESOURCE_HOST", "EXTERNAL_RESOURCE_USER", "EXTERNAL_RESOURCE_PASSWORD",
            "CLUSTER_PREFIX", "DOCKER_REGISTRY", "DOCKER_REGISTRY_USER", "DOCKER_REGISTRY_PASSWORD",
            "METRICS_HOST", "METRICS_PORT", "MODEL_TRAIN_METRICS_ENABLED", "S3_BUCKET_NAME"
    ]

    envVars = envToPass.collect({ name -> envVar(key: name, value: System.getenv(name)) })
    envVars << envVar(key: 'ENCLAVE_DEPLOYMENT_PREFIX', value: "${env.ENCLAVE_DEPLOYMENT_PREFIX}")
    envVars << envVar(key: 'NAMESPACE', value: "${params.Enclave}")
    envVars << envVar(key: 'MODEL_SERVER_URL', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${params.Enclave}-edge.${params.Enclave}")
    envVars << envVar(key: 'EDI_URL', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${params.Enclave}-edi.${params.Enclave}")

    label = "jenkins-build-${UUID.randomUUID().toString()}"

    def tolerations = """
spec:
  containers:
  - name: builder
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    volumeMounts:
    - mountPath: "/var/run/docker.sock"
      name: docker-socket
  volumes:
  - name: docker-socket
    hostPath:
      path: "/var/run/docker.sock"
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "jenkins-slave"
    effect: "NoSchedule"
"""

    podTemplate(
            label: label, yaml: tolerations,
            namespace: "${params.Enclave}",
            annotations: annotations,
            containers: [
                    containerTemplate(
                            name: 'model',
                            image: model_image,
                            resourceLimitMemory: ram,
                            resourceLimitCpu: cpu,
                            ttyEnabled: true,
                            command: 'cat',
                            envVars: envVars
                    ),
                    containerTemplate(
                            name: 'builder',
                            image: builder_image,
                            resourceLimitMemory: '100Mi',
                            resourceLimitCpu: '100m',
                            ttyEnabled: true,
                            command: '/usr/local/bin/uwsgi',
                            serviceAccount: 'jenkins',
                            args: '--strict --ini /etc/uwsgi/model_builder_uwsgi.ini',
                            envVars: envVars
                    )
            ],
            serviceAccount: "model-builder"
    ) {
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
    export INIT_DIR="`pwd`"
    rm -f notebook.html

    cd "${env.ROOT_DIR}"
    jupyter nbconvert --execute "${env.NOTEBOOK_NAME}" --stdout > "\$INIT_DIR/notebook.html"
    """

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts "notebook.html"
}

def runScript(scriptPath){
    env.ROOT_DIR = rootDir()
    env.TARGET_SCRIPT_PATH = scriptPath
    env.MODEL_ID = defaultModelId(scriptPath)

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'TARGET_SCRIPT_PATH = ' + env.TARGET_SCRIPT_PATH
    echo 'MODEL_ID = ' + env.MODEL_ID

    sh """
    export INIT_DIR="`pwd`"
    rm -f notebook.html
    rm -f script-log.txt

    cd "${env.ROOT_DIR}"
    python3.6 "${env.TARGET_SCRIPT_PATH}" | tee "\$INIT_DIR/script-log.txt"

    echo "<html><body><h2>Script output</h2><pre>" > "\$INIT_DIR/notebook.html"
    cat "\$INIT_DIR/script-log.txt" >> "\$INIT_DIR/notebook.html"
    echo "</pre></body></html>" >> "\$INIT_DIR/notebook.html"

    sleep 15
    """

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts "script-log.txt"
    archiveArtifacts "notebook.html"
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
    modelVersion = modelExtendedVersion()

    modelImageVersion = modelVersion
    env.TEMPORARY_DOCKER_IMAGE_NAME = generateModelTemporaryImageName(env.MODEL_ID, modelVersion)
    dockerName = "${System.getenv('CLUSTER_PREFIX')}/${params.Enclave}-${env.MODEL_ID}"
    env.EXTERNAL_IMAGE_NAME = "${System.getenv('DOCKER_REGISTRY')}/${dockerName}:${modelImageVersion}"

    sh """
    cd ${env.ROOT_DIR}
    legionctl --verbose build  \
    --build-type docker-remote \
    --docker-image-tag ${env.TEMPORARY_DOCKER_IMAGE_NAME} \
    --push-to-registry  ${env.EXTERNAL_IMAGE_NAME} \
    --model-file "${env.MODEL_FILE_NAME}"
    """

}
def deploy(Map deployParams=null) {
    if (deployParams == null)
        deployParams = [:]

    count = deployParams.get('count', 1)
    livenesstimeout = deployParams.get('livenesstimeout', 2)
    readinesstimeout = deployParams.get('readinesstimeout', 2)
    modelIamRole = deployParams.get('modelIamRole', "${System.getenv('CLUSTER_NAME')}-${params.Enclave}-model-role")
    deploytimeout = deployParams.get('deploytimeout', 300)
    env.MODEL_ID = modelId()
    env.MODEL_FILE_NAME = modelFileName()
    env.MODEL_VERSION = legionProperties()['modelVersion']

    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_FILE_NAME = ' + env.MODEL_FILE_NAME

    sh """
    legionctl --verbose undeploy --ignore-not-found ${env.MODEL_ID} --model-version ${env.MODEL_VERSION}
    legionctl --verbose deploy ${env.EXTERNAL_IMAGE_NAME} --model-iam-role=${modelIamRole} --livenesstimeout=${livenesstimeout} --readinesstimeout=${readinesstimeout} --timeout=${deploytimeout}
    legionctl --verbose inspect
    """
}

def runTests() {
    env.ROOT_DIR = rootDir()
    env.MODEL_ID = modelId()
    env.MODEL_VERSION = modelVersion()

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'MODEL_ID = ' + env.MODEL_ID
    echo 'MODEL_VERSION = ' + env.MODEL_VERSION

    sh """
    export INIT_DIR="`pwd`"
    rm -f nosetests.xml

    pip3 install nose

    cd "${env.ROOT_DIR}/tests"
    MODEL_ID="${env.MODEL_ID}" MODEL_VERSION="${env.MODEL_VERSION}" nosetests --with-xunit --xunit-file "\$INIT_DIR/nosetests.xml"
    """

    junit "nosetests.xml"
}

def runPerformanceTests(testScript) {
    env.ROOT_DIR = rootDir()
    env.TEST_SCRIPT = testScript
    env.ENCLAVE_DEPLOYMENT_PREFIX = sh(returnStdout: true, script: 'echo $ENCLAVE_DEPLOYMENT_PREFIX').trim()

    echo 'ROOT_DIR = ' + env.ROOT_DIR
    echo 'TEST_SCRIPT = ' + env.TEST_SCRIPT

    modelApiHost = (params.host && params.host.length() > 0) ? params.host : "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${params.Enclave}-edge.${params.Enclave}"

    sh """
    export INIT_DIR="`pwd`"
    rm -f locust.log

    echo "Starting querying ${modelApiHost}"

    cd ${env.ROOT_DIR}/performance/
    locust -f ${env.TEST_SCRIPT} --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${modelApiHost} --only-summary --logfile "\$INIT_DIR/locust.log"
    """

    archiveArtifacts "locust.log"
}

return this