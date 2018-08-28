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

class Globals {
    /*
     * Storage for global script variables
     */

    // ENV variables (passed from K8S and extra)
    static envVars = [:]
}


def modelId() {
    /**
     * Get model id from stderr
     */
    def modelId = legionProperties()['modelId']

    return (modelId == null) ? '<Model-Id is not defined>' : modelId
}

def modelVersion() {
    /**
     * Get model version from stderr
     */
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
    /**
     * Get model file path from stderr
     */
    def fileName = legionProperties()['modelPath']

    if (fileName == null) {
        return '<Model-Path is not defined>'
    } else {
        return fileName
    }
}

def defaultModelId(notebookName) {
    /**
     * Get model id from file name
     */
    return (notebookName.indexOf('.') >= 0) ?
            notebookName.substring(0, notebookName.lastIndexOf('.')) : notebookName
}

def getDefaultImageName(){
    /**
     * Get default base image name
     */
    return System.getenv("LEGION_BASE_IMAGE_REPOSITORY") + ":" + System.getenv("LEGION_BASE_IMAGE_TAG")
}

def pod(Map podParams=null, Closure body) {
    /**
     * Run closure in jenkins slave on K8S pod
     */

    // Default arguments
    if (podParams == null)
        podParams = [:]
    
    // Parse parameters
    image = podParams.get('image', getDefaultImageName())
    cpu = podParams.get('cpu', '330m')
    ram = podParams.get('ram', '4Gi')
    enclave = podParams.get('enclave', '')

    // Override enclave if parameter has been passed
    if (params.Enclave)
        enclave = params.Enclave

    // Check enclave parameter
    if (!enclave){
        echo '[FAILURE] Parameter Enclave not defined!'
        currentBuild.result = 'FAILURE'
        return
    }
    else
        println "Using enclave ${enclave}"

    // Create list of env variables that should be passed to slave
    envToPass = [
            "LEGION_PACKAGE_VERSION", "LEGION_PACKAGE_REPOSITORY", "LEGION_BASE_IMAGE_TAG",
            "LEGION_BASE_IMAGE_REPOSITORY",
            "EDI_USER", "EDI_PASSOWRD", "EDI_TOKEN",
            "EXTERNAL_RESOURCE_PROTOCOL", "EXTERNAL_RESOURCE_HOST", "EXTERNAL_RESOURCE_USER", "EXTERNAL_RESOURCE_PASSWORD",
            "MODEL_IMAGES_REGISTRY", "MODEL_IMAGES_REGISTRY_HOST", "DOCKER_REGISTRY_USER", "DOCKER_REGISTRY_PASSWORD",
            "GRAPHITE_HOST", "STATSD_HOST", "STATSD_PORT",
            "AIRFLOW_S3_URL", "AIRFLOW_REST_API", "AIRFLOW_DAGS_DIRECTORY", "DAGS_VOLUME_PVC"
    ]

    // Collect list of ENV variables to pass to slave instance
    envVarsList = envToPass.collect({ name -> envVar(key: name, value: System.getenv(name)) })
    envVarsList << envVar(key: 'ENCLAVE', value: "${enclave}")
    envVarsList << envVar(key: 'ENCLAVE_DEPLOYMENT_PREFIX', value: "${env.ENCLAVE_DEPLOYMENT_PREFIX}")
    envVarsList << envVar(key: 'MODEL_SERVER_URL', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${enclave}-edge.${enclave}")
    envVarsList << envVar(key: 'EDI_URL', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${enclave}-edi.${enclave}")
    envVarsList << envVar(key: 'DEFAULT_MODEL_API_HOST', value: "http://${env.ENCLAVE_DEPLOYMENT_PREFIX}${enclave}-edge.${enclave}")

    // Copy to Globals map to share alongside functions
    envVarsList.each{ it -> Globals.envVars.putAt(it.toMap().key, it.toMap().value)}

    println 'Creating slave with env variables:'
    println Globals.envVars

    // Build pod
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
            namespace: "${enclave}",
            containers: [
                    containerTemplate(
                            name: 'model',
                            image: image,
                            resourceLimitMemory: ram,
                            resourceLimitCpu: cpu,
                            ttyEnabled: true,
                            command: 'cat',
                            envVars: envVarsList),
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
    /**
     * Get root directory from Jenkinsfile location of current Job
     */
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
    /**
     * Run Jupyter notebook using file name
     */
    Globals.envVars.ROOT_DIR = rootDir()
    Globals.envVars.NOTEBOOK_NAME = notebookName
    Globals.envVars.MODEL_ID = defaultModelId(notebookName)

    sh """
    pip3 install --extra-index-url \$LEGION_PACKAGE_REPOSITORY legion==\$LEGION_PACKAGE_VERSION
    export CONTAINER_DIR="`pwd`"
    cd ${Globals.envVars.ROOT_DIR}
    export MODEL_ID="${Globals.envVars.MODEL_ID}"
    jupyter nbconvert --execute "${Globals.envVars.NOTEBOOK_NAME}" --stdout > notebook.html
    cp notebook.html "\$CONTAINER_DIR"
    """

    sleep time: 1, unit: 'SECONDS'

    archiveArtifacts 'notebook.html'
}

def runScript(scriptPath){
    /**
     * Run Python script using file name
     */
    Globals.envVars.ROOT_DIR = rootDir()
    Globals.envVars.TARGET_SCRIPT_PATH = scriptPath
    Globals.envVars.MODEL_ID = defaultModelId(scriptPath)

    sh """
    pip3 install --extra-index-url \$LEGION_PACKAGE_REPOSITORY legion==\$LEGION_PACKAGE_VERSION
    export CONTAINER_DIR="`pwd`"
    export MODEL_ID="${Globals.envVars.MODEL_ID}"
    cd ${Globals.envVars.ROOT_DIR}
    python3.6 "${Globals.envVars.TARGET_SCRIPT_PATH}" | tee script-log.txt

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
    /**
     * Generate temporary docker image name
     */
    Random random = new Random()
    randInt = random.nextInt(3000)
    return "legion_ci_${modelId}_${modelVersion}_${randInt}"
}

def build() {
    /**
     * Build docker image with model from docker binary & push to nexus
     */
    Globals.envVars.ROOT_DIR = rootDir()
    Globals.envVars.MODEL_ID = modelId()
    Globals.envVars.MODEL_FILE_NAME = modelFileName()

    baseDockerImage = getDefaultImageName()
    modelVersion = modelVersion()

    modelImageVersion = modelVersion
    Globals.envVars.TEMPORARY_DOCKER_IMAGE_NAME = generateModelTemporaryImageName(Globals.envVars.MODEL_ID, modelVersion)
    Globals.envVars.EXTERNAL_IMAGE_NAME = "${System.getenv('MODEL_IMAGES_REGISTRY')}${Globals.envVars.MODEL_ID}:${modelImageVersion}"

    sh """
    cd ${Globals.envVars.ROOT_DIR}
    legionctl build  \
    --docker-image-tag ${Globals.envVars.TEMPORARY_DOCKER_IMAGE_NAME} \
    --push-to-registry  ${Globals.envVars.EXTERNAL_IMAGE_NAME} \
    ${Globals.envVars.MODEL_FILE_NAME}
    """

}
def deploy(Map deployParams=null) {
    /**
     * Deploy built docker image to K8S cluster (to specific enclave on a cluster)
     */
    Globals.envVars.MODEL_ID = modelId()
    Globals.envVars.MODEL_FILE_NAME = modelFileName()
    
    if (deployParams == null)
      deployParams = [:]

    count = deployParams.get('count', 1)
    livenesstimeout = deployParams.get('livenesstimeout', 2)
    readinesstimeout = deployParams.get('readinesstimeout', 2)

    sh """
    legionctl undeploy --ignore-not-found ${Globals.envVars.MODEL_ID}
    legionctl deploy ${Globals.envVars.EXTERNAL_IMAGE_NAME} --livenesstimeout=${livenesstimeout} --readinesstimeout=${readinesstimeout}
    legionctl inspect
    """
}

def runTests() {
    /**
     * Run tests
     */
    Globals.envVars.ROOT_DIR = rootDir()
    Globals.envVars.MODEL_ID = modelId()

    sh """
    cd "${Globals.envVars.ROOT_DIR}/tests"
    MODEL_ID="${Globals.envVars.MODEL_ID}" nosetests --with-xunit
    """

    junit rootDir() + '/tests/nosetests.xml'
}

def runPerformanceTests(testScript) {
    /**
     * Run performance tests from specific script
     */
    Globals.envVars.ROOT_DIR = rootDir()
    Globals.envVars.TEST_SCRIPT = testScript

    modelApiHost = params.host ? params.host : Globals.envVars.DEFAULT_MODEL_API_HOST

    sh """
    echo "Starting quering ${modelApiHost}"

    pip3 install --extra-index-url \$LEGION_PACKAGE_REPOSITORY legion==\$LEGION_PACKAGE_VERSION
    cd ${Globals.envVars.ROOT_DIR}/performance/ && locust -f ${Globals.envVars.TEST_SCRIPT} --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${modelApiHost} --only-summary --logfile locust.log
    """

    archiveArtifacts rootDir() + '/performance/locust.log'
}

return this
