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
                                extras: ' --extra-vars "profile=${Profile} skip_kops=${Skip_kops}"',
                                colorized: true
                            )
                        }
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

    def previousBuild = currentBuild.getPreviousBuild()
    def previousBuildResult = previousBuild != null ? previousBuild.result : null

    def currentBuildResultSuccessful = buildStatus == 'SUCCESSFUL' || buildStatus == 'SUCCESS'
    def previousBuildResultSuccessful = previousBuildResult == 'SUCCESSFUL' || previousBuildResult == 'SUCCESS'

    def masterOrDevelopBuild = params.GitBranch == 'origin/develop' || params.GitBranch == 'origin/master'

    print("NOW SUCCESSFUL: ${currentBuildResultSuccessful}, PREV SUCCESSFUL: ${previousBuildResultSuccessful}, MASTER OR DEV: ${masterOrDevelopBuild}")

    if (!masterOrDevelopBuild)
        return

    // Skip green -> green
    if (currentBuildResultSuccessful && previousBuildResultSuccessful)
        return

    // Default values
    def colorCode = '#FF0000'
    def summary = """\
    @here Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}* (previous: ${previousBuildResult})
    branch *${params.GitBranch}*
    profile *<https://${params.Profile}|${params.Profile}>*
    skip kops *${params.Skip_kops}*
    Manage: <${env.BUILD_URL}|Open>, <${env.BUILD_URL}/consoleFull|Full logs>, <${env.BUILD_URL}/parameters/|Parameters>
    """.stripIndent()

    // Override default values based on build status
    if (buildStatus == 'STARTED') {
        colorCode = '#FFFF00'
    } else if (buildStatus == 'SUCCESSFUL') {
        colorCode = '#00FF00'
    } else {
        colorCode = '#FF0000'
    }

    slackSend (color: colorCode, message: summary)
}