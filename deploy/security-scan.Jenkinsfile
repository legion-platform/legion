pipeline {
    agent any

    stages {
        stage('Checkout test for security issues') {
            steps {
                cleanWs()
                checkout scm
                script {
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"
                }
            }
        }
    }
    post {
        always {
            script {
                if (currentBuild.currentResult != 'SUCCESSFUL' && currentBuild.currentResult != 'SUCCESS'){
                    def subject = "Security issues on Legion branch ${env.BRANCH_NAME}"

                    def messageEmail = """\
                    There are some critical security issues on branch ${env.BRANCH_NAME}.

                    Links:
                    Run Information - ${env.BUILD_URL}
                    Full logs - ${env.BUILD_URL}consoleText
                    """.stripIndent()

                    def colorSlack = '#FF0000'
                    def messageSlack = """\
                    @channel SECURITY ISSUES DETECTED ON *${env.BRANCH_NAME}*!

                    There are some critical security issues on branch *${env.BRANCH_NAME}*.

                    _Links_: <${env.BUILD_URL}|Run Information>, <${env.BUILD_URL}consoleText|Full logs>
                    """.stripIndent()

                    print("Sending slack notification with color: ${colorSlack}. \nText:\n${messageSlack}")
                    slackSend (color: colorSlack, message: messageSlack)

                    print("Sending email notification with subject \"${subject}\" to ${env.DevTeamMailList}.\nText:\n${messageEmail}")
                    emailext (
                        subject: subject,
                        body: messageEmail,
                        to: "${env.DevTeamMailList}"
                    )

                }
            }
        }
    }
}