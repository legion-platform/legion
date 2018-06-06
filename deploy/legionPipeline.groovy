def installTools(){
    sh '''
    sudo rm -rf .venv
    virtualenv .venv -p $(which python3)
    cd legion_test
    ../.venv/bin/python3 setup.py develop
    '''
}

def createCluster() {
    dir('deploy/ansible'){
        withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    ansiblePlaybook(
                        playbook: 'create-cluster.yml',
                        extras: ' --extra-vars "profile=${params.Profile} skip_kops=${params.Skip_kops}"',
                        colorized: true
                    )
                }
            }
        }
    }
}

def terminateCluster() {
    dir('deploy/ansible'){
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                ansiblePlaybook(
                    playbook: 'terminate-cluster.yml',
                    extras: ' --extra-vars "profile=${params.Profile}"',
                    colorized: true
                )
            }
        }
    }
}

def deployLegion() {
    if (params.DeployLegion){
        dir('deploy/ansible'){
            withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
                withAWS(credentials: 'kops') {
                    wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                        ansiblePlaybook(
                            playbook: 'deploy-legion.yml',
                            extras: ' --extra-vars "profile=${params.Profile} base_version=${params.BaseVersion}  local_version=${params.LocalVersion}"',
                            colorized: true
                        )
                    }
                }
            }
        }
    }
    else {
            print("Skipping Legion Deployment")
    }
}

def createjenkinsJobs() {
    sh """
    cd legion_test
    ../.venv/bin/pip install -r requirements/base.txt
    ../.venv/bin/pip install -r requirements/test.txt
    ../.venv/bin/python setup.py develop
    cd ..

    .venv/bin/create_example_jobs \
    "https://jenkins.${params.Profile}" \
    examples \
    . \
    "git@github.com:epam/legion.git" \
    ${targetBranch} \
    --connection-timeout 600 \
    --git-root-key "legion-root-key" \
    --model-host "" \
    --dynamic-model-prefix "DYNAMIC MODEL"
    """
}

def runRobotTests() {
    withAWS(credentials: 'kops') {
        sh '''
        cd legion_test
        ../.venv/bin/pip install -r requirements/base.txt
        ../.venv/bin/pip install -r requirements/test.txt
        ../.venv/bin/python setup.py develop

        cd ../tests
        ../.venv/bin/pip install yq

        PATH_TO_PROFILE="../deploy/profiles/$Profile.yml"
        CLUSTER_NAME=$(yq -r .cluster_name $PATH_TO_PROFILE)
        CLUSTER_STATE_STORE=$(yq -r .state_store $PATH_TO_PROFILE)
        echo "Loading kubectl config from $CLUSTER_STATE_STORE for cluster $CLUSTER_NAME"

        kops export kubecfg --name $CLUSTER_NAME --state $CLUSTER_STATE_STORE

        DISPLAY=:99 PROFILE=$Profile ../.venv/bin/python3 -m robot.run *.robot || true
        '''
        step([
            $class : 'RobotPublisher',
            outputPath : 'tests/',
            outputFileName : "*.xml",
            disableArchiveOutput : false,
            passThreshold : 100,
            unstableThreshold: 95.0,
            onlyCritical : true,
            otherFiles : "*.png",
        ])
    }
}

def deployLegionEnclave() {
    dir('deploy/ansible'){
        withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    ansiblePlaybook(
                        playbook: 'deploy-legion-enclave.yml',
                        extras: ' --extra-vars "profile=${params.Profile} base_version=${params.BaseVersion}  local_version=${params.LocalVersion} enclave_name=${params.EnclaveName}"',
                        colorized: true
                    )
                }
            }
        }
    }
}

def terminateLegionEnclave() {
    dir('deploy/ansible'){
        withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    ansiblePlaybook(
                        playbook: 'terminate-legion-enclave.yml',
                            extras: ' --extra-vars "profile=${Profile} enclave_name=${EnclaveName}"',
                            colorized: true
                        )
                }
            }
        }
    }
}

def buildDescription(){
	currentBuild.description = "${params.Profile} ${params.GitBranch}"
}

def notifyBuild(String buildStatus = 'STARTED') {
    // build status of null means successful
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    def previousBuild = currentBuild.getPreviousBuild()
    def previousBuildResult = previousBuild != null ? previousBuild.result : null

    def currentBuildResultSuccessful = buildStatus == 'SUCCESSFUL' || buildStatus == 'SUCCESS'
    def previousBuildResultSuccessful = previousBuildResult == 'SUCCESSFUL' || previousBuildResult == 'SUCCESS'

    def masterOrDevelopBuild = params.GitBranch == 'origin/develop' || params.GitBranch == 'origin/master'

    print("NOW SUCCESSFUL: ${currentBuildResultSuccessful}, PREV SUCCESSFUL: ${previousBuildResultSuccessful}, MASTER OR DEV: ${masterOrDevelopBuild}")

    if (!masterOrDevelopBuild)
        return

    // Skip green -> green
    if (currentBuildResultSuccessful && previousBuildResultSuccessful)
        return

    // Default values
    def colorCode = '#FF0000'
    def summary = """\
    @here Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}* (previous: ${previousBuildResult})
    branch *${params.GitBranch}*
    profile *<https://${params.Profile}|${params.Profile}>*
    Manage: <${env.BUILD_URL}|Open>, <${env.BUILD_URL}/consoleFull|Full logs>, <${env.BUILD_URL}/parameters/|Parameters>
    """.stripIndent()

    // Override default values based on build status
    if (buildStatus == 'STARTED') {
        colorCode = '#FFFF00'
    } else if (buildStatus == 'SUCCESSFUL') {
        colorCode = '#00FF00' 
    } else {
        colorCode = '#FF0000'
    }

    slackSend (color: colorCode, message: summary)
}
return this