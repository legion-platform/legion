def TagAndUploadDockerImage(imageName) {
    def releaseImage = "${params.DockerRegistry}/${imageName}:${baseVersion}-${localVersion}"
    sh """
    # Make sure release image exists locally
    docker pull ${releaseImage}
    # Push stable image to local registry
    docker tag ${releaseImage} ${params.DockerRegistry}/${imageName}:${baseVersion}
    docker tag ${releaseImage} ${params.DockerRegistry}/${imageName}:latest
    docker push ${params.DockerRegistry}/${imageName}:${baseVersion}
    docker push ${params.DockerRegistry}/${imageName}:latest
    # Push stable image to DockerHub
    docker tag ${releaseImage} ${params.DockerHubRegistry}/${imageName}:${baseVersion}
    docker tag ${releaseImage} ${params.DockerHubRegistry}/${imageName}:latest
    docker push ${params.DockerHubRegistry}/${imageName}:${baseVersion}
    docker push ${params.DockerHubRegistry}/${imageName}:latest
    """
}

node {

    baseVersion = ${params.BuildVersion}.split("-").first()
    localVersion = ${params.BuildVersion}.split("-").last()
    releaseCommit = localVersion.split("\\.").last()
    
    try{

        print("Propogate ${params.BuildVersion} as stable ${baseVersion} release")

        stage('Upload Legion python package to PyPi'){
            print('Upload Legion package to Pypi repository')
            sh """
            wget ${params.NexusPypiUrl}/repository/pypi-hosted/packages/legion/${baseVersion}+${localVersion}/legion-${baseVersion}+${localVersion}.tar.gz -o legion-${baseVersion}.tar.gz
            twine upload -r ${params.PypiRepo} legion-${baseVersion}.tar.gz && rm legion-${baseVersion}.tar.gz
            """
        }
    
        stage('Tag Docker images'){
            print('Push Docker images to DockerHub repository')
            TagAndUploadDockerImage("base-python-image")
            TagAndUploadDockerImage("k8s-grafana")
            TagAndUploadDockerImage("k8s-edi")
            TagAndUploadDockerImage("k8s-edge")
            TagAndUploadDockerImage("test-bare-model-api-model-1")
            TagAndUploadDockerImage("test-bare-model-api-model-2")
            TagAndUploadDockerImage("k8s-airflow")
        }

        stage('Set GIT release Tag'){
            print('Set Release tag')
            checkout scm
            sh '''
            git checkout ${release.Commit}
            if [ `git tag |grep ${ReleaseTag}"` ]; then
                git tag -d ${ReleaseTag} && git push origin :refs/tags/${ReleaseTag}
            git tag -a ${ReleaseTag}  -m "Release ${ReleaseTag}"
            git push origin :refs/tags/${ReleaseTag}
            '''
        }
        
        stage('Update Legion version string'){
            if (params.UpdateVersionString){
                print('Update Legion package version string')
                def nextVersion
                if (${params.NextVersion})
                    nextVersion = (${params.NextVersion}
                else:
                    def ver_parsed = ${baseVersion}.split("\\.")
                    ver_parsed[1] = ver_parsed[1].toInteger() + 1
                    def nextVersion = ver_parsed.join(".")

                sh '''
                git checkout develop && git pull -r origin develop
                sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                git commit -a -m "Update Legion version to ${nextVersion}" && git push origin develop
                '''
            }
            else {
                print("Skipping version string update")
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
