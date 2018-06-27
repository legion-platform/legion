node {
    def legion
    try{
        stage('Checkout GIT'){
            def scmVars = checkout scm
            targetBranch = scmVars.GIT_COMMIT

            legion = load 'legionPipeline.groovy'

            legion.buildDescription()
        }

        legion = load 'deploy/legionPipeline.groovy'

        legion.buildDescription()
        
        stage('Deploy Legion Enclave') {
            legion.deployLegionEnclave()
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
