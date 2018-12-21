import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

def chartNames = null

pipeline {
    agent any

    options{
            buildDiscarder(logRotator(numToKeepStr: '35', artifactNumToKeepStr: '35'))
            disableConcurrentBuilds()
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
            ///Job parameters
            localDocumentationStorage = "/www/docs/"
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
                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerCacheArg = (env.param_enable_docker_cache) ? '' : '--no-cache'

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user=${env.BUILD_USER} --label build_date=${buildDate}"
                    println(Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (env.param_stable_release) {
                        if (env.param_release_version){
                            Globals.buildVersion = sh returnStdout: true, script: "python3.6 tools/update_version_id --build-version=${env.param_release_version} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
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

                    /// Set Git Tag in case of stable release
                    if (env.param_stable_release) {
                        stage('Set GIT release Tag'){
                            if (env.param_push_git_tag){
                                print('Set Release tag')
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
                            } else {
                                print("Skipping release git tag push")
                            }
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
                sh "docker build ${Globals.dockerCacheArg} -t legion-docker-agent:${env.BUILD_NUMBER} -f pipeline.Dockerfile ."
            }
        }
        stage('Build dependencies') {
            parallel {
                stage('Build Jenkins plugin') {
                    agent {
                        docker {
                            image 'maven:3.5.3-jdk-8'
                            args '-v $HOME/.m2:/tmp/.m2 -e HOME=/tmp'
                        }
                    }
                    steps {
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
                    }
                }
                stage('Run Python code analyzers') {
                    agent {
                        docker {
                            image "legion-docker-agent:${env.BUILD_NUMBER}"
                        }
                    }
                    steps {
                        sh '''
                        pycodestyle --show-source --show-pep8 legion/legion
                        pycodestyle --show-source --show-pep8 legion/tests --ignore E402,E126,W503,E731
                        pydocstyle --source legion/legion

                        pycodestyle --show-source --show-pep8 legion_airflow/legion_airflow
                        pycodestyle --show-source --show-pep8 legion_airflow/tests
                        pydocstyle legion_airflow/legion_airflow

                        # Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
                        touch legion/tests/__init__.py

                        TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion/legion > legion-pylint.log
                        TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion/tests >> legion-pylint.log

                        TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_airflow/legion_airflow >> legion-pylint.log
                        TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_airflow/tests >> legion-pylint.log
                        TERM="linux" pylint --exit-zero --output-format=parseable --reports=no legion_test/legion_test >> legion-pylint.log
                        # Because of https://github.com/PyCQA/pylint/issues/352 or need to fix PYTHONPATH in unit tests
                        rm -rf legion/tests/__init__.py
                        '''

                        archiveArtifacts 'legion-pylint.log'
                        step([
                            $class                     : 'WarningsPublisher',
                            parserConfigurations       : [[
                                                                  parserName: 'PYLint',
                                                                  pattern   : 'legion-pylint.log'
                                                          ]],
                            unstableTotalAll           : '99999',
                            usePreviousBuildAsReference: true
                        ])
                    }
                }
                stage("Upload Legion package") {
                    agent {
                        docker {
                            image "legion-docker-agent:${env.BUILD_NUMBER}"
                            args "-e HOME=/tmp"
                        }
                    }
                    steps {
                        script {
                            withCredentials([[
                             $class: 'UsernamePasswordMultiBinding',
                             credentialsId: 'nexus-local-repository',
                             usernameVariable: 'USERNAME',
                             passwordVariable: 'PASSWORD']]) {
                                sh """cat > /tmp/.pypirc << EOL
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
                            twine upload -r ${env.param_local_pypi_distribution_target_name} '/src/legion/dist/legion-${Globals.buildVersion}.*'
                            twine upload -r ${env.param_local_pypi_distribution_target_name} '/src/legion_test/dist/legion_test-${Globals.buildVersion}.*'
                            twine upload -r ${env.param_local_pypi_distribution_target_name} '/src/legion_airflow/dist/legion_airflow-${Globals.buildVersion}.*'
                            """

                            if (env.param_stable_release) {
                                stage('Upload Legion package to pypi.org'){
                                    if (env.param_upload_legion_package){
                                        withCredentials([[
                                        $class: 'UsernamePasswordMultiBinding',
                                        credentialsId: 'pypi-repository',
                                        usernameVariable: 'USERNAME',
                                        passwordVariable: 'PASSWORD']]) {
                                            sh """cat > /tmp/.pypirc << EOL
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
                                        twine upload -r ${env.param_pypi_distribution_target_name} '/src/legion/dist/legion-${Globals.buildVersion}.*'
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
        stage('Build docs') {
            agent {
                docker {
                    image "legion-docker-agent:${env.BUILD_NUMBER}"
                    args "-v ${LocalDocumentationStorage}:${localDocumentationStorage}"
                }
            }
            steps {
                script {
                    fullBuildNumber = env.BUILD_NUMBER
                    fullBuildNumber.padLeft(4, '0')

                    sh """
                    cd legion/docs
                    sphinx-apidoc -f --private -o source/ ../legion/ -V '${Globals.buildVersion}'
                    sed -i 's/\'1.0\'/\'${Globals.buildVersion}\'/' source/conf.py
                    make html
                    find build/html -type f -name '*.html' | xargs sed -i -r 's/href=\"(.*)\\.md\"/href=\"\\1.html\"/'
                    cd ../../
                    """

                    sh "cd legion && cp -rf docs/build/html/ \"${localDocumentationStorage}/${Globals.buildVersion}/\""
                }
            }
        }
        stage("Build and Upload Base Docker Image") {
            steps {
                script {
                    sh """
                    cd base-python-image
                    docker build ${Globals.dockerCacheArg} -t "legion/base-python-image:${Globals.buildVersion}" ${Globals.dockerLabels} .
                    """
                    legion.uploadDockerImage('base-python-image', "${Globals.buildVersion}")
                }
            }
        }
        stage("Build Ansible Docker image") {
            steps {
                sh "docker build ${Globals.dockerCacheArg} -t legion/k8s-ansible:${Globals.buildVersion} ${Globals.dockerLabels}  -f k8s/ansible/Dockerfile ."
            }
        }    
        stage("Build Docker images & Helms") {
            parallel {
                stage("Build Grafana Docker image") {
                    steps {
                        sh """
                        cd k8s/grafana
                        docker build ${Globals.dockerCacheArg} --build-arg pip_extra_index_params=" --extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-grafana:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }

                stage("Build Edge Docker image") {
                    steps {
                        sh """
                        rm -rf k8s/edge/static/docs
                        cp -rf ${localDocumentationStorage}/${Globals.buildVersion}/ k8s/edge/static/docs/
                        build_time=`date -u +'%d.%m.%Y %H:%M:%S'`
                        sed -i "s/{VERSION}/${Globals.buildVersion}/" k8s/edge/static/index.html
                        sed -i "s/{COMMIT}/${Globals.rootCommit}/" k8s/edge/static/index.html
                        sed -i "s/{BUILD_INFO}/#${env.BUILD_NUMBER} \$build_time UTC/" k8s/edge/static/index.html

                        cd k8s/edge
                        docker build ${Globals.dockerCacheArg} --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edge:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Jenkins Docker image") {
                    steps {
                        sh """
                        cd k8s/jenkins
                        docker build ${Globals.dockerCacheArg} --build-arg update_center_url="" --build-arg update_center_experimental_url="${env.param_jenkins_plugins_repository}" --build-arg update_center_download_url="${env.param_jenkins_plugins_repository}" --build-arg legion_plugin_version="${Globals.buildVersion}" -t legion/k8s-jenkins:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Bare models") {
                    steps {
                        script {
                            legion.buildTestBareModel("demo-abc-model", "1.0", "1")
                            legion.buildTestBareModel("demo-abc-model", "1.1", "2")
                            legion.buildTestBareModel("edi-test-model", "1.2", "3")
                            legion.buildTestBareModel("feedback-test-model", "1.0", "4")
                            legion.buildTestBareModel("command-test-model", "1.0", "5")
                        }
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        sh """
                        cd k8s/edi
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edi:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Airflow Docker image") {
                    steps {
                        sh """
                        cd k8s/airflow
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-airflow:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        sh """
                        cd k8s/fluentd
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${env.param_pypi_repository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-fluentd:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                /// Infra images which are used during cluster creation
                stage('Build kube-fluentd') {
                    steps {
                        dir("${env.infraBuildWorkspace}/kube-fluentd") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/k8s-kube-fluentd:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Build kube-elb-security') {
                    steps {
                        dir("${env.infraBuildWorkspace}/kube-elb-security") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/k8s-kube-elb-security:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Build oauth2-proxy') {
                    steps {
                        script {
                            dir("${env.infraBuildWorkspace}/oauth2-proxy") {
                                sh """
                                docker build ${Globals.dockerCacheArg} -t legion/k8s-oauth2-proxy:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                                """
                            }
                        }
                    }
                }
                stage("Run Python tests") {
                    agent {
                        docker {
                            image "legion-docker-agent:${env.BUILD_NUMBER}"
                            args "-v ${LocalDocumentationStorage}:${LocalDocumentationStorage} -v /var/run/docker.sock:/var/run/docker.sock -u root --net host"
                        }
                    }
                    steps {
                        sh """
                        cd /src/legion
                        VERBOSE=true BASE_IMAGE_VERSION="${Globals.buildVersion}" nosetests --processes=10 \
                                                                                            --process-timeout=600 \
                                                                                            --with-coverage \
                                                                                            --cover-package legion \
                                                                                            --with-xunitmp \
                                                                                            --cover-html \
                                                                                            --logging-level DEBUG \
                                                                                            -v || true
                        cd -
                        cp /src/legion/nosetests.xml legion/nosetests.xml
                        """
                        junit 'legion/nosetests.xml'

                        sh """
                        cp -rf /src/legion/cover \"${localDocumentationStorage}/${Globals.buildVersion}-cover\"
                        """
                    }
                }
                stage('Package helm charts'){
                    steps{
                        dir ("${WORKSPACE}/deploy/helms") {
                            script {
                                chartNames = sh(returnStdout: true, script: 'ls').split()
                                println (chartNames)
                                for (chart in chartNames){
                                    sh"""
                                    sed -i 's@^version: .*\$@version: ${Globals.buildVersion}@g' ${chart}/Chart.yaml
                                    #Show package list, debug purposes
                                    helm package ${chart}
                                    """
                                }
                            }
                        }
                    }
                }
            }
        }

        stage("Push Docker Images") {
            parallel {
                stage('Upload Grafana Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-grafana', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Ansible Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-ansible', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Edge Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-edge', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Jenkins Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-jenkins', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Bare models') {
                    steps {
                        script {
                            legion.uploadDockerImage('test-bare-model-api-model-1', "${Globals.buildVersion}")
                            legion.uploadDockerImage('test-bare-model-api-model-2', "${Globals.buildVersion}")
                            legion.uploadDockerImage('test-bare-model-api-model-3', "${Globals.buildVersion}")
                            legion.uploadDockerImage('test-bare-model-api-model-4', "${Globals.buildVersion}")
                            legion.uploadDockerImage('test-bare-model-api-model-5', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Edi Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-edi', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Airflow Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-airflow', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload Fluentd Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-fluentd', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload oauth2-proxy Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-oauth2-proxy', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload kube-fluentd Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-kube-fluentd', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload kube-elb-security Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-kube-elb-security', "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Deploy helm charts'){
                    steps{
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
                            script{
                                if (env.param_stable_release) {
                                    stage('Publish helm charts to Public repo'){
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
            }
        }
        stage("CI Stage") {
            steps {
                script {
                    if (env.param_stable_release) {
                        stage('Update Legion version string'){
                            //Update version.py file in legion package with new version string
                            if (env.param_update_version_string){
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
                            if (env.param_update_master){
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
