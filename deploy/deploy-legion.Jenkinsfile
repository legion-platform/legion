node {
    def legion
    try{
        stage('Checkout GIT'){
            def scmVars = checkout scm
            targetBranch = scmVars.GIT_COMMIT
        }

        legion = load 'deploy/legionPipeline.groovy'

        legion.buildDescription()
        
        stage('Install tools package'){
            legion.installTools()
        }

        
        stage('Deploy Legion') {
            if (params.DeployLegion){
                legion.deployLegion()
            }
            else {
                print("Skipping Legion Deployment")
            }
        }
        
        stage('Create jenkins jobs'){
            if (params.CreateJenkinsTests){
                legion.createjenkinsJobs()
            }
            else {
                println('Skipping Jenkins Jobs creation')
            }
        }

        stage('Run robot tests'){
            if (params.UseRegressionTests){
                legion.runRobotTests()
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
        legion.notifyBuild(currentBuild.result)
    }
}