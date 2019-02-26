def buildDescription(){
   currentBuild.description = "${env.param_profile} ${env.param_git_branch}"
}

def ansibleDebugRunCheck(String debugRun) {
    // Run ansible playbooks and helm charts from sources in workspace and use verbose output for debug purposes
    if (debugRun == "true" ) {
      ansibleHome =  "${WORKSPACE}/deploy/ansible"
      ansibleVerbose = '-vvv'
      helmLocalSrc = 'true'
    } else {
      ansibleHome = env.ansibleHome
      ansibleVerbose = env.ansibleVerbose
      helmLocalSrc = env.helmLocalSrc
    }
}

def createCluster() {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Create cluster') {
                        sh """
                        cd ${ansibleHome} && \
                        ansible-playbook create-cluster.yml \
                        ${ansibleVerbose} \
                        --vault-password-file=${vault} \
                        --extra-vars "profile=${env.param_profile} \
                        legion_version=${env.param_legion_version} \
                        skip_kops=${env.param_skip_kops} \
                        helm_repo=${env.param_helm_repo} \
                        helm_local_src=${helmLocalSrc}" 
                        """
                    }
                }
            }
        }
    }
}

def terminateCluster() {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Terminate cluster') {
                        sh """
                        cd ${ansibleHome} && \
                        ansible-playbook terminate-cluster.yml \
                        ${ansibleVerbose} \
                        --vault-password-file=${vault} \
                        --extra-vars "profile=${env.param_profile} \
                        keep_jenkins_volume=${env.param_keep_jenkins_volume} \
                        helm_local_src=${helmLocalSrc}"
                        """
                    }
                }
            }
        }
    }
}

def deployLegion() {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Deploy Legion') {
                        sh """
                        cd ${ansibleHome} && \
                        ansible-playbook deploy-legion.yml \
                        ${ansibleVerbose} \
                        --vault-password-file=${vault} \
                        --extra-vars "profile=${env.param_profile} \
                        legion_version=${env.param_legion_version}  \
                        pypi_repo=${env.param_pypi_repo} \
                        helm_repo=${env.param_helm_repo} \
                        docker_repo=${env.param_docker_repo} \
                        helm_local_src=${helmLocalSrc}"
                        """
                    }
                }
            }
        }
    }
}

def updateTLSCert() {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Reissue TLS Certificates') {
                        sh """
                        cd ${ansibleHome} && \
                        ansible-playbook update-tls-certificate.yml \
                        ${ansibleVerbose} \
                        --vault-password-file=${vault} \
                        --extra-vars "profile=${env.param_profile} \
                        vault_pass=${vault}"
                        """
                    }
                }
            }
        }
    }
}

def createjenkinsJobs(String commitID) {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/legion-docker-agent:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Create Jenkins jobs') {
                        dir("${WORKSPACE}"){
                            def creds
                            def output = sh(script:"""
                                export PATH_TO_PROFILES_DIR=\"deploy/profiles\"
                                export PATH_TO_PROFILE_FILE=\"\$PATH_TO_PROFILES_DIR/${env.param_profile}.yml\"
                                export CLUSTER_NAME=\"\$(yq -r .cluster_name \$PATH_TO_PROFILE_FILE)\"
                                export CLUSTER_STATE_STORE=\"\$(yq -r .state_store \$PATH_TO_PROFILE_FILE)\"
                                echo \"Loading kubectl config from \$CLUSTER_STATE_STORE for cluster \$CLUSTER_NAME\"
                                export CREDENTIAL_SECRETS=\"${env.param_profile}.yaml\"

                                aws s3 cp \$CLUSTER_STATE_STORE/vault/${env.param_profile} \$CLUSTER_NAME
                                ansible-vault decrypt --vault-password-file=${vault} --output \$CREDENTIAL_SECRETS \$CLUSTER_NAME

                                kops export kubecfg --name \$CLUSTER_NAME --state \$CLUSTER_STATE_STORE

                                export PROFILE=${env.param_profile}

                                echo ----
                                jenkins_dex_client
                                """, returnStdout: true)

                            creds = output.split('----')[1].split('\n')
                            env.jenkins_user = creds[1]
                            env.jenkins_pass = creds[2]
                            env.jenkins_token = creds[3]

                            sh """
                            create_example_jobs \
                            \"https://jenkins.${env.param_profile}\" \
                            ./examples \
                            ./ \
                            \"https://github.com/legion-platform/legion.git\" \
                            ${commitID} \
                            --connection-timeout 600 \
                            --git-root-key \"legion-root-key\" \
                            --model-host "" \
                            --dynamic-model-prefix \"DYNAMIC MODEL\" \
                            --jenkins-user "${jenkins_user}" \
                            --jenkins-password "${jenkins_pass}" \
                            --jenkins-cookies "${jenkins_token}" \
                            """
                        }
                    }
                }
            }
        }
    }
}

def runRobotTests(tags="") {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/legion-docker-agent:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Run Robot tests') {
                        dir("${WORKSPACE}"){
                            def nose_report = 0
                            def robot_report = 0
                            def tags_list = tags.toString().trim().split(',')
                            def robot_tags = []
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
                            sh """
                            echo "Starting robot tests"
                            cd tests/robot
                            rm -f *.xml

                            PATH_TO_PROFILES_DIR=\"../../deploy/profiles\"
                            PATH_TO_PROFILE_FILE=\"\$PATH_TO_PROFILES_DIR/${env.param_profile}.yml\"
                            PATH_TO_COOKIES=\"\$PATH_TO_PROFILES_DIR/cookies.dat\"

                            export CLUSTER_NAME=\"\$(yq -r .cluster_name \$PATH_TO_PROFILE_FILE)\"
                            export CLUSTER_STATE_STORE=\"\$(yq -r .state_store \$PATH_TO_PROFILE_FILE)\"
                            echo \"Loading kubectl config from \$CLUSTER_STATE_STORE for cluster \$CLUSTER_NAME\"
                            export CREDENTIAL_SECRETS=\"${env.param_profile}.yaml\"

                            aws s3 cp \$CLUSTER_STATE_STORE/vault/${env.param_profile} \$CLUSTER_NAME
                            ansible-vault decrypt --vault-password-file=${vault} --output \$CREDENTIAL_SECRETS \$CLUSTER_NAME

                            kops export kubecfg --name \$CLUSTER_NAME --state \$CLUSTER_STATE_STORE
                            
                            # Start Xvfb server in background
                            Xvfb :99 -ac &

                            # Get Auth cookies
                            DISPLAY=:99 \
                            PROFILE=${env.param_profile} LEGION_VERSION=${env.param_legion_version} \
                            jenkins_dex_client --path-to-profiles \$PATH_TO_PROFILES_DIR > \$PATH_TO_COOKIES

                            # Run Robot tests
                            DISPLAY=:99 \
                            PROFILE=${env.param_profile} LEGION_VERSION=${env.param_legion_version} PATH_TO_COOKIES=\$PATH_TO_COOKIES \
                            pabot --verbose --processes 6 --variable PATH_TO_PROFILES_DIR:\$PATH_TO_PROFILES_DIR --listener legion_test.process_reporter ${env.robot_tags} --outputdir . tests/**/*.robot || true

                            echo \"Starting python tests\"
                            cd ../python
                            export CREDENTIAL_SECRETS=\"${env.param_profile}.yaml\"
                            aws s3 cp \$CLUSTER_STATE_STORE/vault/${env.param_profile} \$CLUSTER_NAME
                            ansible-vault decrypt --vault-password-file=${vault} --output \$CREDENTIAL_SECRETS \$CLUSTER_NAME

                            PROFILE=${env.param_profile} PATH_TO_PROFILES_DIR=\$PATH_TO_PROFILES_DIR LEGION_VERSION=${env.param_legion_version} \
                            nosetests ${env.nose_tags} --with-xunit --logging-level DEBUG -v || true
                            """

                            robot_report = sh(script: 'find tests/robot/ -name "*.xml" | wc -l', returnStdout: true)
                            nose_report = sh(script: 'cat tests/python/nosetests.xml | wc -l', returnStdout: true)

                            if (robot_report.toInteger() > 0) {
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
                            else {
                                echo "No '*.xml' files for generating robot report"
                            }

                            if (nose_report.toInteger() > 1) {
                                junit 'tests/python/nosetests.xml'
                            }
                            else {
                                echo "No ''*.xml' files for generating nosetests report"
                            }

                            if (!(nose_report.toInteger() > 1 && robot_report.toInteger() > 0) && !tags) {
                                echo "All tests were run but no reports found. Marking build as UNSTABLE"
                                currentBuild.result = 'UNSTABLE'
                            }
                            if (!(nose_report.toInteger() > 1 || robot_report.toInteger() > 0) && tags) {
                                echo "No tests were run during this build. Marking build as UNSTABLE"
                                currentBuild.result = 'UNSTABLE'
                            }     

                            sh """
                            # Cleanup temp files
                            rm -rf tests/python/__pycache__
                            rm -rf tests/robot/__pycache__
                            rm -rf tests/robot/pabot_results
                            """         
                        }
                    }
                }
            }
        }
    }
}

def deployLegionEnclave() {
    withCredentials([
        file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Deploy Legion') {
                        sh """
                        cd ${ansibleHome} && \
                        ansible-playbook deploy-legion.yml \
                        ${ansibleVerbose} \
                        --vault-password-file=${vault} \
                        --extra-vars "profile=${env.param_profile} \
                        legion_version=${env.param_legion_version} \
                        pypi_repo=${env.param_pypi_repo} \
                        docker_repo=${env.param_docker_repo} \
                        helm_repo=${env.param_helm_repo} \
                        enclave_name=${env.param_enclave_name} \
                        helm_local_src=${helmLocalSrc}"
                        """
                    }
                }
            }
        }
    }
}

def terminateLegionEnclave() {
    dir('deploy/ansible'){
        withCredentials([
            file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
            withAWS(credentials: 'kops') {
                wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                    docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                        stage('Terminate Legion Enclave') {
                            sh """
                            cd ${ansibleHome} && \
                            ansible-playbook terminate-legion-enclave.yml \
                            ${ansibleVerbose} \
                            --vault-password-file=${vault} \
                            --extra-vars "profile=${env.param_profile} \
                            enclave_name=${env.param_enclave_name}"
                            """
                        }
                    }
                }
            }
        }
    }
}


def cleanupClusterSg(String cleanupContainerVersion) {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${cleanupContainerVersion}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    stage('Cleanup Cluster SG') {
                        sh """
                        cd ${ansibleHome} && \
                        ansible-playbook cleanup-cluster-sg.yml \
                        ${ansibleVerbose} \
                        --vault-password-file=${vault} \
                        --extra-vars "profile=${env.param_profile}" 
                        """
                    }
                }
            }
        }
    }
}

def authorizeJenkinsAgent() {
    withCredentials([
    file(credentialsId: "vault-${env.param_profile}", variable: 'vault')]) {
        withAWS(credentials: 'kops') {
            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                docker.image("${env.param_docker_repo}/k8s-ansible:${env.param_legion_version}").inside("-e HOME=/opt/legion/deploy -v ${WORKSPACE}/deploy/profiles:/opt/legion/deploy/profiles -u root") {
                    sh """
                    cd ${ansibleHome} && \
                    ansible-playbook authorize-jenkins-agent.yml \
                    ${ansibleVerbose} \
                    --vault-password-file=${vault} \
                    --extra-vars "profile=${env.param_profile}" 
                    """
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

    def masterOrDevelopBuild = env.param_git_branch == 'origin/develop' || env.param_git_branch == 'origin/master'

    print("NOW SUCCESSFUL: ${currentBuildResultSuccessful}, PREV SUCCESSFUL: ${previousBuildResultSuccessful}, MASTER OR DEV: ${masterOrDevelopBuild}")

    // Default values
    def colorCode = '#FF0000'
    def arguments = ""
    if (env.param_legion_version) {
        arguments = arguments + "\nversion *${env.param_legion_version}*"
    }
    def mailSubject = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'"
    def summary = """\
    @here Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}* (previous: ${previousBuildResult}) \n
    Branch: *${GitBranch}* \n
    Profile: *<https://${env.param_profile}|${env.param_profile}>* \n
    Arguments: ${arguments} \n
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

    /// Notify everyone about each Nightly build
    if ("${env.JOB_NAME}".contains("Legion_CI_Infra")) {
        slackSend (color: colorCode, message: summary)
        emailext (
            subject: mailSubject,
            body: summary,
            to: "${env.DevTeamMailList}"
        )
    /// Notify committers about CI builds
    } else if ("${env.JOB_NAME}".contains("Legion_CI")) {
        emailext (
            subject: mailSubject,
            body: summary,
            recipientProviders: [[$class: 'DevelopersRecipientProvider']]
        )
    /// Notify everyone about failed Master or Develop branch builds
    } else if (!currentBuildResultSuccessful && masterOrDevelopBuild) {
        slackSend (color: colorCode, message: summary)
        emailext (
            subject: mailSubject,
            body: summary,
            to: "${env.DevTeamMailList}"
        )
    }

}

def buildTestBareModel(modelId, modelVersion, versionNumber) {
    sh """
        cd tests/models
        rm -rf robot.model || true
        mkdir /app || true
        python3 simple.py --id "${modelId}" --version "${modelVersion}"

        legionctl --verbose build \
                  --docker-image-tag "legion/test-bare-model-api-model-${versionNumber}:${Globals.buildVersion}" \
                  --model-file robot.model
    """
}

def pullDockerCache(base_images=[], legion_image=null){
    if (base_images){
        for (image in base_images) {
            sh "docker pull ${image} || true"
        }
    }
    if (legion_image){
        sh "docker pull ${env.param_docker_registry}/${legion_image}:${env.param_docker_cache_source} || true"
    }
}
def uploadDockerImage(String imageName) {
    if (env.param_stable_release) {
        sh """
        # Push stable image to local registry
        docker tag legion/${imageName}:${Globals.buildVersion} ${env.param_docker_registry}/${imageName}:${Globals.buildVersion}
        docker tag legion/${imageName}:${Globals.buildVersion} ${env.param_docker_registry}/${imageName}:latest
        docker push ${env.param_docker_registry}/${imageName}:${Globals.buildVersion}
        docker push ${env.param_docker_registry}/${imageName}:latest
        # Push stable image to DockerHub
        docker tag legion/${imageName}:${Globals.buildVersion} ${env.param_docker_hub_registry}/${imageName}:${Globals.buildVersion}
        docker tag legion/${imageName}:${Globals.buildVersion} ${env.param_docker_hub_registry}/${imageName}:latest
        docker push ${env.param_docker_hub_registry}/${imageName}:${Globals.buildVersion}
        docker push ${env.param_docker_hub_registry}/${imageName}:latest
        """
    } else {
        sh """
        docker tag legion/${imageName}:${Globals.buildVersion} ${env.param_docker_registry}/${imageName}:${Globals.buildVersion}
        docker push ${env.param_docker_registry}/${imageName}:${Globals.buildVersion}
        """
    }
}

return this
