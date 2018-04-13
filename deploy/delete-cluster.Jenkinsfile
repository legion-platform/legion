def baseDomain = ''
def BASE_DOMAIN = false
def targetBranch = params.GitBranch

node {
    try {
        stage('Checkout GIT'){
            def scmVars = checkout scm
            targetBranch = scmVars.GIT_COMMIT
        }

        stage('Delete Cluster') {
            dir('deploy/ansible'){
                withAWS(credentials: 'kops') {
                    wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                        ansiblePlaybook(
                            playbook: 'delete-cluster.yml --extra-vars "profile=${Profile}"',
                            colorized: true
                        )
                    }
                }
            }
        }
    }
    catch (e) {
        // If there was an exception thrown, the build failed
        currentBuild.result = "FAILED"
        throw e
    } finally {
        // Success or failure, always send notifications
        notifyBuild(currentBuild.result)
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