def targetBranch = params.GitBranch

node {
    try{
        stage('Checkout GIT'){
            def scmVars = checkout scm
            targetBranch = scmVars.GIT_COMMIT

            def legion = load 'deploy/legionPipeline.groovy'

            legion.buildDescription()
        }

        stage('Terminate Legion Enclave') {
            legion.terminateLegionEnclave()
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
