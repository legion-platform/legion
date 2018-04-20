node {
    try{
        stage('Checkout GIT'){
            checkout scm
        }
        
        stage('Install tools package'){
                sh '''
                sudo rm -rf .venv
                virtualenv .venv
    
                cd legion_test
                ../.venv/bin/python3 setup.py develop
                '''
        }

        stage('Create Kubernetes Cluster') {
            dir('deploy/ansible'){
                withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
                    withAWS(credentials: 'kops') {
                        wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                            ansiblePlaybook(
                                playbook: 'create-cluster.yml',
                                extras: ' --extra-vars "profile=${Profile}"',
                                colorized: true
                            )
                        }
                    }
                }
            }
        }

def notifyBuild(String buildStatus = 'STARTED') {
    // build status of null means successful
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    // Default values
    def colorName = 'RED'
    def colorCode = '#FF0000'
    def subject = "Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}*"
    def summary = "@channel ${subject} \n<${env.BUILD_URL}|Open>"

    // Override default values based on build status
    if (buildStatus == 'STARTED') {
        color = 'YELLOW'
        colorCode = '#FFFF00'
    } else if (buildStatus == 'SUCCESSFUL') {
        color = 'GREEN'
        colorCode = '#00FF00'
    } else {
        color = 'RED'
        colorCode = '#FF0000'
    }

    // Send notifications
    if (params.SLACK_NOTIFICATION_ENABLED){
        slackSend (color: colorCode, message: summary)
    }
}