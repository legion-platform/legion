import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

def legion

pipeline {
    agent any

    options{
        buildDiscarder(logRotator(numToKeepStr: '5'))
        disableConcurrentBuilds()
    }
    environment {
        build_workspace = "${WORKSPACE}"
        def dex_dockerimage = "k8s-dex"
        shared_lib_path = "deploy/legionPipeline.groovy"
    }
    stages {
        stage('Checkout and set build vars') {
            steps {
                dir ("${build_workspace}/dex") {
                    checkout([$class: 'GitSCM', branches: [[name: "${params.GitBranchDex}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: "${params.GitRepoDex}"]]])
                    script {
                        Globals.rootCommit = sh(returnStdout: true, script: 'git rev-parse --short HEAD')
                        Globals.rootCommit = Globals.rootCommit.trim()
                    }
                }
                dir ("${build_workspace}/legion") {
                    script {
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
                                Globals.buildVersion = sh returnStdout: true, script: "python3.6 tools/update_version_id --build-version=${params.ReleaseVersion} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER} --git-revision=${Globals.rootCommit}"
                            } else {
                                print('Error: ReleaseVersion parameter must be specified for stable release')
                                exit 1
                            }
                        } else {
                            Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER} --git-revision=${Globals.rootCommit}"
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
                    }
                }
            }
        }
        stage('Build docker image Dex') {
            steps {
                dir ("${build_workspace}/dex") {
                    sh "docker build ${Globals.dockerCacheArg} -t ${params.DockerRegistry}/${dex_dockerimage}:${BUILD_NUMBER} -f Dockerfile ."
                }
            }
        }
        stage('Push docker image Dex') {
            steps {
                sh """
                docker tag ${params.DockerRegistry}/${dex_dockerimage}:${BUILD_NUMBER} ${params.DockerRegistry}/${dex_dockerimage}:latest
                docker tag ${params.DockerRegistry}/${dex_dockerimage}:${BUILD_NUMBER} ${params.DockerRegistry}/${dex_dockerimage}:${Globals.buildVersion}
                docker push ${params.DockerRegistry}/${dex_dockerimage}:${Globals.buildVersion}
                docker push ${params.DockerRegistry}/${dex_dockerimage}:latest
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