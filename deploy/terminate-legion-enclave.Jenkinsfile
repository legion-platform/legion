pipeline {
    agent any

    environment {
        //Input parameters
        param_git_branch = "${params.GitBranch}"
        param_profile = "${params.Profile}"
        param_legion_version = "${params.LegionVersion}"
        aram_enclave_name = "${params.EnclaveName}"
        param_docker_repo = "${params.DockerRepo}"
        //Job parameters
        sharedLibPath = "deploy/legionPipeline.groovy"
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    legion = load "${env.sharedLibPath}"
                    legion.buildDescription()
                }
            }
        }
        
        stage('Terminate Legion Enclave') {
            steps {
                script {
                    legion.terminateLegionEnclave()
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