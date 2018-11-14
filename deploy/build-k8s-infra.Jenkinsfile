import java.text.SimpleDateFormat

def legion

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

pipeline {
    agent any

    options{
        buildDiscarder(logRotator(numToKeepStr: '5'))
        disableConcurrentBuilds()
    }
    environment {
        build_workspace = "${WORKSPACE}/k8s/k8s-infra"
        def oauth2_proxy_docker_dockerimage = "k8s-oauth2-proxy-docker"
        def kube_fluentd_dockerimage = "k8s-kube-fluentd"
        def kube_elb_security_dockerimage = "k8s-kube-elb-security"
        shared_lib_path = "deploy/legionPipeline.groovy"
        //Enable docker cache parameter
        enable_docker_cache = "${params.EnableDockerCache}"
        //Build major version release and optionally push it to public repositories
        stable_release = "${params.StableRelease}"
        //Release version to tag all artifacts to
        release_version = "${params.ReleaseVersion}"
        //Git Branch to build package from
        git_branch = "${params.GitBranch}"
        //Docker registry 
        docker_registry = "${params.DockerRegistry}"
    }
    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    legion = load "${shared_lib_path}"
                    Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                    Globals.rootCommit = Globals.rootCommit.trim()
                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerCacheArg = "${enable_docker_cache}" ? '' : '--no-cache'

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user=${env.BUILD_USER} --label build_date=${buildDate}"
                    println(Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (env.stable_release) {
                        if (env.release_version){
                            Globals.buildVersion = sh returnStdout: true, script: "python3.6 tools/update_version_id --build-version=${release_version} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                    }
                    Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                    env.BuildVersion = Globals.buildVersion

                    currentBuild.description = "${Globals.buildVersion} ${git_branch}"
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
        stage('Build docker images') {
            parallel {
                stage('Build kube-fluentd') {
                    steps {
                        dir ("${build_workspace}/kube-fluentd") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/${kube_fluentd_dockerimage}:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Build kube-elb-security') {
                    steps {
                        dir ("${build_workspace}/kube-elb-security") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/${kube_elb_security_dockerimage}:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Build oauth2-proxy-docker') {
                    steps {
                        dir ("${build_workspace}/oauth2-proxy-docker") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/${oauth2_proxy_docker_dockerimage}:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
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
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${docker_registry}"
                }
            }
        }
        stage('Push docker images') {
            parallel {
                stage('Upload oauth2-proxy-docker Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage("${oauth2_proxy_docker_dockerimage}", "${Globals.buildVersion}")
                        }

                    }
                }
                stage('Upload kube-fluentd Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage("${kube_fluentd_dockerimage}", "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload kube-elb-security Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage("${kube_elb_security_dockerimage}", "${Globals.buildVersion}")
                        }
                    }
                }
            }
        }
    }
    post {
      always {
          script {
              legion.notifyBuild(currentBuild.currentResult)
          }
          deleteDir()
      }
  }
}