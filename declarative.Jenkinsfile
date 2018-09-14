import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
}

pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                    Globals.rootCommit = Globals.rootCommit.trim()
                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user=${env.BUILD_USER} --label build_date=${buildDate}"
                    println(Globals.dockerLabels)

                    if (params.StableRelease) {
                        stage('Set GIT release Tag'){
                            if (params.PushGitTag){
                                print('Set Release tag')
                                sh """
                                if [ `git tag |grep ${params.ReleaseVersion}` ]; then
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
                sh "docker build -t legion-docker-agent:${env.BUILD_NUMBER} -f pipeline.Dockerfile ."
            }
        }
        stage('Set Legion build version') {
            agent { 
                docker {
                    image "legion-docker-agent:${env.BUILD_NUMBER}"
                }
            }
            steps {
                script {
                    if (params.StableRelease) {
                        if (params.ReleaseVersion){
                            Globals.buildVersion = sh returnStdout: true, script: "update_version_id --build-version=${params.ReleaseVersion} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                    }
                    Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

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
                }
            }
		}
        stage('Build dependencies') {
            parallel {
                stage('Build Jenkins plugin') {
                    agent {
                        docker {
                            image 'maven:3'
                            args '-v $HOME/.m2:/tmp/.m2 -e HOME=/tmp'
                        }
                    }
                    steps {
                        /// Jenkins plugin to be used in Jenkins Docker container only
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

                            sh '''
                            cd legion
                            LEGION_VERSION="\$(python -c 'import legion; print(legion.__version__);')"
                            cd docs
                            sphinx-apidoc -f --private -o source/ ../legion/ -V "\$LEGION_VERSION"
                            sed -i "s/'1.0'/'\$LEGION_VERSION'/" source/conf.py
                            make html
                            find build/html -type f -name '*.html' | xargs sed -i -r 's/href="(.*)\\.md"/href="\\1.html"/'
                            cd ../../
                            '''

                            sh "cd legion && cp -rf docs/build/html/ \"${params.LocalDocumentationStorage}/${Globals.buildVersion}/\""
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
                        pycodestyle --show-source --show-pep8 tests --ignore E402,E126,W503
                        pydocstyle --source legion

                        export TERM="linux"
                        rm -f pylint.log
                        pylint legion >> pylint.log || exit 0
                        pylint tests >> pylint.log || exit 0
                        cd ..
                        '''

                        archiveArtifacts 'legion/pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''

                        sh '''
                        cd legion_airflow
                        pycodestyle legion_airflow
                        pycodestyle tests
                        pydocstyle legion_airflow

                        pylint legion_airflow >> pylint.log || exit 0
                        pylint tests >> pylint.log || exit 0
                        cd ..
                        '''
        
                        archiveArtifacts 'legion/pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''

                        sh '''
                        cd legion_airflow
                        pycodestyle legion_airflow
                        pycodestyle tests
                        pydocstyle legion_airflow

                        pylint legion_airflow >> pylint.log || exit 0
                        pylint tests >> pylint.log || exit 0
                        cd ..
                        '''

                        archiveArtifacts 'legion/pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''

                        sh '''
                        cd legion_airflow
                        pycodestyle legion_airflow
                        pycodestyle tests
                        pydocstyle legion_airflow

                        pylint legion_airflow >> pylint.log || exit 0
                        pylint tests >> pylint.log || exit 0
                        cd ..
                        '''

                        archiveArtifacts 'legion_airflow/pylint.log'
                        warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion_airflow/pylint.log']], unHealthy: ''
                    }
                }
                stage("Build Base Docker image") {
                    steps {
                        sh """
                        cd base-python-image
                        docker build -t "legion/base-python-image:${Globals.buildVersion}" ${Globals.dockerLabels} .
                        """
                    }
                }
            }
        }
        stage("Upload dependencies") {
            parallel {
                stage("Upload Base Docker Image") {
                    steps {
                        script {
                            UploadDockerImage('base-python-image')
                        }
                    }
                }
                stage("Upload Legion") {
                    agent {
                        docker {
                            image "legion-docker-agent:${env.BUILD_NUMBER}"
                            args "-e HOME=/tmp"
                        }
                    }
                    steps {
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
repository=https://nexus.cc.mldev.ada.iqvia.com/repository/pypi-hosted/
username=${env.USERNAME}
password=${env.PASSWORD}
EOL
"""
                        }
                        sh """
                        ln -s /src/legion/dist/legion-*.tar.gz ./legion-${Globals.buildVersion}.tar.gz
                        ln -s /src/legion_airflow/dist/legion_airflow-*.tar.gz ./legion_airflow-${Globals.buildVersion}.tar.gz
                        ln -s /src/legion_test/dist/legion_test*.tar.gz ./legion_test-${Globals.buildVersion}.tar.gz
                        twine upload -r ${params.LocalPyPiDistributionTargetName} ./legion-${Globals.buildVersion}.*
                        twine upload -r ${params.LocalPyPiDistributionTargetName} ./legion_airflow-${Globals.buildVersion}.*
                        twine upload -r ${params.LocalPyPiDistributionTargetName} ./legion_test-${Globals.buildVersion}.*
                        """
                    }
                }
            }
        }
        stage("Build Docker Images") {
            parallel {
                stage("Build Grafana Docker image") {
                    steps {
                        sh """
                        cd k8s/grafana
                        docker build --build-arg pip_extra_index_params=" --extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-grafana:${Globals.buildVersion} ${Globals.dockerLabels} .
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
                        docker build --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edge:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Jenkins Docker image") {
                    steps {
                        sh """
                        cd k8s/jenkins
                        docker build --build-arg version="${Globals.buildVersion}" --build-arg jenkins_plugin_version="${Globals.buildVersion}" --build-arg jenkins_plugin_server="${params.JenkinsPluginsRepository}" -t legion/k8s-jenkins:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Bare model 1") {
                    steps {
                        sh """
                        cd k8s/test-bare-model-api/model-1
                        docker build --build-arg version="${Globals.buildVersion}" -t legion/test-bare-model-api-model-1:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Bare model 2") {
                    steps {
                        sh """
                        cd k8s/test-bare-model-api/model-2
                        docker build --build-arg version="${Globals.buildVersion}" -t legion/test-bare-model-api-model-2:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Edi Docker image") {
                    steps {
                        sh """
                        cd k8s/edi
                        docker build --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edi:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Build Airflow Docker image") {
                    steps {
                        sh """
                        cd k8s/airflow
                        docker build --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-airflow:${Globals.buildVersion} ${Globals.dockerLabels} .
                        """
                    }
                }
                stage("Run Python tests") {
                    agent { 
                        docker {
                            image "legion-docker-agent:${env.BUILD_NUMBER}"
                            args "-v ${LocalDocumentationStorage}:${LocalDocumentationStorage} -v /var/run/docker.sock:/var/run/docker.sock -u root"
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
	}
    post { 
        cleanup { 
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
    commit *${Globals.rootCommit}*
    version *${Globals.buildVersion}*
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