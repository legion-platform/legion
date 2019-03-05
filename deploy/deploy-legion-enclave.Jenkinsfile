pipeline {
    agent { label 'ec2orchestrator'}

    environment {
        //Input parameters
        param_git_branch = "${params.GitBranch}"
        param_profile = "${params.Profile}"
        param_legion_version = "${params.LegionVersion}"
        aram_enclave_name = "${params.EnclaveName}"
        param_pypi_repo = "${params.PypiRepo}"
        param_docker_repo = "${params.DockerRepo}"
        param_helm_repo = "${params.HelmRepo}"
        param_debug_run = "${params.DebugRun}"
        //Job parameters
        sharedLibPath = "deploy/legionPipeline.groovy"
        ansibleHome =  "/opt/legion/deploy/ansible"
        ansibleVerbose = '-v'
        helmLocalSrc = 'false'
        cleanupContainerVersion = "latest"
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
        
        stage('Deploy Legion Enclave') {
            steps {
                script {
                    legion.ansibleDebugRunCheck(env.param_debug_run)
                    legion.authorizeJenkinsAgent()
                    legion.deployLegionEnclave()
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