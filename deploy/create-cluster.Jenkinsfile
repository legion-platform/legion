def baseDomain = ''
def BASE_DOMAIN = false
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

        stage('Create Kubernetes Cluster') {
               dir('deploy/ansible'){
                   withAWS(credentials: 'kops') {
                       wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                           ansiblePlaybook(
                               playbook: 'create-cluster.yml --extra-vars "profile=${Profile}"',
                               colorized: true
                           )
                       }
                   }
                }

                archiveArtifacts 'deploy/ansible/helm.airflow.debug'
                archiveArtifacts 'deploy/ansible/helm.airflow.status'

                // load variables
                def map = [:]
                def envs = sh returnStdout: true, script: "cat deploy/ansible/output.ini"

                envs.split("\n").each {
                    kv = it.split('=', 2)
                    print "Loaded ${kv[0]} = ${kv[1]}"
                    map[kv[0]] = kv[1]
                }

                BASE_DOMAIN = map["BASE_DOMAIN"]

                print "Loaded base domain ${BASE_DOMAIN}"
                // \ load variables
        }

        stage('Domain'){
            if (BASE_DOMAIN){
                print("Using Domain from ansible stage: $BASE_DOMAIN")
                baseDomain = BASE_DOMAIN
            }
            else if (params.BASE_DOMAIN_OVERRIDE.length() > 0){
                print("Using domain from parameter: ${params.BASE_DOMAIN_OVERRIDE}")
                baseDomain = params.BASE_DOMAIN_OVERRIDE
            }
            else {
                error "Cannot detect domain for post-ansible jobs"
            }
        }

        stage('Create & check jenkins jobs'){
            if (params.CreateJenkinsTests){
                sh """
                .venv/bin/create_example_jobs \
                "http://jenkins.local.${baseDomain}" \
                examples \
                . \
                "git@github.com:epam/legion.git" \
                ${targetBranch} \
                --connection-timeout 600 \
                --git-root-key "legion-root-key" \
                --model-host "" \
                --dynamic-model-prefix "DYNAMIC MODEL"
                """

                if (params.RunJenkinsTests){
                    sh """
                    .venv/bin/check_jenkins_jobs \
                    --jenkins-url "http://jenkins.local.${baseDomain}" \
                    --jenkins-run-jobs-prefix "DYNAMIC MODEL" \
                    --connection-timeout 360 \
                    --run-sleep-sec 30 \
                    --run-timeout 1800 \
                    --jenkins-check-running-jobs \
                    --run-parameter "GitRepository=git@github.com:epam/legion.git" \
                    --run-parameter "GitBranch=${targetBranch}"
                    """

                }
                else {
                    println('Skipped due to RunModelTestsInAnotherJenkins property')
                }


            }
            else {
                print("Skipping Jenkins")
            }
        }

        stage('Run robot tests'){
            if (params.UseRegressionTests){
                sh '''
                cd tests
                ../.venv/bin/python3 -m robot.run --exitonfailure *.robot || true
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