node {
    try {
    	stage('Checkout GIT'){
            checkout scm
        }
    	stage('Terraforming'){
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
                    
                    sh "set +e; terraform plan -var-file=\"../profiles/\$PROFILE.tfvars\" -destroy -out=plan.out -detailed-exitcode; echo \$? > status"
                    
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
                    
                    if (apply) {
                        unstash 'plan'
                        
                        if (fileExists("status.apply")) {
                            sh "rm status.apply"
                        }
                        
                        sh "set +e; terraform destroy -var-file=\"../profiles/\$PROFILE.tfvars\" -force; echo \$? > status.apply"
                        
                        def applyExitCode = readFile('status.apply').trim()
                        if (applyExitCode == "0") {
                            if (params.SLACK_NOTIFICATION_ENABLED){
                                slackSend color: 'good', message: "Destroyed ${env.JOB_NAME} - ${env.BUILD_NUMBER}"    
                            }
                        } else {
                            if (params.SLACK_NOTIFICATION_ENABLED){
                                slackSend color: 'danger', message: "Destroy Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
                            }
                            currentBuild.result = 'FAILURE'
                        }
                        
                    }
                    else {
                        print("Skipping apply process of terraform")
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