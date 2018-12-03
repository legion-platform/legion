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
        buildDiscarder(logRotator(numToKeepStr: '15', artifactNumToKeepStr: '15'))
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
        //Docker registry to build package from
        param_docker_registry = "${params.DockerRegistry}"
        ///Job parameters
        buildWorkspace = "${WORKSPACE}/k8s/k8s-infra"
        oauth2ProxyDockerimage = "k8s-oauth2-proxy"
        kubeFluentdDockerimage = "k8s-kube-fluentd"
        kubeElbSecurityDockerimage = "k8s-kube-elb-security"
        sharedLibPath = "deploy/legionPipeline.groovy"

    }
    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    legion = load "${sharedLibPath}"
                    Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                    Globals.rootCommit = Globals.rootCommit.trim()
                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerCacheArg = "${param_enable_docker_cache}" ? '' : '--no-cache'

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user=${env.BUILD_USER} --label build_date=${buildDate}"
                    println(Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (env.param_stable_release) {
                        if (env.param_release_version){
                            Globals.buildVersion = sh returnStdout: true, script: "python3.6 tools/update_version_id --build-version=${param_release_version} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                    }
                    Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                    env.BuildVersion = Globals.buildVersion

                    currentBuild.description = "${Globals.buildVersion} ${param_git_branch}"
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
                        dir ("${buildWorkspace}/kube-fluentd") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/${kubeFluentdDockerimage}:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Build kube-elb-security') {
                    steps {
                        dir ("${buildWorkspace}/kube-elb-security") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/${kubeElbSecurityDockerimage}:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Build oauth2-proxy') {
                    steps {
                        dir ("${buildWorkspace}/oauth2-proxy") {
                            sh """
                            docker build ${Globals.dockerCacheArg} -t legion/${oauth2ProxyDockerimage}:${Globals.buildVersion} ${Globals.dockerLabels} -f Dockerfile .
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
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${param_docker_registry}"
                }
            }
        }
        stage('Push docker images') {
            parallel {
                stage('Upload oauth2-proxy Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage("${oauth2ProxyDockerimage}", "${Globals.buildVersion}")
                        }

                    }
                }
                stage('Upload kube-fluentd Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage("${kubeFluentdDockerimage}", "${Globals.buildVersion}")
                        }
                    }
                }
                stage('Upload kube-elb-security Docker Image') {
                    steps {
                        script {
                            legion.uploadDockerImage("${kubeElbSecurityDockerimage}", "${Globals.buildVersion}")
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