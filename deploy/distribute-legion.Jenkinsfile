def TagAndUploadDockerImage(imageName) {
    def releaseImage = "${params.DockerRegistry}/${imageName}:${params.ReleaseVersion}-${localVersion}"
    sh """
    # Make sure release image exists locally
    docker pull ${releaseImage}
    # Push stable image to local registry
    docker tag ${releaseImage} ${params.DockerRegistry}/${imageName}:${params.ReleaseVersion}
    docker tag ${releaseImage} ${params.DockerRegistry}/${imageName}:latest
    docker push ${params.DockerRegistry}/${imageName}:${params.ReleaseVersion}
    docker push ${params.DockerRegistry}/${imageName}:latest
    # Push stable image to DockerHub
    docker tag ${releaseImage} ${params.DockerHubRegistry}/${imageName}:${params.ReleaseVersion}
    docker tag ${releaseImage} ${params.DockerHubRegistry}/${imageName}:latest
    docker push ${params.DockerHubRegistry}/${imageName}:${params.ReleaseVersion}
    docker push ${params.DockerHubRegistry}/${imageName}:latest
    """
}

node {

    try{

        print("Build and distribute ${params.ReleaseVersion}")

        stage('Upload Legion python package to PyPi'){
            print('Upload Legion package to Pypi repository')
            sh """
            echo "Replace version string for Legion package"
            sed -i -E "s/__version__.*/__version__ = \'${params.ReleaseVersion}\'/g" legion/legion/version.py
            echo "Build Legion package"
            ../.venv/bin/python3.6 setup.py sdist
            echo "Upload package to PyPi"
            twine upload -r ${params.PypiRepo} dist/legion-${params.ReleaseVersion}.tar.gz && rm dist/legion-${params.ReleaseVersion}.tar.gz
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
            sh '''
            if [ `git tag |grep ${params.ReleaseVersion}"` ]; then
                git tag -d ${params.ReleaseVersion} && git push origin :refs/tags/${params.ReleaseVersion}
            git tag -a ${params.ReleaseVersion}  -m "Release ${params.ReleaseVersion}"
            git push origin :refs/tags/${params.ReleaseVersion}
            '''
        }
        
        stage('Update Legion version string'){
            if (params.UpdateVersionString){
                print('Update Legion package version string')
                def nextVersion
                if (params.NextVersion){
                    nextVersion = params.NextVersion
                } else {
                    def ver_parsed = params.ReleaseVersion.split("\\.")
                    ver_parsed[1] = ver_parsed[1].toInteger() + 1
                    nextVersion = ver_parsed.join(".")
                }
                sh '''
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
        print(currentBuild.result)
    }
}
