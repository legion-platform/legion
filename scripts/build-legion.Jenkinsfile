import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

def chartNames = null

def buildTestBareModel(modelId, modelVersion, versionNumber) {
    sh """
        cd legion/tests/e2e/models
        rm -rf robot.model || true
        mkdir /app || true
        python3 simple.py --id "${modelId}" --version "${modelVersion}"

        legionctl --verbose build \
                  --docker-image-tag "legion/test-bare-model-api-model-${versionNumber}:${Globals.buildVersion}" \
                  --model-file robot.model
    """
}

pipeline {
    agent { label 'ec2builder'}

    options{
            buildDiscarder(logRotator(numToKeepStr: '35', artifactNumToKeepStr: '35'))
        }
    environment {
            /// Input parameters
            //Enable docker cache parameter
            param_enable_docker_cache = "${params.EnableDockerCache}"
            //Build major version release and optionally push it to public repositories
            param_stable_release = "${params.StableRelease}"
            //Release version to tag all artifacts to
            param_release_version = "${params.ReleaseVersion}"
            //Git Branch to build package from
            param_git_branch = "${params.GitBranch}"
             //Legion Infra repo url (for pipeline methods import)
            param_legion_infra_repo = "${params.LegionInfraRepo}"
            //Legion repo version tag (tag or branch name)
            param_legion_infra_version_tag = "${params.LegionInfraVersionTag}"
            //Push release git tag
            param_push_git_tag = "${params.PushGitTag}"
            //Rewrite git tag i exists
            param_force_tag_push = "${params.ForceTagPush}"
            //Push release to master bransh
            param_update_master = "${params.UpdateMaster}"
            //Upload legion python package to pypi
            param_upload_legion_package = "${params.UploadLegionPackage}"
            //Set next releases version explicitly
            param_next_version = "${params.NextVersion}"
            // Update version string
            param_update_version_string = "${params.UpdateVersionString}"
            // Release version to be used as docker cache source
            param_docker_cache_source = "${params.DockerCacheSource}"
            //Artifacts storage parameters
            param_helm_repo_git_url = "${params.HelmRepoGitUrl}"
            param_helm_repo_git_branch = "${params.HelmRepoGitBranch}"
            param_helm_repository = "${params.HelmRepository}"
            param_pypi_repository = "${params.PyPiRepository}"
            param_local_pypi_distribution_target_name = "${params.LocalPyPiDistributionTargetName}"
            param_test_pypi_distribution_target_name = "${params.testPyPiDistributionTargetName}"
            param_public_pypi_distribution_target_name = "${params.PublicPyPiDistributionTargetName}"
            param_pypi_distribution_target_name = "${params.PyPiDistributionTargetName}"
            param_jenkins_plugins_repository_store = "${params.JenkinsPluginsRepositoryStore}"
            param_jenkins_plugins_repository = "${params.JenkinsPluginsRepository}"
            param_docker_registry = "${params.DockerRegistry}"
            param_docker_hub_registry = "${params.DockerHubRegistry}"
            param_git_deploy_key = "${params.GitDeployKey}"
            ///Job parameters
            updateVersionScript = "scripts/update_version_id"
            sharedLibPath = "pipelines/legionPipeline.groovy"
            pathToCharts= "${WORKSPACE}/helms"
    }

    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    sh 'echo RunningOn: $(curl http://checkip.amazonaws.com/)'

                    // import Legion components
                    dir("${WORKSPACE}/legion-aws") {
                        print ("Checkout Legion-infra repo")
                        checkout scm: [$class: 'GitSCM', userRemoteConfigs: [[url: "${env.param_legion_infra_repo}"]], branches: [[name: "refs/tags/${env.param_legion_infra_version_tag}"]]], poll: false

                        print ("Load legion pipeline common library")
                        legion = load "${env.sharedLibPath}"
                    }

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    legion.setBuildMeta(env.updateVersionScript)

                }
            }
        }

        // Set Git Tag in case of stable release
        stage('Set GIT release Tag'){
            steps {
                script {
                    print (env.param_stable_release)
                    if (env.param_stable_release.toBoolean() && env.param_push_git_tag.toBoolean()){
                        legion.setGitReleaseTag()
                    }
                    else {
                        print("Skipping release git tag push")
                    }
                }
            }
        }

        stage("Docker login") {
            steps {
                withCredentials([[
                 $class: 'UsernamePasswordMultiBinding',
                 credentialsId: 'nexus-local-repository',
                 usernameVariable: 'USERNAME',
                 passwordVariable: 'PASSWORD']]) {
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${env.param_docker_registry}"
                }
                script {
                    if (env.param_stable_release.toBoolean()) {
                        withCredentials([[
                        $class: 'UsernamePasswordMultiBinding',
                        credentialsId: 'dockerhub',
                        usernameVariable: 'USERNAME',
                        passwordVariable: 'PASSWORD']]) {
                            sh "docker login -u ${USERNAME} -p ${PASSWORD}"
                        }
                    }
                }
            }
        }

        stage("Build base images") {
            parallel {
                stage("Build toolchains Docker image"){
                    steps {
                        script {
                            legion.buildLegionImage('python-toolchain', '.', 'containers/toolchains/python/Dockerfile')
                            legion.uploadDockerImage('python-toolchain')
                        }
                    }
                }
                stage('Build pipeline Docker agent') {
                    steps {
                        script {
                            legion.buildLegionImage('legion-pipeline-agent', '.', 'containers/pipeline-agent/Dockerfile')
                            legion.uploadDockerImage('legion-pipeline-agent')
                        }
                    }
                }
                // stage("Build Jenkins Legion plugin") {
                //    steps {
                //        script {
                //            docker.image("maven:3.5.3-jdk-8").inside("-v /tmp/.m2:/tmp/.m2 -e HOME=/tmp -u root") {
                //                /// Jenkins plugin which will be used in Jenkins Docker container only
                //                sh """
                //                export JAVA_HOME=\$(readlink -f /usr/bin/java | sed "s:bin/java::")
                //                mvn -f containers/jenkins/legion-jenkins-plugin/pom.xml clean -Dmaven.repo.local=/tmp/.m2/repository
                //                mvn -f containers/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${Globals.buildVersion} -Dmaven.repo.local=///tmp/.m2/repository
                //                mvn -f containers/jenkins/legion-jenkins-plugin/pom.xml install -Dmaven.repo.local=/tmp/.m2/repository
                //                """

                //                archiveArtifacts 'containers/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi'

                //                withCredentials([[
                //                    $class: 'UsernamePasswordMultiBinding',
                //                    credentialsId: 'nexus-local-repository',
                //                    usernameVariable: 'USERNAME',
                //                    passwordVariable: 'PASSWORD']]) {
                //                    sh """
                //                    curl -v -u $USERNAME:$PASSWORD \
                //                    --upload-file containers/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                //                    ${env.param_jenkins_plugins_repository_store}/${Globals.buildVersion}/legion-jenkins-plugin.hpi
                //                    """
                //                    script {
                //                        if (env.param_stable_release.toBoolean()){
                //                            sh """
                //                            curl -v -u $USERNAME:$PASSWORD \
                //                            --upload-file containers/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                //                            ${env.param_jenkins_plugins_repository_store}/latest/legion-jenkins-plugin.hpi
                //                            """
                //                        }
                //                    }
                //                }
                //                sh "rm -rf ${WORKSPACE}/containers/jenkins/legion-jenkins-plugin/*"
                //             }
                //         }
                //     }
                // }
            }
        }
    
        stage("Build Docker images & Run Tests") {
            parallel {
                stage("Build Edge Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-edge', '.', 'containers/edge/Dockerfile')
                        }
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-edi', '.', "containers/edi/Dockerfile")
                        }
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-fluentd', 'containers/fluentd')
                        }
                    }
                }
                stage("Build Jenkins Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-jenkins', "containers/jenkins", "Dockerfile", """--build-arg update_center_url="" --build-arg update_center_experimental_url="${env.param_jenkins_plugins_repository}" --build-arg update_center_download_url="${env.param_jenkins_plugins_repository}" --build-arg legion_plugin_version="${Globals.buildVersion}" """)
                        }
                    }
                }
                stage("Build test models") {
                    steps {
                        script {
                            docker.image("legion/python-toolchain:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root") {
                                buildTestBareModel("demo-abc-model", "1.0", "1")
                                buildTestBareModel("demo-abc-model", "1.1", "2")
                                buildTestBareModel("edi-test-model", "1.2", "3")
                                buildTestBareModel("feedback-test-model", "1.0", "4")
                                buildTestBareModel("command-test-model", "1.0", "5")
                                buildTestBareModel("auth-test-model", "1.0", "6")
                            }
                        }
                    }
                }
                stage('Build docs') {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-u root") {
                                sh """
                                cd /opt/legion
                                make LEGION_VERSION=${Globals.buildVersion} build-docs
                                cp /opt/legion/legion_docs_${Globals.buildVersion}.tar.gz ${WORKSPACE}
                                """

                                archiveArtifacts artifacts: "legion_docs_${Globals.buildVersion}.tar.gz"
                                sh "rm ${WORKSPACE}/legion_docs_${Globals.buildVersion}.tar.gz"
                            }
                        }
                    }
                }
                stage('Run Python code analyzers') {
                    steps {
                        script{
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside() {
                                def statusCode = sh script:'make lint', returnStatus:true

                                if (statusCode != 0) {
                                    currentBuild.result = 'UNSTABLE'
                                }

                                archiveArtifacts 'target/pylint/legion.log'
                                archiveArtifacts 'target/pydocstyle/legion.log'
                                step([
                                    $class                     : 'WarningsPublisher',
                                    parserConfigurations       : [[
                                                                        parserName: 'PYLint',
                                                                        pattern   : 'target/pylint/legion.log'
                                                                ]],
                                    unstableTotalAll           : '0',
                                    usePreviousBuildAsReference: true
                                ])
                            }
                        }
                    }
                }
            }
        }

        stage("Run unittests") {
            steps {
                script {
                    docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root --net host") {
                            sh """
                                CURRENT_DIR="\$(pwd)"
                                cd /opt/legion
                                make SANDBOX_PYTHON_TOOLCHAIN_IMAGE="legion/python-toolchain:${Globals.buildVersion}" \
                                     TEMP_DIRECTORY="\${CURRENT_DIR}" unittests || true
                            """
                            sh 'cp -r /opt/legion/target/coverage.xml /opt/legion/target/nosetests.xml /opt/legion/target/cover ./'
                            junit 'nosetests.xml'
                            cobertura coberturaReportFile: 'coverage.xml'
                            publishHTML (target: [
                              allowMissing: false,
                              alwaysLinkToLastBuild: false,
                              keepAll: true,
                              reportDir: 'cover',
                              reportFiles: 'index.html',
                              reportName: "Test Coverage Report"
                            ])
                            sh 'rm -rf coverage.xml nosetests.xml cover'
                    }
                }
            }
        }

        stage('Upload artifacts'){
            parallel {
                stage("Upload Legion package") {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside() {
                                withCredentials([[
                                $class: 'UsernamePasswordMultiBinding',
                                credentialsId: 'nexus-local-repository',
                                usernameVariable: 'USERNAME',
                                passwordVariable: 'PASSWORD']]) {
                                sh """
                                cat > /tmp/.pypirc << EOL
                                [distutils]
                                index-servers =
                                  ${env.param_local_pypi_distribution_target_name}
                                [${env.param_local_pypi_distribution_target_name}]
                                repository=${env.param_pypi_repository.split('/').dropRight(1).join('/')}/
                                username=${env.USERNAME}
                                password=${env.PASSWORD}
                                EOL
                                """.stripIndent()
                                }
                                sh """
                                cat /tmp/.pypirc
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/sdk/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/cli/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/toolchains/python/dist/legion-*'
                                """

                                if (env.param_stable_release.toBoolean()) {
                                    if (env.param_upload_legion_package.toBoolean()){
                                        withCredentials([[
                                        $class: 'UsernamePasswordMultiBinding',
                                        credentialsId: 'pypi-repository',
                                        usernameVariable: 'USERNAME',
                                        passwordVariable: 'PASSWORD']]) {
                                            sh """
                                            cat > /tmp/.pypirc << EOL
                                            [distutils]
                                            index-servers =
                                              ${env.param_test_pypi_distribution_target_name}
                                            ${env.param_public_pypi_distribution_target_name}
                                            [${env.param_test_pypi_distribution_target_name}]
                                            repository=https://test.pypi.org/legacy/
                                            username=${env.USERNAME}
                                            password=${env.PASSWORD}
                                            [${env.param_public_pypi_distribution_target_name}]
                                            repository=https://upload.pypi.org/legacy/
                                            username=${env.USERNAME}
                                            password=${env.PASSWORD}
                                            EOL
                                            """.stripIndent()
                                        }
                                        sh """
                                        twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/sdk/dist/legion-*'
                                        twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/cli/dist/legion-*'
                                        """
                                    } else {
                                        print("Skipping package upload")
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Package and upload helm charts'){
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root") {
                                legion.uploadHelmCharts(env.pathToCharts)
                            }
                        }
                    }
                }
                stage('Upload Edge Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-edge')
                        }
                    }
                }
                stage('Upload Edi Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-edi')
                        }
                    }
                }
                stage('Upload Fluentd Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-fluentd')
                        }
                    }
                }
                stage('Upload Jenkins Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-jenkins')
                        }
                    }
                }
                stage("Upload test models") {
                    steps {
                        script {
                            legion.uploadDockerImage("test-bare-model-api-model-1")
                            legion.uploadDockerImage("test-bare-model-api-model-2")
                            legion.uploadDockerImage("test-bare-model-api-model-3")
                            legion.uploadDockerImage("test-bare-model-api-model-4")
                            legion.uploadDockerImage("test-bare-model-api-model-5")
                            legion.uploadDockerImage("test-bare-model-api-model-6")
                        }
                    }
                }
            }
        }

        stage("Update Legion version string") {
            steps {
                script {
                    if (env.param_stable_release.toBoolean() && env.param_update_version_string.toBoolean()) {
                        legion.updateVersionString(env.versionFile)
                    }
                    else {
                        print("Skipping version string update")
                    }
                }
            }
        }

        stage('Update Master branch'){
            steps {
                script {
                    if (env.param_update_master.toBoolean()){
                        legion.updateMasterBranch()
                    }
                    else {
                        print("Skipping Master branch update")
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                // import Legion components
                dir("${WORKSPACE}/legion-aws") {
                    print ("Checkout Legion-infra repo")
                    checkout scm: [$class: 'GitSCM', userRemoteConfigs: [[url: "${env.param_legion_infra_repo}"]], branches: [[name: "refs/tags/${env.param_legion_infra_version_tag}"]]], poll: false

                    print ("Load legion pipeline common library")
                    legion = load "${env.sharedLibPath}"
                }
                legion.notifyBuild(currentBuild.currentResult)
            }
            deleteDir()
        }
    }
}
