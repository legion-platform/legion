import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

def chartNames = null

pipeline {
    agent { label 'ec2orchestrator-808'}

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
            ///Job parameters
            infraBuildWorkspace = "${WORKSPACE}/k8s/k8s-infra"
            sharedLibPath = "deploy/legionPipeline.groovy"
    }

    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    legion = load "${env.sharedLibPath}"
                    Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                    Globals.rootCommit = Globals.rootCommit.trim()
                    println("Root commit: " + Globals.rootCommit)

                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerCacheArg = (env.param_enable_docker_cache.toBoolean()) ? '' : '--no-cache'
                    println("Docker cache args: " + Globals.dockerCacheArg)

                    wrap([$class: 'BuildUser']) {
                        BUILD_USER = binding.hasVariable('BUILD_USER') ? '${BUILD_USER}' : "null"
                    }

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user='${BUILD_USER}' --label build_date=${buildDate}"
                    println("Docker labels: " + Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (env.param_stable_release) {
                        if (env.param_release_version ) {
                            Globals.buildVersion = sh returnStdout: true, script: "python3.6 tools/update_version_id --build-version=${env.param_release_version} legion/legion/version.py '${BUILD_USER}'"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py '${BUILD_USER}'"
                    }

                    Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                    env.BuildVersion = Globals.buildVersion

                    currentBuild.description = "${Globals.buildVersion} ${env.param_git_branch}"
                    print("Build version " + Globals.buildVersion)
                    print('Building shared artifact')
                    envFile = 'file.env'
                    sh """
                    rm -f $envFile
                    touch $envFile
                    echo "LEGION_VERSION=${Globals.buildVersion}" >> $envFile
                    """
                    archiveArtifacts envFile
                    sh "rm -f $envFile"
                }
            }
        }

        // Set Git Tag in case of stable release
        stage('Set GIT release Tag'){
            steps {
                script {
                    if (env.param_stable_release) {
                        if (env.param_push_git_tag.toBoolean()){
                            print('Set Release tag')
                            sh """
                            echo ${env.param_push_git_tag}
                            if [ `git tag |grep -x ${env.param_release_version}` ]; then
                                if [ ${env.param_force_tag_push} = "true" ]; then
                                    echo 'Removing existing git tag'
                                    git tag -d ${env.param_release_version}
                                    git push origin :refs/tags/${env.param_release_version}
                                else
                                    echo 'Specified tag already exists!'
                                    exit 1
                                fi
                            fi
                            git tag ${env.param_release_version}
                            git push origin ${env.param_release_version}
                            """
                        } else {
                            print("Skipping release git tag push")
                        }
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
            }
        }
        stage('Build Agent Docker Image') {
            steps {
                script {
                    legion.pullDockerCache(['python:3.6'],'legion-docker-agent')
                    sh "docker build ${Globals.dockerCacheArg} --cache-from=${env.param_docker_registry}/legion-docker-agent:${env.param_docker_cache_source} -t legion/legion-docker-agent:${Globals.buildVersion} -f pipeline.Dockerfile ."
                    legion.uploadDockerImage('legion-docker-agent')
                }
            }
        }

        stage('Build dependencies') {
            parallel {
                stage('Build Jenkins plugin') {
                    steps {
                        script{
                            docker.image("maven:3.5.3-jdk-8").inside("-v /tmp/.m2:/tmp/.m2 -e HOME=/tmp -u root") {
                                /// Jenkins plugin which will be used in Jenkins Docker container only
                                sh """
                                export JAVA_HOME=\$(readlink -f /usr/bin/java | sed "s:bin/java::")
                                mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml clean -Dmaven.repo.local=/tmp/.m2/repository
                                mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${Globals.buildVersion} -Dmaven.repo.local=/tmp/.m2/repository
                                mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml install -Dmaven.repo.local=/tmp/.m2/repository
                                """

                                archiveArtifacts 'k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi'

                                withCredentials([[
                                    $class: 'UsernamePasswordMultiBinding',
                                    credentialsId: 'nexus-local-repository',
                                    usernameVariable: 'USERNAME',
                                    passwordVariable: 'PASSWORD']]) {
                                    sh """
                                    curl -v -u $USERNAME:$PASSWORD \
                                    --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                                    ${env.param_jenkins_plugins_repository_store}/${Globals.buildVersion}/legion-jenkins-plugin.hpi
                                    """
                                    script {
                                        if (env.param_stable_release){
                                            sh """
                                            curl -v -u $USERNAME:$PASSWORD \
                                            --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                                            ${env.param_jenkins_plugins_repository_store}/latest/legion-jenkins-plugin.hpi
                                            """
                                        }
                                    }
                                }
                                sh "rm -rf ${WORKSPACE}/k8s/jenkins/legion-jenkins-plugin/*"
                            }
                        }
                    }
                }

                stage('Run Python code analyzers') {
                    steps {
                        script{
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
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
                stage("Upload Legion package") {
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
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
"""
                                }
                                sh """
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion_test/dist/legion_test-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion_airflow/dist/legion_airflow-*'
                                """

                                if (env.param_stable_release) {
                                    stage('Upload Legion package to pypi.org'){
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
"""
                                            }
                                            sh """
                                            twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/dist/legion-${Globals.buildVersion}.*'
                                            """
                                        } else {
                                            print("Skipping package upload")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } 
        }

        stage('Build docs') {
            steps {
                script {
                    docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
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
        
        stage("Build and Upload Base Docker Image & Ansible image ") {
            parallel {
                stage ("Build Base python image") {
                    steps {
                        script {
                            legion.pullDockerCache(['ubuntu:16.04'], 'base-python-image')
                            sh """
                            cd base-python-image
                            docker build ${Globals.dockerCacheArg} --cache-from=ubuntu:16.04 --cache-from=${env.param_docker_registry}/base-python-image:${env.param_docker_cache_source} -t "legion/base-python-image:${Globals.buildVersion}" ${Globals.dockerLabels} .
                            """
                            legion.uploadDockerImage('base-python-image')
                        }
                    }
                }
                // Build ansible aside from other images because it uses root as context
                stage("Build Ansible Docker image") {
                    steps {
                        script {
                            legion.pullDockerCache(['ubuntu:18.04'], 'k8s-ansible')
                            sh "docker build ${Globals.dockerCacheArg} --cache-from=ubuntu:18.04 --cache-from=${env.param_docker_registry}/k8s-ansible:${env.param_docker_cache_source} -t legion/k8s-ansible:${Globals.buildVersion} ${Globals.dockerLabels}  -f k8s/ansible/Dockerfile ."
                        }
                    }
                }
            }
        }
        stage("Build toolchains Docker image"){
            steps {
                script {
                    /// don't pull base image because it's been created in current run
                    legion.pullDockerCache([], 'python-toolchain')
                    sh """
                    cd k8s/toolchains/python
                    docker build ${Globals.dockerCacheArg} --cache-from=${env.param_docker_registry}/legion-docker-agent:${env.param_docker_cache_source} --cache-from=${env.param_docker_registry}/legion-docker-agent:${env.param_docker_cache_source} --cache-from=${env.param_docker_registry}/python-toolchain:${env.param_docker_cache_source} --build-arg version="${Globals.buildVersion}" -t legion/python-toolchain:${Globals.buildVersion} ${Globals.dockerLabels} .
                    """
                }
            }
        }
        stage("Build Docker images & Run Tests") {
            parallel {
                stage("Build Edge Docker image") {
                    steps {
                        script {
                            legion.pullDockerCache(['openresty/openresty:1.13.6.2-bionic'], 'k8s-edge')
                            sh """
                            cd k8s/edge
                            docker build ${Globals.dockerCacheArg} --cache-from=openresty/openresty:1.13.6.2-bionic --cache-from=${env.param_docker_registry}/k8s-edge:${env.param_docker_cache_source} --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edge:${Globals.buildVersion} ${Globals.dockerLabels} .
                            """
                        }
                    }
                }
                stage("Build Jenkins Docker image") {
                    steps {
                        script {
                            legion.pullDockerCache(['jenkins/jenkins:2.121.3'], 'k8s-edge')
                            sh """
                            cd k8s/jenkins
                            docker build ${Globals.dockerCacheArg} --cache-from=jenkins/jenkins:2.121.3 --cache-from=${env.param_docker_registry}/k8s-jenkins:${env.param_docker_cache_source} --build-arg update_center_url="" --build-arg update_center_experimental_url="${env.param_jenkins_plugins_repository}" --build-arg update_center_download_url="${env.param_jenkins_plugins_repository}" --build-arg legion_plugin_version="${Globals.buildVersion}" -t legion/k8s-jenkins:${Globals.buildVersion} ${Globals.dockerLabels} .
                            """
                        }
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        script {
                            legion.pullDockerCache([], 'k8s-edi')
                            sh """
                            cd k8s/edi
                            docker build ${Globals.dockerCacheArg} --cache-from=legion/base-python-image:${Globals.buildVersion} --cache-from=${env.param_docker_registry}/k8s-edi:${env.param_docker_cache_source} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edi:${Globals.buildVersion} ${Globals.dockerLabels} .
                            """
                        }
                    }
                }
                stage("Build Airflow Docker image") {
                    steps {
                        script {
                            legion.pullDockerCache([], 'k8s-airflow')
                            sh """
                            cd k8s/airflow
                            docker build ${Globals.dockerCacheArg} --cache-from=legion/base-python-image:${Globals.buildVersion} --cache-from=${env.param_docker_registry}/k8s-airflow:${env.param_docker_cache_source} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-airflow:${Globals.buildVersion} ${Globals.dockerLabels} .
                            """
                        }
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        script {
                            legion.pullDockerCache(['k8s.gcr.io/fluentd-elasticsearch:v2.0.4'], 'k8s-fluentd')
                            sh """
                            cd k8s/fluentd
                            docker build ${Globals.dockerCacheArg} --cache-from=k8s.gcr.io/fluentd-elasticsearch:v2.0.4 --cache-from=${env.param_docker_registry}/k8s-fluentd:${env.param_docker_cache_source} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-fluentd:${Globals.buildVersion} ${Globals.dockerLabels} .
                            """
                        }
                    }
                }
                stage("Build test models") {
                    steps {
                        script {
                            docker.image("legion/python-toolchain:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root") {
                                legion.buildTestBareModel("demo-abc-model", "1.0", "1")
                                legion.buildTestBareModel("demo-abc-model", "1.1", "2")
                                legion.buildTestBareModel("edi-test-model", "1.2", "3")
                                legion.buildTestBareModel("feedback-test-model", "1.0", "4")
                                legion.buildTestBareModel("command-test-model", "1.0", "5")
                                legion.buildTestBareModel("auth-test-model", "1.0", "6")
                            }
                        }
                    }
                }
                /// Infra images which are used during cluster creation
                stage('Build kube-fluentd') {
                    steps {
                        script {
                            dir("${env.infraBuildWorkspace}/kube-fluentd") {
                                legion.pullDockerCache(['fluent/fluentd-kubernetes-daemonset:v1.2-debian-syslog'], 'k8s-kube-fluentd')
                                sh "docker build ${Globals.dockerCacheArg} --cache-from=fluent/fluentd-kubernetes-daemonset:v1.2-debian-syslog --cache-from=${env.param_docker_registry}/k8s-kube-fluentd:${env.param_docker_cache_source} -t legion/k8s-kube-fluentd:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile ."
                            }
                        }
                    }
                }
                stage('Build kube-elb-security') {
                    steps {
                        script {
                            dir("${env.infraBuildWorkspace}/kube-elb-security") {
                                legion.pullDockerCache(['alpine:3.8', 'golang:1.10-alpine'], 'kube-elb-security')
                                sh "docker build ${Globals.dockerCacheArg} --cache-from=alpine:3.8 --cache-from=golang:1.10-alpine --cache-from=${env.param_docker_registry}/k8s-kube-elb-security:${env.param_docker_cache_source} -t legion/k8s-kube-elb-security:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile ."
                            }
                        }
                    }
                }
                stage('Build oauth2-proxy') {
                    steps {
                        script {
                            dir("${env.infraBuildWorkspace}/oauth2-proxy") {
                                legion.pullDockerCache(['alpine:3.8', 'golang:1.10-alpine'], 'k8s-oauth2-proxy')
                                sh "docker build ${Globals.dockerCacheArg} --cache-from=alpine:3.8 --cache-from=golang:1.10-alpine --cache-from=${env.param_docker_registry}/k8s-oauth2-proxy:${env.param_docker_cache_source} -t legion/k8s-oauth2-proxy:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile ."
                            }
                        }
                    }
                }
                stage("Run Python tests") {
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root") {
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
                                    --cover-html \
                                    --logging-level DEBUG \
                                    -v || true

                                cd -
                                cp /src/legion/nosetests.xml legion/nosetests.xml
                                tar -czf legion/legion_coverage_${Globals.buildVersion}.tar.gz /src/legion/cover
                                """
                                /// Parse nose tests results
                                junit 'legion/nosetests.xml'

                                archiveArtifacts artifacts: "legion/legion_coverage_${Globals.buildVersion}.tar.gz"
                            }
                        }
                    }
                }
            }
        }

        stage("Push Docker Images & Helm charts") {
            parallel {
                stage('Package and upload helm charts'){
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root") {
                                dir ("${WORKSPACE}/deploy/helms") {
                                    chartNames = sh(returnStdout: true, script: 'ls').split()
                                    println (chartNames)
                                    for (chart in chartNames){
                                        sh """
                                            export HELM_HOME="\$(pwd)"

                                            helm init --client-only
                                            helm dependency update "${chart}"
                                            helm package --version "${Globals.buildVersion}" "${chart}"
                                        """
                                    }
                                }
                                withCredentials([[
                                $class: 'UsernamePasswordMultiBinding',
                                credentialsId: 'nexus-local-repository',
                                usernameVariable: 'USERNAME',
                                passwordVariable: 'PASSWORD']]) {
                                    dir ("${WORKSPACE}/deploy/helms") {
                                        script {
                                            for (chart in chartNames){
                                            sh"""
                                            curl -u ${USERNAME}:${PASSWORD} ${env.param_helm_repository} --upload-file ${chart}-${Globals.buildVersion}.tgz
                                            """
                                            }
                                        }
                                    }
                                }
                                dir ("${WORKSPACE}/legion-helm-charts") {
                                    if (env.param_stable_release) {
                                        //checkout repo with existing charts  (needed for generating correct repo index file )
                                        git branch: "${env.param_helm_repo_git_branch}", poll: false, url: "${env.param_helm_repo_git_url}"
                                        //move packed charts to folder (where repo was checkouted)
                                        for (chart in chartNames){
                                            sh"""
                                            mkdir -p ${WORKSPACE}/legion-helm-charts/${chart}
                                            cp ${WORKSPACE}/deploy/helms/${chart}-${Globals.buildVersion}.tgz ${WORKSPACE}/legion-helm-charts/${chart}/
                                            git add ${chart}/${chart}-${Globals.buildVersion}.tgz
                                            """
                                        }
                                        sh """
                                        helm repo index ./
                                        git add index.yaml
                                        git status
                                        git commit -m "Release ${Globals.buildVersion}"
                                        git push origin ${env.param_helm_repo_git_branch}
                                        """
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Upload Ansible Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-ansible')
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
                stage('Upload Airflow Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-airflow')
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
                stage('Upload oauth2-proxy Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-oauth2-proxy')
                        }
                    }
                }
                stage('Upload kube-fluentd Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-kube-fluentd')
                        }
                    }
                }
                stage('Upload kube-elb-security Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-kube-elb-security')
                        }
                    }
                }
                stage('Upload python-toolchain Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('python-toolchain')
                        }
                    }
                }
            }
        }
        stage("CI Stage") {
            steps {
                script {
                    if (env.param_stable_release) {
                        stage('Update Legion version string'){
                            //Update version.py file in legion package with new version string
                            if (env.param_update_version_string.toBoolean()){
                                print('Update Legion package version string')
                                if (env.param_next_version){
                                    sh """
                                    git reset --hard
                                    git checkout develop
                                    sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                                    git commit -a -m "Bump Legion version to ${nextVersion}" && git push origin develop
                                    """
                                } else {
                                    throw new Exception("next_version must be specified with update_version_string parameter")
                                }
                            }
                            else {
                                print("Skipping version string update")
                            }
                        }

                        stage('Update Master branch'){
                            if (env.param_update_master.toBoolean()){
                                sh """
                                git reset --hard
                                git checkout develop
                                git checkout master && git pull -r origin master
                                git pull -r origin develop
                                git push origin master
                                """
                            }
                            else {
                                print("Skipping Master branch update")
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                legion = load "${sharedLibPath}"
                legion.notifyBuild(currentBuild.currentResult)
            }
            deleteDir()
        }
    }
}
