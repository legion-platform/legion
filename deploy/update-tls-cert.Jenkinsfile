pipeline {
    agent { label 'ec2orchestrator'}

    environment {
        //Input parameters
        param_git_branch = "${params.GitBranch}"
        param_profile = "${params.Profile}"
        param_legion_version = "${params.LegionVersion}"
        param_docker_repo = "${params.DockerRepo}"
        param_debug_run = "${params.DebugRun}"
        //Job parameters
        sharedLibPath = "deploy/legionPipeline.groovy"
        ansibleHome =  "/opt/legion/deploy/ansible"
        ansibleVerbose = '-v'
        helmLocalSrc = 'false'
    }

    stages {
        stage('Checkout GIT'){
            steps {
                cleanWs()
                checkout scm
                script {
                        legion = load "${env.sharedLibPath}"
                        legion.buildDescription()
                }
            }
        }

        stage('Check and Update TLS Certificates') {
            steps {
                script {
                    legion.ansibleDebugRunCheck(env.param_debug_run)
                    legion.updateTLSCert()
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
        }
        cleanup {
            script {
                legion.cleanupClusterSg(param_legion_version ?: cleanupContainerVersion)
            }
            deleteDir()
        }
    }
}

