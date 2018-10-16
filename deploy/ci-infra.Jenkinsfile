def legionVersion = "latest"

def notifyBuild(String buildStatus = 'STARTED') {
  // build status of null means successful
  buildStatus =  buildStatus ?: 'SUCCESSFUL'
 
  // Default values
  def colorName = 'RED'
  def colorCode = '#FF0000'
  def subject = "${buildStatus}: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'"
  def summary = "${subject} (${env.BUILD_URL})"
  def details = """<p>STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
    <p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>"""
 
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
 
  emailext (
      subject: subject,
      body: details,
      to: 'Aliaksandr_Semianets@epam.com',
      recipientProviders: [[$class: 'DevelopersRecipientProvider']]
    )
}

node {
    try {
        stage('Terminate Cluster if exists') {
            result = build job: params.TerminateClusterJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
            ]
        }

        stage('Create Cluster') {
            result = build job: params.CreateClusterJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    booleanParam(name: 'Skip_kops', value: false),
            ]
        }

        stage('Deploy Legion & run tests') {
            result = build job: params.DeployLegionJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    string(name: 'LegionVersion', value: legionVersion),
                    string(name: 'TestsTags', value: "infra"),
                    booleanParam(name: 'DeployLegion', value: true),
                    booleanParam(name: 'CreateJenkinsTests', value: true),
                    booleanParam(name: 'UseRegressionTests', value: true),
            ]
        }

        stage('Deploy Legion Enclave') {
            result = build job: params.DeployLegionEnclaveJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    string(name: 'LegionVersion', value: legionVersion),
                    string(name: 'EnclaveName', value: 'enclave-ci')
            ]
        }

        stage('Terminate Legion Enclave') {
            result = build job: params.TerminateLegionEnclaveJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    string(name: 'EnclaveName', value: 'enclave-ci')
            ]
        stage('Test') {
            print("${env.BUILD_NUMBER}")
        }

    }
    catch (e) {
        // If there was an exception thrown, the build failed
        currentBuild.result = "FAILED"
        throw e
    }
    finally {
        stage('Terminate Cluster') {
            result = build job: params.TerminateClusterJobName, propagate: true, wait: true, parameters: [
                [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
            ]
        notifyBuild(currentBuild.result)
    }

}