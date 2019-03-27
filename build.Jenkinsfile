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
        cd tests/models
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
            param_pypi_repository = "${params.PyPiRepository}"
            param_local_pypi_distribution_target_name = "${params.LocalPyPiDistributionTargetName}"
            param_test_pypi_distribution_target_name = "${params.testPyPiDistributionTargetName}"
            param_public_pypi_distribution_target_name = "${params.PublicPyPiDistributionTargetName}"
            param_pypi_distribution_target_name = "${params.PyPiDistributionTargetName}"
            param_docker_registry = "${params.DockerRegistry}"
            param_docker_hub_registry = "${params.DockerHubRegistry}"
            param_git_deploy_key = "${params.GitDeployKey}"
            ///Job parameters
            versionFile = "legion/legion/version.py"
            sharedLibPath = "legion-aws/pipelines/legionPipeline.groovy"
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
                        checkout scm: [$class: 'GitSCM', userRemoteConfigs: [[url: "${env.param_legion_infra_repo}"]], branches: [[name: "refs/tags/${env.param_legion_infra_version_tag}"]]], poll: false
                        legion = load "${env.sharedLibPath}"
                    }

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    legion.setBuildMeta(env.versionFile)

                }
            }
        }

        // Set Git Tag in case of stable release
        stage('Set GIT release Tag'){
            steps {
                script {
                    legion.setGitReleaseTag()
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
                    if (env.param_stable_release) {
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

        stage('Build pipeline Docker agent with Legion') {
            steps {
                script {
                    legion.buildLegionImage('legion-pipeline-agent', '.', 'containers/pipeline-agent/Dockerfile')
                    legion.uploadDockerImage('legion-pipeline-agent')
                }
            }
        }
        
        stage("Build Base python image") {
            steps {
                script {
                    legion.buildLegionImage('base-python-image', 'containers/base-python-image', 'containers/base-python-image/Dockerfile')
                    legion.uploadDockerImage('base-python-image')
                }
            }
        }

        stage("Build toolchains Docker image"){
            steps {
                script {
                    legion.buildLegionImage('python-toolchain', 'containers/toolchains/python', 'containers/toolchains/python/Dockerfile')
                }
            }
        }

        stage('Run Python code analyzers') {
            steps {
                script{
                    docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside() {
                        sh '''
                        bash analyze_code.sh
                        '''

                        archiveArtifacts 'legion-pylint.log'
                        step([
                            $class                     : 'WarningsPublisher',
                            parserConfigurations       : [[
                                                                parserName: 'PYLint',
                                                                pattern   : 'legion-pylint.log'
                                                        ]], 
                            unstableTotalAll           : '0',
                            usePreviousBuildAsReference: true
                        ])
                    }
                }
            }
        }

        stage('Run tests and upload artifacts'){
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
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion_test/dist/legion_test-*'
                                """

                                if (env.param_stable_release) {
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
                                        twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/dist/legion-*'
                                        """
                                    } else {
                                        print("Skipping package upload")
                                    }
                                }
                            }
                        }
                    }
                }

                stage('Build docs') {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside() {
                                sh """
                                cd legion/docs
                                sphinx-apidoc -f --private -o source/ ../legion/ -V '${Globals.buildVersion}'
                                sed -i 's/\'1.0\'/\'${Globals.buildVersion}\'/' source/conf.py
                                make html
                                find build/html -type f -name '*.html' | xargs sed -i -r 's/href=\"(.*)\\.md\"/href=\"\\1.html\"/'
                                cd ../../
                                """

                                sh "tar -czf legion_docs_${Globals.buildVersion}.tar.gz legion/docs/build/html/"
                                archiveArtifacts artifacts: "legion_docs_${Globals.buildVersion}.tar.gz"
                            }
                        }
                    }
                }

                stage("Run Python tests") {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root --net host") {
                                sh """
                                export TEMP_DIRECTORY="\$(pwd)"
                                cd /src/legion
                                VERBOSE=true \
                                DEBUG=true \
                                BASE_IMAGE_VERSION="${Globals.buildVersion}" \
                                SANDBOX_PYTHON_TOOLCHAIN_IMAGE="legion/python-toolchain:${Globals.buildVersion}" \
                                    nosetests --processes=10 \
                                    --process-timeout=600 \
                                    --with-coverage \
                                    --cover-package legion \
                                    --with-xunitmp \
                                    --cover-xml \
                                    --cover-html \
                                    --logging-level DEBUG \
                                    -v || true

                                cd -
                                cp /src/legion/nosetests.xml legion/nosetests.xml
                                cp /src/legion/coverage.xml legion/coverage.xml
                                cp -r /src/legion/cover legion/cover
                                """

                                junit 'legion/nosetests.xml'
                                cobertura coberturaReportFile: 'legion/coverage.xml'
                                publishHTML (target: [
                                    allowMissing: false,
                                    alwaysLinkToLastBuild: false,
                                    keepAll: true,
                                    reportDir: 'legion/cover',
                                    reportFiles: 'index.html',
                                    reportName: "Test Coverage Report"
                                ])

                                sh """
                                    rm -rf legion/nosetests.xml
                                    rm -rf legion/coverage.xml
                                    rm -rf legion/cover
                                """
                            }
                        }
                    }
                }
            }
        }

        stage("Build Docker images & Upload Helm charts") {
            parallel {
                stage("Build Edge Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-edge', 'containers/edge', 'containers/edge/Dockerfile')
                        }
                    }
                }
                stage("Build Jenkins Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-jenkins', "containers/jenkins", "containers/jenkins/Dockerfile", """--build-arg update_center_url="" --build-arg update_center_experimental_url="${env.param_jenkins_plugins_repository}" --build-arg update_center_download_url="${env.param_jenkins_plugins_repository}" --build-arg legion_plugin_version="${Globals.buildVersion}" """)
                        }
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-edi', "containers/edi", 'containers/edi/Dockerfile')
                        }
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-fluentd', 'containers/fluentd', 'containers/fluentd/Dockerfile')
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

                stage("Run Python tests") {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root --net host") {
                                sh """
                                export TEMP_DIRECTORY="\$(pwd)"
                                cd /src/legion
                                VERBOSE=true \
                                DEBUG=true \
                                BASE_IMAGE_VERSION="${Globals.buildVersion}" \
                                SANDBOX_PYTHON_TOOLCHAIN_IMAGE="legion/python-toolchain:${Globals.buildVersion}" \
                                    nosetests --processes=10 \
                                    --process-timeout=600 \
                                    --with-coverage \
                                    --cover-package legion \
                                    --with-xunitmp \
                                    --cover-xml \
                                    --cover-html \
                                    --logging-level DEBUG \
                                    -v || true

                                cd -
                                cp /src/legion/nosetests.xml legion/nosetests.xml
                                cp /src/legion/coverage.xml legion/coverage.xml
                                cp -r /src/legion/cover legion/cover
                                """

                                junit 'legion/nosetests.xml'
                                cobertura coberturaReportFile: 'legion/coverage.xml'
                                publishHTML (target: [
                                  allowMissing: false,
                                  alwaysLinkToLastBuild: false,
                                  keepAll: true,
                                  reportDir: 'legion/cover',
                                  reportFiles: 'index.html',
                                  reportName: "Test Coverage Report"
                                ])

                                sh """
                                    rm -rf legion/nosetests.xml
                                    rm -rf legion/coverage.xml
                                    rm -rf legion/cover
                                """
                            }
                        }
                    }
                }

            }
        }

        stage("Push Docker Images & Helm charts") {
            parallel {
                stage('Upload Edge Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-edge')
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

                stage('Package and upload helm charts'){
                    steps {
                        script {
                            legion.uploadHelmCharts()
                        }
                    }
                }
            }
        }

        stage("Update Legion version string") {
            steps {
                script {
                    if (env.param_stable_release && env.param_update_version_string.toBoolean()) {
                        legion.updateVersionString(versionFile)
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
                dir("${WORKSPACE}/legion-aws") {
                    checkout scm: [$class: 'GitSCM', userRemoteConfigs: [[url: "${env.param_legion_infra_repo}"]], branches: [[name: "refs/tags/${env.param_legion_infra_version_tag}"]]], poll: false
                    legion = load "${env.sharedLibPath}"
                }
                legion.notifyBuild(currentBuild.currentResult)
            }
            deleteDir()
        }
    }
}
