def legion
def commit_id = null
def dockerCacheArg

pipeline {
    agent any

    options{
        buildDiscarder(logRotator(numToKeepStr: '5'))
        disableConcurrentBuilds()
    }
    parameters {
        booleanParam(defaultValue: false, description: 'Enable slack notifications', name: 'EnableSlackNotifications')
        booleanParam(defaultValue: false, description: '', name: 'EnableDockerCache')
    }
    environment {
        build_workspace = "${WORKSPACE}"
        def dex_dockerimage = "k8s-dex"
        shared_lib_path = "deploy/legionPipeline.groovy"
        docker_registry = "legionplatform"
        dex_repository = "https://github.com/legion-platform/dex.git"
        dex_branch_name = "feat/legion"
        legion_repository = "https://github.com/legion-platform/legion.git"
        legion_branch_name = "develop"
    }
    stages {
        stage('Checkout and set build vars') {
            steps {
                dir ("${build_workspace}/dex") {
                    checkout([$class: 'GitSCM', branches: [[name: "${dex_branch_name}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: "${dex_repository}"]]])
                    script {
                        dockerCacheArg = (params.EnableDockerCache) ? '' : '--no-cache'
                        commit_id = sh(returnStdout: true, script: 'git rev-parse --short HEAD')
                        sh "echo ${commit_id}"
                    }
                }
                dir ("${build_workspace}/legion") {
                    checkout([$class: 'GitSCM', branches: [[name: "${legion_branch_name}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: "${legion_repository}"]]])
                }
            }
        }
        stage('Build docker image Dex') {
            steps {
                dir ("${build_workspace}/dex") {
                    sh '''
                    docker build  ${dockerCacheArg} -t ${docker_registry}/${dex_dockerimage}:${BUILD_NUMBER} -f Dockerfile .
                    '''
                }
            }
        }
        stage('Push docker image Dex') {
            steps {
                sh """
                docker tag ${docker_registry}/${dex_dockerimage}:${BUILD_NUMBER} ${docker_registry}/${dex_dockerimage}:latest
                docker tag ${docker_registry}/${dex_dockerimage}:${BUILD_NUMBER} ${docker_registry}/${dex_dockerimage}:${BUILD_NUMBER}-${commit_id}
                docker push ${docker_registry}/${dex_dockerimage}:${BUILD_NUMBER}-${commit_id}
                docker push ${docker_registry}/${dex_dockerimage}:latest
                """
            }
        }
    }
    post {
      always {
          script {
              legion = load "legion/${shared_lib_path}"
              legion.notifyBuild(currentBuild.currentResult)
          }
          deleteDir()
      }
  }
}