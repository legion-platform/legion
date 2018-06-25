node {
    def legion
    try {
        stage('Checkout GIT'){
            def scmVars = checkout scm
        }

        legion = load 'deploy/legionPipeline.groovy'

        legion.buildDescription()

        stage('Terminate Cluster') {
            legion.terminateCluster()
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