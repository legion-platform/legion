import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
}

pipeline {
    agent { 
        dockerfile {
            filename 'pipeline.Dockerfile'
            args "-v /var/run/docker.sock:/var/run/docker.sock -v ${LocalDocumentationStorage}:${LocalDocumentationStorage} -v \$HOME/.m2:\$HOME/.m2"
        }
    }

    stages {
        stage('Checkout') {
            steps {
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
        stage('Set Legion build version') {
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
                }
            }
		}
        stage('Build dependencies') {
            parallel {
                stage('Build Jenkins plugin') {
                    steps {
                        /// Jenkins plugin to be used in Jenkins Docker container only
                        sh """
                        mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml clean
                        mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${Globals.buildVersion}
                        mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml install
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

                            sh "cd legion && cp -rf docs/build/html/ \"${params.LocalDocumentationStorage}\$(python -c 'import legion; print(legion.__version__);')/\""
                        }
                    }
                }
                stage('Run Python code analyzers') {
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
            }
            post { 
                cleanup { 
                    deleteDir()
                }
            }
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