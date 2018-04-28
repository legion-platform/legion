def baseDomain = ''
def targetBranch = params.GitBranch

node {
    try{
        stage('Checkout GIT'){
            def scmVars = checkout scm
            targetBranch = scmVars.GIT_COMMIT
        }
        
        stage('Install tools package'){
                sh '''
                sudo rm -rf .venv
                virtualenv .venv
    
                cd legion_test
                ../.venv/bin/python3 setup.py develop
                '''
        }

        
        stage('Deploy Legion') {
            if (params.DeployLegion){
                dir('deploy/ansible'){
                    withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
                        withAWS(credentials: 'kops') {
                            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                                ansiblePlaybook(
                                    playbook: 'deploy-legion.yml',
                                    extras: ' --extra-vars "profile=${Profile} base_version=${BaseVersion}  local_version=${LocalVersion}"',
                                    colorized: true
                                )
                            }
                        }
                    }
                }
            }
            else {
                    print("Skipping Legion Deployment")
            }
        }
    
        stage('Domain'){
            baseDomain = params.Profile
        }
        
        stage('Create jenkins jobs'){
            if (params.CreateJenkinsTests){
                sh """
                cd legion_test
                ../.venv/bin/pip install -r requirements/base.txt
                ../.venv/bin/pip install -r requirements/test.txt
                ../.venv/bin/python setup.py develop
                cd ..

                .venv/bin/create_example_jobs \
                "https://jenkins.${baseDomain}" \
                examples \
                . \
                "git@github.com:epam/legion.git" \
                ${targetBranch} \
                --connection-timeout 600 \
                --git-root-key "legion-root-key" \
                --model-host "" \
                --dynamic-model-prefix "DYNAMIC MODEL"
                """
            }
            else {
                println('Skipping Jenkins Jobs creation')
            }
        }

        stage('Run robot tests'){
            if (params.UseRegressionTests){
                sh '''
                cd legion_test
                ../.venv/bin/pip install -r requirements/base.txt
                ../.venv/bin/pip install -r requirements/test.txt
                ../.venv/bin/python setup.py develop

                cd ../tests
                ../.venv/bin/pip install yq

                PATH_TO_PROFILE="../deploy/profiles/$Profile.yml"
                CLUSTER_NAME=$(yq -r .cluster_name $PATH_TO_PROFILE)
                CLUSTER_STATE_STORE=$(yq -r .state_store $PATH_TO_PROFILE)
                echo "Loading kubectl config from $CLUSTER_STATE_STORE for cluster $CLUSTER_NAME"

                kops export kubecfg --name $CLUSTER_NAME --state $CLUSTER_STATE_STORE

                DISPLAY=:99 PROFILE=$Profile ../.venv/bin/python3 -m robot.run *.robot || true
                '''
                step([
                    $class : 'RobotPublisher',
                    outputPath : 'tests/',
                    outputFileName : "*.xml",
                    disableArchiveOutput : false,
                    passThreshold : 100,
                    unstableThreshold: 95.0,
                    onlyCritical : true,
                    otherFiles : "*.png",
                ])
            }
            else {
                println('Skipped due to UseRegressionTests property')
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