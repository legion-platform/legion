def ansibleIp = ''
def baseDomain = ''
def BASE_DOMAIN = false
def ip = ''

node {
    try {
        stage('Checkout GIT'){
            checkout scm
        }
    	stage('Terraforming'){
    	    if (params.USE_TERRAFORM){
        	    dir('deploy/terraform'){
        	        wrap([$class: 'AnsiColorBuildWrapper', colorMapName: 'xterm']) {
                	    sh "terraform --version"
                	    if (fileExists("status")) {
                            sh "rm status"
                        }
                        
                        if (fileExists(".terraform/terraform.tfstate")){
                            sh "rm .terraform/terraform.tfstate"
                        }
						
						if (!fileExists("../profiles/" + params.PROFILE + ".tfvars")){
							sh "pwd"
							sh "ls -lah ../profiles/"
							error "Cannot found profile ${params.PROFILE} files"
						}
                        
                        sh '''
                        terraform init \
                            -var-file="../profiles/$PROFILE.tfvars" \
                            -backend-config="bucket=$TF_VAR_STATE_S3_BUCKET" \
                            -backend-config="key=$TF_VAR_STATE_S3_KEY.$PROFILE" \
                            -backend-config="region=$TF_VAR_STATE_S3_REGION"
                        '''
                        
                        sh "set +e; terraform plan -var-file=\"../profiles/\$PROFILE.tfvars\" -out=plan.out -detailed-exitcode; echo \$? > status"
                        
                        def exitCode = readFile('status').trim()
                        def apply = false
                        echo "Terraform Plan Exit Code: ${exitCode}"
                        
                        if (exitCode == "0") {
                            currentBuild.result = 'SUCCESS'
                        }
                        if (exitCode == "1") {
                            if (params.SLACK_NOTIFICATION_ENABLED){
                                slackSend color: '#0080ff', message: "Plan Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
                            }
                            currentBuild.result = 'FAILURE'
                        }
                        if (exitCode == "2") {
                            stash name: "plan", includes: "plan.out"
                            
                            if (!params.TF_AUTO_APPLY){
                                if (params.SLACK_NOTIFICATION_ENABLED){
                                    slackSend color: 'good', message: "Plan Awaiting Approval: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
                                }
                                try {
                                    input message: 'Apply Plan?', ok: 'Apply'
                                    apply = true
                                } catch (err) {
                                    if (params.SLACK_NOTIFICATION_ENABLED){
                                        slackSend color: 'warning', message: "Plan Discarded: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
                                    }
                                    apply = false
                                    currentBuild.result = 'UNSTABLE'
                                }
                            }
                            else {
                                apply = true
                            }
                        }
                        
                        if (apply) {
                            unstash 'plan'
                            
                            if (fileExists("status.apply")) {
                                sh "rm status.apply"
                            }
                            
                            sh 'set +e; terraform apply plan.out; echo \$? > status.apply'
                            
                            def applyExitCode = readFile('status.apply').trim()
                            if (applyExitCode == "0") {
                                if (params.SLACK_NOTIFICATION_ENABLED){
                                    slackSend color: 'good', message: "Changes Applied ${env.JOB_NAME} - ${env.BUILD_NUMBER}"    
                                }
                            } else {
                                if (params.SLACK_NOTIFICATION_ENABLED){
                                    slackSend color: 'danger', message: "Apply Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
                                }
                                currentBuild.result = 'FAILURE'
                            }
                            
                            ansibleIp = sh(returnStdout: true, script: "terraform output -json private_ip | jq '.value'").trim().replaceAll("\"", "")
                            
                            print("Terra IP: $ansibleIp")
                            
                        }
                        else {
                            print("Skipping apply process of terraform")
                        }
                    }
                }
            }
            else {
                print("Skipping terraform")
            }
        }
        stage('IP'){

            if (ansibleIp.length() > 0){
                print("Using IP from terraform stage: $ansibleIp")
                ip = ansibleIp
            }
            else if (params.ANSIBLE_SPECIFIC_IP.length() > 0){
                print("Using IP from parameter: ${params.ANSIBLE_SPECIFIC_IP}")
                ip = params.ANSIBLE_SPECIFIC_IP
            }
            else {
                error "Cannot detect IP for ansible"
            }
        }
        stage('Ansible'){
            if (params.USE_ANSIBLE){
                sh """
                ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook \
                -u ${params.TF_VAR_SSH_USER} \
                -e "ansible_ssh_user=${params.TF_VAR_SSH_USER}" \
                --private-key "${params.TF_VAR_SSH_KEY}" -i "$ip," deploy/ansible/site.yml
                """

                // Loading result values from
                load "deploy/ansible/output.groovy"
            }
            else {
                print("Skipping ansible")
            }
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
                create_example_jobs \
                "http://jenkins.local.${baseDomain}" \
                examples \
                . \
                "git@github.com:akharlamov/drun-root.git" \
                ${params.GitBranch} \
                --git-root-key "legion-root-key" \
                --model-host "" \
                --dynamic-model-prefix "DYNAMIC MODEL"
                """

                if (params.RunJenkinsTests){
                    sh """
                    check_jenkins_jobs \
                    --jenkins-url "http://jenkins.local.${baseDomain}" \
                    --jenkins-run-jobs-prefix "DYNAMIC MODEL" \
                    --connection-timeout 360 \
                    --run-sleep-sec 30 \
                    --run-timeout 1800 \
                    --jenkins-check-running-jobs \
                    --run-parameter "GitRepository=git@github.com:akharlamov/drun-root.git" \
                    --run-parameter "GitBranch=${params.GitBranch}"
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