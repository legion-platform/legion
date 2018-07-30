def TagAndUploadDockerImage(imageName) {
    def releaseImage = "${params.DockerRegistry}/legion/${imageName}:${Globals.baseVersion}-${Globals.localVersion}"
    sh """
    # Make sure release image exists locally
    docker pull ${releaseImage}
    # Push stable image to local registry
    docker tag ${releaseImage} ${params.DockerRegistry}/legion/${imageName}:${Globals.baseVersion}
    docker tag ${releaseImage} ${params.DockerRegistry}/legion/${imageName}:latest
    docker push ${params.DockerRegistry}/legion/${imageName}:${Globals.baseVersion}
    docker push ${params.DockerRegistry}/legion/${imageName}:latest
    # Push stable image to DockerHub
    docker tag ${releaseImage} ${params.DockerHubRegistry}/legion-platform/${imageName}:${Globals.baseVersion}
    docker tag ${releaseImage} ${params.DockerHubRegistry}/legion-platform/${imageName}:latest
    docker push ${params.DockerHubRegistry}/legion-platform/${imageName}:${Globals.baseVersion}
    docker push ${params.DockerRegistry}/legion/${imageName}:latest
    """
}

node {
    def legion

    baseVersion = ${params.buildVersion}.split("-").first()
    localVersion = ${params.buildVersion}.split("-").last()
    releaseCommit = localVersion.split("\\.").last()
    
    try{

        stage('Upload Legion python package'){
            print('Upload Legion package to Pypi repository')
            sh """
            wget https://nexus.cc.epm.kharlamov.biz/repository/pypi-hosted/packages/legion/${baseVersion}+${localVersion}/legion-${baseVersion}+${localVersion}.tar.gz -o legion-${baseVersion}.tar.gz
            twine upload -r pypi-org legion-${baseVersion}.tar.gz && rm legion-${baseVersion}.tar.gz
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
            git tag -a ${ReleaseTag}  -m "Release ${ReleaseTag}"
            git push origin ${ReleaseTag}
            '''
        }

        stage('Update Legion version'){
            print('Update Legion package version string')
            def nextVersion
            if (${params.nextVersion})
                nextVersino = (${params.nextVersion}
            else:
                def ver_parsed = ${baseVersion}.split("\\.")
                ver_parsed[1] = ver_parsed[1].toInteger() + 1
                nextVersion = ver_parsed.join(".")

            sh '''
            git checkout develop && git pull -r origin develop
            sed -i -E "s/__version__.*/__version__ = \'${newVersion}\'/g" legion/legion/version.py
            git commit -a -m "Update Legion version to ${newVersion}" && git push origin develop
            '''

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
