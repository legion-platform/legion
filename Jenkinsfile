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

    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                    Globals.rootCommit = Globals.rootCommit.trim()
                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerCacheArg = (params.EnableDockerCache) ? '' : '--no-cache'

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user=${env.BUILD_USER} --label build_date=${buildDate}"
                    println(Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (params.StableRelease) {
                        if (params.ReleaseVersion){
                            Globals.buildVersion = sh returnStdout: true, script: "python3.6 tools/update_version_id --build-version=${params.ReleaseVersion} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                    }

                    Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                    env.BuildVersion = Globals.buildVersion

                    currentBuild.description = "${Globals.buildVersion} ${params.GitBranch}"
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
                    if (params.StableRelease) {
                        stage('Set GIT release Tag'){
                            if (params.PushGitTag){
                                print('Set Release tag')
                                sh """
                                if [ `git tag |grep -w ${params.ReleaseVersion}` ]; then
                                    if [ ${params.ForceTagPush} = "true" ]; then
                                        echo 'Removing existing git tag'
                                        git tag -d ${params.ReleaseVersion}
                                        git push origin :refs/tags/${params.ReleaseVersion}
                                    else
                                        echo 'Specified tag already exists!'
                                        exit 1
                                    fi
                                fi
                                git tag ${params.ReleaseVersion}
                                git push origin ${params.ReleaseVersion}
                                """
                            } else {
                                print("Skipping release git tag push")
                            }
                        }
                    }
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
                            ${params.JenkinsPluginsRepositoryStore}/${Globals.buildVersion}/legion-jenkins-plugin.hpi
                            """
                            script {
                                if (params.StableRelease){
                                    sh """
                                    curl -v -u $USERNAME:$PASSWORD \
                                    --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                                    ${params.JenkinsPluginsRepositoryStore}/latest/legion-jenkins-plugin.hpi
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
                        cd legion
                        pycodestyle --show-source --show-pep8 legion
                        pycodestyle --show-source --show-pep8 tests --ignore E402,E126,W503,E731
                        pydocstyle --source legion

                        TERM="linux" pylint --persistent=n legion > legion-pylint.log || exit 0
                        TERM="linux" pylint --persistent=n tests >> legion-pylint.log || exit 0
                        cd ..
                        '''

                        archiveArtifacts 'legion/legion-pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/legion-pylint.log']], unHealthy: ''

                        sh '''
                        cd legion_airflow
                        pycodestyle --show-source --show-pep8 legion_airflow
                        pycodestyle --show-source --show-pep8 tests
                        pydocstyle legion_airflow

                        TERM="linux" pylint --persistent=n legion_airflow > legion_airflow-pylint.log || exit 0
                        TERM="linux" pylint --persistent=n tests >> legion_airflow-pylint.log || exit 0
                        cd ..
                        '''

                        archiveArtifacts 'legion_airflow/legion_airflow-pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion_airflow/legion_airflow-pylint.log']], unHealthy: ''

                        sh '''
                        cd legion_test

                        TERM="linux" pylint --persistent=n legion_test > legion_test-pylint.log || exit 0
                        cd ..
                        '''

                        archiveArtifacts 'legion_test/legion_test-pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion_test/legion_test-pylint.log']], unHealthy: ''
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
  ${params.LocalPyPiDistributionTargetName}

[${params.LocalPyPiDistributionTargetName}]
repository=${params.PyPiRepository.split('/').dropRight(1).join('/')}/
username=${env.USERNAME}
password=${env.PASSWORD}
EOL
"""
                            }
                            sh """
                            twine upload -r ${params.LocalPyPiDistributionTargetName} '/src/legion/dist/legion-${Globals.buildVersion}.*'
                            twine upload -r ${params.LocalPyPiDistributionTargetName} '/src/legion_test/dist/legion_test-${Globals.buildVersion}.*'
                            twine upload -r ${params.LocalPyPiDistributionTargetName} '/src/legion_airflow/dist/legion_airflow-${Globals.buildVersion}.*'
                            """

                            if (params.StableRelease) {
                                stage('Upload Legion package to pypi.org'){
                                    if (params.UploadLegionPackage){
                                        withCredentials([[
                                        $class: 'UsernamePasswordMultiBinding',
                                        credentialsId: 'pypi-repository',
                                        usernameVariable: 'USERNAME',
                                        passwordVariable: 'PASSWORD']]) {
                                            sh """cat > /tmp/.pypirc << EOL
[distutils]
index-servers =
  ${params.PyPiDistributionTargetName}

[${params.testPyPiDistributionTargetName}]
repository=https://test.pypi.org/legacy/
username=${env.USERNAME}
password=${env.PASSWORD}

[${params.PublicPyPiDistributionTargetName}]
repository=https://upload.pypi.org/legacy/
username=${env.USERNAME}
password=${env.PASSWORD}
EOL
"""
                                        }
                                        sh """
                                        twine upload -r ${params.PyPiDistributionTargetName} '/src/legion/dist/legion-${Globals.buildVersion}.*'
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
                    args "-v ${LocalDocumentationStorage}:${LocalDocumentationStorage}"
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

                    sh "cd legion && cp -rf docs/build/html/ \"${params.LocalDocumentationStorage}/${Globals.buildVersion}/\""
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
                    UploadDockerImage('base-python-image')
                }
            }
        }
        stage("Build Docker Images") {
            parallel {
                stage("Build Grafana Docker image") {
                    steps {
                        sh """
                        cd k8s/grafana
                        docker build ${Globals.dockerCacheArg} --build-arg pip_extra_index_params=" --extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-grafana:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Edge Docker image") {
                    steps {
                        sh """
                        rm -rf k8s/edge/static/docs
                        cp -rf ${params.LocalDocumentationStorage}/${Globals.buildVersion}/ k8s/edge/static/docs/
                        build_time=`date -u +'%d.%m.%Y %H:%M:%S'`
                        sed -i "s/{VERSION}/${Globals.buildVersion}/" k8s/edge/static/index.html
                        sed -i "s/{COMMIT}/${Globals.rootCommit}/" k8s/edge/static/index.html
                        sed -i "s/{BUILD_INFO}/#${env.BUILD_NUMBER} \$build_time UTC/" k8s/edge/static/index.html

                        cd k8s/edge
                        docker build ${Globals.dockerCacheArg} --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edge:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Jenkins Docker image") {
                    steps {
                        sh """
                        cd k8s/jenkins
                        docker build ${Globals.dockerCacheArg} --build-arg update_center_url="" --build-arg update_center_experimental_url="${params.JenkinsPluginsRepository}" --build-arg update_center_download_url="${params.JenkinsPluginsRepository}" --build-arg legion_plugin_version="${Globals.buildVersion}" -t legion/k8s-jenkins:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Bare models") {
                    steps {
                        // Build test-bare-model-api-model-1
                        sh """
                        cd tests/test-bare-model-api
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg model_id="demo-abc-model" --build-arg model_version="1.0" -t legion/test-bare-model-api-model-1:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                        // Build test-bare-model-api-model-2
                        sh """
                        cd tests/test-bare-model-api
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg model_id="demo-abc-model" --build-arg model_version="1.1" -t legion/test-bare-model-api-model-2:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                        // Build test-bare-model-api-model-3
                        sh """
                        cd tests/test-bare-model-api
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg model_id="edi-test-model" --build-arg model_version="1.2" -t legion/test-bare-model-api-model-3:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        sh """
                        cd k8s/edi
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edi:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Airflow Docker image") {
                    steps {
                        sh """
                        cd k8s/airflow
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-airflow:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        sh """
                        cd k8s/fluentd
                        docker build ${Globals.dockerCacheArg} --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-fluentd:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
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
                        VERBOSE=true BASE_IMAGE_VERSION="${Globals.buildVersion}" nosetests --with-coverage --cover-package legion --with-xunit --cover-html  --logging-level DEBUG -v || true
                        cd -
                        cp /src/legion/nosetests.xml legion/nosetests.xml
                        """
                        junit 'legion/nosetests.xml'

                        sh """
                        cp -rf /src/legion/cover \"${params.LocalDocumentationStorage}/${Globals.buildVersion}-cover\"
                        """
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
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${params.DockerRegistry}"
                }
            }
        }
        stage("Push Docker Images") {
            parallel {
                stage('Upload Grafana Docker Image') {
                    steps {
                        UploadDockerImage('k8s-grafana')
                    }
                }
                stage('Upload Edge Docker Image') {
                    steps {
                        UploadDockerImage('k8s-edge')
                    }
                }
                stage('Upload Jenkins Docker image') {
                    steps {
                        UploadDockerImage('k8s-jenkins')
                    }
                }
                stage('Upload Bare models') {
                    steps {
                        UploadDockerImage('test-bare-model-api-model-1')
                        UploadDockerImage('test-bare-model-api-model-2')
                        UploadDockerImage('test-bare-model-api-model-3')
                    }
                }
                stage('Upload Edi Docker image') {
                    steps {
                        UploadDockerImage('k8s-edi')
                    }
                }
                stage('Upload Airflow Docker image') {
                    steps {
                        UploadDockerImage('k8s-airflow')
                    }
                }
                stage('Upload Fluentd Docker image') {
                    steps {
                        UploadDockerImage('k8s-fluentd')
                    }
                }
            }
        }
        stage("CI Stage") {
            steps {
                script {
                    if (params.StableRelease) {
                        stage('Update Legion version string'){
                            if (params.UpdateVersionString){
                                print('Update Legion package version string')
                                def nextVersion
                                if (params.NextVersion){
                                    nextVersion = params.NextVersion
                                } else {
                                    def ver_parsed = params.ReleaseVersion.split("\\.")
                                    ver_parsed[1] = ver_parsed[1].toInteger() + 1
                                    nextVersion = ver_parsed.join(".")
                                }
                                sh """
                                git reset --hard
                                sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                                git commit -a -m "Bump Legion version to ${nextVersion}" && git push origin develop
                                """
                            }
                            else {
                                print("Skipping version string update")
                            }
                        }

                        stage('Update Master branch'){
                            if (params.UpdateMaster){
                                sh """
                                git reset --hard
                                git co master && git pull -r origin master
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
        stage('Package helm charts'){
            steps{
                dir ("${WORKSPACE}/deploy/helms") {
                    script {
                        chartNames = sh(returnStdout: true, script: 'ls').split()
                        println (chartNames)
                        for (chart in chartNames){
                            sh"""
                            sed -i 's@^version: .*\$@version: ${Globals.buildVersion}@g' ${chart}/Chart.yaml
                            helm package ${chart}
                            """
                        }
                    }
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
                               curl -u ${USERNAME}:${PASSWORD} ${params.NexusHelmRepository} --upload-file ${chart}-${Globals.buildVersion}.tgz
                               """
                            }
                        }
                    }
                }
                dir ("${WORKSPACE}/legion-helm-charts") {
                    script{
                    if (params.StableRelease) {
                        stage('Update Legion version string'){
                            if (params.UpdateVersionString){
                                //checkout repo with existing charts  (needed for generating correct repo index file )
                                checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: 'https://github.com/legion-platform/legion-helm-charts.git']]])
                                //move packed charts to folder (where repo was checkouted)
                                for (chart in chartNames){
                                    sh"""
                                    cp ${WORKSPACE}/deploy/helms/${chart}--${Globals.buildVersion}.tgz ${WORKSPACE}/legion-helm-charts/
                                    git add ${chart}--${Globals.buildVersion}.tgz
                                    """
                                }
                                sh """
                                ls -alh
                                helm repo index ./
                                cat index.yaml
                                git add index.yaml
                                git status
                                echo "Release ${Globals.buildVersion}"
                                """
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
                legion = load "deploy/legionPipeline.groovy"
                legion.notifyBuild(currentBuild.currentResult)
            }
            deleteDir()
        }
    }
}

def UploadDockerImageLocal(imageName) {
    sh """
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    docker push ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    """
}

def UploadDockerImagePublic(imageName) {
    sh """
    # Push stable image to local registry
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerRegistry}/${imageName}:latest
    docker push ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    docker push ${params.DockerRegistry}/${imageName}:latest
    # Push stable image to DockerHub
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerHubRegistry}/${imageName}:${Globals.buildVersion}
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerHubRegistry}/${imageName}:latest
    docker push ${params.DockerHubRegistry}/${imageName}:${Globals.buildVersion}
    docker push ${params.DockerHubRegistry}/${imageName}:latest
    """
}

def UploadDockerImage(imageName) {
    if (params.StableRelease) {
         UploadDockerImagePublic(imageName)
    } else {
        UploadDockerImageLocal(imageName)
    }
}
