node {
    def legion
    try{
        stage('Checkout GIT'){
            checkout scm
        }

        legion = load 'deploy/legionPipeline.groovy'

        legion.buildDescription()
        
        stage('Create Kubernetes Cluster') {
            legion.createClusterDockerized()
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