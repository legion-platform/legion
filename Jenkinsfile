import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

def chartNames = null

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
            infraBuildWorkspace = "${WORKSPACE}/build/containers/k8s-infra"
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
                        BUILD_USER = binding.hasVariable('BUILD_USER') ? "${BUILD_USER}" : "null"
                    }

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user='${BUILD_USER}' --label build_date=${buildDate}"
                    println("Docker labels: " + Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (env.param_stable_release) {
                        if (env.param_release_version ) {
                            Globals.buildVersion = sh returnStdout: true, script: "python build/update_version_id --build-version=${env.param_release_version} legion/legion/version.py ${env.BUILD_NUMBER} '${BUILD_USER}'"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python build/update_version_id ${env.BUILD_NUMBER} '${BUILD_USER}'"
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
                            sshagent(["${env.param_git_deploy_key}"]) {
                                sh """
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
                            }
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

        stage("Build base images") {
            parallel {
                stage("Build toolchains Docker image"){
                    steps {
                        script {
                            legion.buildLegionImage('python-toolchain', 'toolchains/python')
                        }
                    }
                }
                stage('Build Agent Docker Image') {
                    steps {
                        script {
                            legion.buildLegionImage('legion-docker-agent', 'pipeline')
                            legion.uploadDockerImage('legion-docker-agent')
                        }
                    }
                }
                stage("Build Jenkins Legion plugin") {
                   steps {
                       script {
                           docker.image("maven:3.5.3-jdk-8").inside("-v /tmp/.m2:/tmp/.m2 -e HOME=/tmp -u root") {
                               /// Jenkins plugin which will be used in Jenkins Docker container only
                               sh """
                               export JAVA_HOME=\$(readlink -f /usr/bin/java | sed "s:bin/java::")
                               mvn -f build/containers/jenkins/legion-jenkins-plugin/pom.xml clean -Dmaven.repo.local=/tmp/.m2/repository
                               mvn -f build/containers/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${Globals.buildVersion} -Dmaven.repo.local=/tmp/.m2/repository
                               mvn -f build/containers/jenkins/legion-jenkins-plugin/pom.xml install -Dmaven.repo.local=/tmp/.m2/repository
                               """

                               archiveArtifacts 'build/containers/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi'

                               withCredentials([[
                                   $class: 'UsernamePasswordMultiBinding',
                                   credentialsId: 'nexus-local-repository',
                                   usernameVariable: 'USERNAME',
                                   passwordVariable: 'PASSWORD']]) {
                                   sh """
                                   curl -v -u $USERNAME:$PASSWORD \
                                   --upload-file build/containers/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                                   ${env.param_jenkins_plugins_repository_store}/${Globals.buildVersion}/legion-jenkins-plugin.hpi
                                   """
                                   script {
                                       if (env.param_stable_release){
                                           sh """
                                           curl -v -u $USERNAME:$PASSWORD \
                                           --upload-file build/containers/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                                           ${env.param_jenkins_plugins_repository_store}/latest/legion-jenkins-plugin.hpi
                                           """
                                       }
                                   }
                               }
                               sh "rm -rf ${WORKSPACE}/build/containers/jenkins/legion-jenkins-plugin/*"
                            }
                        }
                    }
                }
            }
        }
        stage("Build Docker images & Run Tests") {
            parallel {
                 stage("Build Jenkins Docker image") {
                    steps {
                        script {
                             legion.buildLegionImage('k8s-jenkins', "jenkins", """--build-arg update_center_url="" --build-arg update_center_experimental_url="${env.param_jenkins_plugins_repository}" --build-arg update_center_download_url="${env.param_jenkins_plugins_repository}" --build-arg legion_plugin_version="${Globals.buildVersion}" """)
                         }
                     }
                 }
                 stage('Build docs') {
                     steps {
                         script {
                             docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
                                 sh "make LEGION_VERSION=${Globals.buildVersion} build-docs"

                                 archiveArtifacts artifacts: "legion_docs_${Globals.buildVersion}.tar.gz"
                            }
                        }
                    }
                 }
                 stage("Build Ansible Docker image") {
                     steps {
                         script {
                             legion.buildLegionImage('k8s-ansible', 'ansible')
                         }
                     }
                 }
                 stage('Run Python code analyzers') {
                    steps {
                        script{
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
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
                stage("Build Edge Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-edge', 'edge')
                        }
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-edi', "edi")
                        }
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-fluentd', 'fluentd')
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
                            legion.buildLegionImage('k8s-kube-fluentd', "k8s-infra/kube-fluentd")
                        }
                    }
                }
                stage('Build kube-elb-security') {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-kube-elb-security', "k8s-infra/kube-elb-security")
                        }
                    }
                }
                stage('Build oauth2-proxy') {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-oauth2-proxy', "k8s-infra/oauth2-proxy")
                        }
                    }
                }
                stage("Run unittests") {
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root --net host") {
                                    sh """
                                        CURRENT_DIR="\$(pwd)"
                                        cd /src

                                        make SANDBOX_PYTHON_TOOLCHAIN_IMAGE="legion/python-toolchain:${Globals.buildVersion}" \
                                             TEMP_DIRECTORY="\${CURRENT_DIR}" unittests || true
                                    """

                                    sh 'cp -r /src/target/coverage.xml /src/target/nosetests.xml /src/target/cover ./'

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
                                if (env.param_stable_release) {
                                    //checkout repo with existing charts  (needed for generating correct repo index file )
                                    sshagent(["${env.param_git_deploy_key}"]) {
                                        sh """
                                        mkdir ~/.ssh || true
                                        ssh-keyscan github.com >> ~/.ssh/known_hosts
                                        git clone ${env.param_helm_repo_git_url} && cd ${WORKSPACE}/legion-helm-charts
                                        git checkout ${env.param_helm_repo_git_branch}
                                        """
                                    }
                                    //move packed charts to folder (where repo was checkouted)
                                    for (chart in chartNames){
                                        sh"""
                                        cd ${WORKSPACE}/legion-helm-charts
                                        mkdir -p ${WORKSPACE}/legion-helm-charts/${chart}
                                        mv ${WORKSPACE}/deploy/helms/${chart}-${Globals.buildVersion}.tgz ${WORKSPACE}/legion-helm-charts/${chart}/
                                        git add ${chart}/${chart}-${Globals.buildVersion}.tgz
                                        """
                                    }
                                    sshagent(["${env.param_git_deploy_key}"]) {
                                        sh """
                                        cd ${WORKSPACE}/legion-helm-charts
                                        helm repo index ./
                                        git add index.yaml
                                        git status
                                        git commit -m "Release ${Globals.buildVersion}"
                                        git push origin ${env.param_helm_repo_git_branch}
                                        """

                                    }
                                }

                                // Cleanup directory
                                sh """
                                rm -rf ${WORKSPACE}/legion-helm-charts
                                rm -rf ${WORKSPACE}/deploy/helms
                                """
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
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/sdk/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/cli/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/toolchains/python/dist/legion-*'
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
"""
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
                                    sshagent(["${env.param_git_deploy_key}"]) {
                                        sh """
                                        git reset --hard
                                        git checkout develop
                                        sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                                        git commit -a -m "Bump Legion version to ${nextVersion}" && git push origin develop
                                        """
                                    }
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
                                sshagent(["${env.param_git_deploy_key}"]) {
                                    sh """
                                    git reset --hard
                                    git checkout develop
                                    git checkout master && git pull -r origin master
                                    git pull -r origin develop
                                    git push origin master
                                    """
                                }
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
