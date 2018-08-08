def installTools(){
    sh '''
    sudo rm -rf .venv
    virtualenv .venv -p $(which python3)

    cd legion
    ../.venv/bin/python3 setup.py develop
    cd ..

    cd legion_test
    ../.venv/bin/python3 setup.py develop
    '''
}

def buildDescription(){
   currentBuild.description = "${params.Profile} ${params.GitBranch}"
}

def createCluster() {
    dir('deploy/ansible'){
        sh 'env'
        withCredentials([
            file(credentialsId: "vault-${params.Profile}", variable: 'vault')]) {
            withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                ansiblePlaybook(
                    playbook: 'create-cluster.yml',
                    extras: '--vault-password-file=${vault} \
                            --extra-vars "profile=${Profile} \
                            skip_kops=${Skip_kops}"',
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
                    extras: ' --extra-vars "profile=${Profile}"',
                    colorized: true
                )
            }
        }
    }
}

def deployLegion() {
    dir('deploy/ansible'){
        withCredentials([file(credentialsId: "vault-${params.Profile}", variable: 'vault')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    if (params.PublicRelease){
                        ansiblePlaybook(
                            playbook: 'deploy-legion.yml',
                            extras: '--vault-password-file=${vault} \
                                     --extra-vars "profile=${Profile} \
                                     legion_version=${LegionVersion} \
                                     pypi_repo=${PypiRepo} \
                                     docker_repo=${DockerRepo}" ',
                            colorized: true
                         )
                    } else {
                        ansiblePlaybook(
                            playbook: 'deploy-legion.yml',
                            extras: '--vault-password-file=${vault} \
                                     --extra-vars "profile=${Profile} \
                                     legion_version=${LegionVersion}" ',
                            colorized: true
                        )
                        
                    }
                }
            }
        }
    }
}

def createjenkinsJobs(String commitID) {
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
    ${commitID} \
    --connection-timeout 600 \
    --git-root-key "legion-root-key" \
    --model-host "" \
    --dynamic-model-prefix "DYNAMIC MODEL"
    """
}

def runRobotTests(tags="") {
    withAWS(credentials: 'kops') {
    	withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
            def tags_list=tags.toString().trim().split(',')
            def robot_tags= []
            def nose_tags = []
            for (item in tags_list) {
                if (item.startsWith('-')) {
                    item = item.replace("-","")
                    robot_tags.add(" -e ${item}")
                    nose_tags.add(" -a !${item}")
                    }
                else if (item?.trim()) {
                    robot_tags.add(" -i ${item}")
                    nose_tags.add(" -a ${item}")
                    }
                }
            env.robot_tags= robot_tags.join(" ")
            env.nose_tags = nose_tags.join(" ")

            sh '''
            cd legion
            ../.venv/bin/pip install -r requirements/base.txt
            ../.venv/bin/pip install -r requirements/test.txt
            ../.venv/bin/python setup.py develop
            cd ..

            cd legion_test
            ../.venv/bin/pip install -r requirements/base.txt
            ../.venv/bin/pip install -r requirements/test.txt
            ../.venv/bin/python setup.py develop

            echo "Starting robot tests"
            cd ../tests/robot
            ../../.venv/bin/pip install yq

            PATH_TO_PROFILES_DIR="${PROFILES_PATH:-../../deploy/profiles}/"
            PATH_TO_PROFILE_FILE="${PATH_TO_PROFILES_DIR}$Profile.yml"
            CLUSTER_NAME=$(yq -r .cluster_name $PATH_TO_PROFILE_FILE)
            CLUSTER_STATE_STORE=$(yq -r .state_store $PATH_TO_PROFILE_FILE)
            echo "Loading kubectl config from $CLUSTER_STATE_STORE for cluster $CLUSTER_NAME"

            kops export kubecfg --name $CLUSTER_NAME --state $CLUSTER_STATE_STORE
            PATH=../../.venv/bin:$PATH DISPLAY=:99 \
            PROFILE=$Profile LEGION_VERSION=$LegionVersion \
            ../../.venv/bin/python3 -m robot.run --variable PATH_TO_PROFILES_DIR:$PATH_TO_PROFILES_DIR $robot_tags *.robot || true

            echo "Starting python tests"
            cd ../python

            kops export kubecfg --name $CLUSTER_NAME --state $CLUSTER_STATE_STORE
            PROFILE=$Profile PATH_TO_PROFILES_DIR=$PATH_TO_PROFILES_DIR LEGION_VERSION=$LegionVersion \
            ../../.venv/bin/nosetests $nose_tags --with-xunit || true
            '''
            step([
                $class : 'RobotPublisher',
                outputPath : 'tests/robot/',
                outputFileName : "*.xml",
                disableArchiveOutput : false,
                passThreshold : 100,
                unstableThreshold: 95.0,
                onlyCritical : true,
                otherFiles : "*.png",
            ])
        }
	}
    junit 'tests/python/nosetests.xml'
}

def deployLegionEnclave() {
    dir('deploy/ansible'){
        withCredentials([
            file(credentialsId: "vault-${params.Profile}", variable: 'vault')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    if (params.PublicRelease){
                        ansiblePlaybook(
                            playbook: 'deploy-legion-enclave.yml',
                            extras: '--vault-password-file=${vault} \
                                     --extra-vars "profile=${Profile} \
                                     legion_version=${LegionVersion} \
                                     pypi_repo=${PypiRepo} \
                                     docker_repo=${DockerRepo}" \
                                     enclave_name=${EnclaveName}"',
                            colorized: true
                         )
                    } else {
                        ansiblePlaybook(
                            playbook: 'deploy-legion-enclave.yml',
                            extras: '--vault-password-file=${vault} \
                                     --extra-vars "profile=${Profile} \
                                     legion_version=${LegionVersion}" \
                                     enclave_name=${EnclaveName}" ',
                            colorized: true
                        )
                    }
                }
            }
        }
    }
}

def terminateLegionEnclave() {
    dir('deploy/ansible'){
        withCredentials([
            file(credentialsId: "vault-${params.Profile}", variable: 'vault')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    ansiblePlaybook(
                        playbook: 'terminate-legion-enclave.yml',
                            extras: '--vault-password-file=${vault} \
                                    --extra-vars "profile=${Profile} \
                                    enclave_name=${EnclaveName}"',
                            colorized: true
                    )
                }
            }
        }
    }
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
    def arguments = ""
    if (params.Skip_kops != null) {
        arguments = arguments + "\nskip kops *${params.Skip_kops}*"
    }
    if (params.LegionVersion) {
        arguments = arguments + "\nversion *${params.LegionVersion}*"
    }

    if (params.DeployLegion != null && params.CreateJenkinsTests != null && params.UseRegressionTests != null) {
        arguments = arguments + "\nDeploy *${params.DeployLegion}*, Create Jenkins tests *${params.CreateJenkinsTests}*, Use regression tests *${params.UseRegressionTests}*"
    }
    if (params.EnclaveName) {
        arguments = arguments + "\nEnclave *${params.EnclaveName}*"
    }
    def summary = """\
    @here Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}* (previous: ${previousBuildResult})
    branch *${GitBranch}*
    profile *<https://${env.Profile}|${env.Profile}>*
    ${arguments}
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
