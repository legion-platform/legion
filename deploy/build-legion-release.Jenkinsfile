def TagAndUploadDockerImage(imageName) {
    sh """
    # Push stable image to local registry
    docker tag legion/${imageName}:${params.ReleaseVersion} ${params.DockerRegistry}/${imageName}:${params.ReleaseVersion}
    docker tag legion/${imageName}:${params.ReleaseVersion} ${params.DockerRegistry}/${imageName}:latest
    docker push ${params.DockerRegistry}/${imageName}:${params.ReleaseVersion}
    docker push ${params.DockerRegistry}/${imageName}:latest
    # Push stable image to DockerHub
    docker tag legion/${imageName}:${params.ReleaseVersion} ${params.DockerHubRegistry}/${imageName}:${params.ReleaseVersion}
    docker tag legion/${imageName}:${params.ReleaseVersion} ${params.DockerHubRegistry}/${imageName}:latest
    docker push ${params.DockerHubRegistry}/${imageName}:${params.ReleaseVersion}
    docker push ${params.DockerHubRegistry}/${imageName}:latest
    """
}

node {
    try {
        timestamps {
            stage('Checkout GIT'){
                checkout scm
            }

            stage('Install build dependencies'){
                sh '''
                sudo rm -rf .venv
                virtualenv .venv -p $(which python3.6)
                sudo chmod a+r -R .
                cd legion
                ../.venv/bin/pip install -r requirements/base.txt
                ../.venv/bin/pip install -r requirements/test.txt
                '''
            }

            parallel (
                'Build Python packages': {
                    sh '''
                    cd legion_test
                    ../.venv/bin/python3.6 setup.py sdist
                    ../.venv/bin/python3.6 setup.py develop
                    cd -
                    '''

                    print('Build and distributing legion_test')
                    sh """
                    sed -i -E "s/__version__.*/__version__ = \'${params.ReleaseVersion}\'/g" legion_test/legion_test/version.py
                    cd legion_test
                    ../.venv/bin/python3.6 setup.py sdist
                    ../.venv/bin/python3.6 setup.py sdist upload -r ${params.LocalPyPiDistributionTargetName}
                    ../.venv/bin/python3.6 setup.py develop
                    cd -
                    """

                    print('Build and distributing legion')
                    sh """
                    sed -i -E "s/__version__.*/__version__ = \'${params.ReleaseVersion}\'/g" legion/legion/version.py
                    cd legion
                    ../.venv/bin/python3.6 setup.py sdist
                    ../.venv/bin/python3.6 setup.py sdist upload -r ${params.LocalPyPiDistributionTargetName}
                    ../.venv/bin/python3.6 setup.py develop
                    cd -
                    """

                    print('Build and distributing legion_airflow')
                    sh """
                    sed -i -E "s/__version__.*/__version__ = \'${params.ReleaseVersion}\'/g" legion_airflow/legion_airflow/version.py
                    cd legion_airflow
                    ../.venv/bin/pip install -r requirements/base.txt
                    ../.venv/bin/pip install -r requirements/test.txt
                    ../.venv/bin/python3.6 setup.py sdist
                    ../.venv/bin/python3.6 setup.py sdist upload -r ${params.LocalPyPiDistributionTargetName}
                    ../.venv/bin/python3.6 setup.py develop
                    cd -
                    """
                }, 'Build docs': {
                    fullBuildNumber = env.BUILD_NUMBER
                    fullBuildNumber.padLeft(4, '0')

                    sh '''
                    cd legion
                    LEGION_VERSION="\$(../.venv/bin/python3.6 -c 'import legion; print(legion.__version__);')"
                    cd docs
                    sphinx-apidoc -f --private -o source/ ../legion/ -V "\$LEGION_VERSION"
                    sed -i "s/'1.0'/'\$LEGION_VERSION'/" source/conf.py
                    make html
                    find build/html -type f -name '*.html' | xargs sed -i -r 's/href="(.*)\\.md"/href="\\1.html"/'
                    cd ../../
                    '''

                    sh "cd legion && cp -rf docs/build/html/ \"${params.LocalDocumentationStorage}\$(../.venv/bin/python3.6 -c 'import legion; print(legion.__version__);')/\""
                }, 'Run Python code analyzers': {
                    sh '''
                    cd legion
                    ../.venv/bin/pycodestyle --show-source --show-pep8 legion
                    ../.venv/bin/pycodestyle --show-source --show-pep8 tests --ignore E402,E126,W503
                    ../.venv/bin/pydocstyle --source legion

                    export TERM="linux"
                    rm -f pylint.log
                    ../.venv/bin/pylint legion >> pylint.log || exit 0
                    ../.venv/bin/pylint tests >> pylint.log || exit 0
                    cd ..
                    '''

                    archiveArtifacts 'legion/pylint.log'
                    warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''

                    sh '''
                    cd legion_airflow
                    ../.venv/bin/pycodestyle legion_airflow
                    ../.venv/bin/pycodestyle tests
                    ../.venv/bin/pydocstyle legion_airflow

                    ../.venv/bin/pylint legion_airflow >> pylint.log || exit 0
                    ../.venv/bin/pylint tests >> pylint.log || exit 0
                    cd ..
                    '''
    
                    archiveArtifacts 'legion/pylint.log'
                    warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''

                    sh '''
                    cd legion_airflow
                    ../.venv/bin/pycodestyle legion_airflow
                    ../.venv/bin/pycodestyle tests
                    ../.venv/bin/pydocstyle legion_airflow

                    ../.venv/bin/pylint legion_airflow >> pylint.log || exit 0
                    ../.venv/bin/pylint tests >> pylint.log || exit 0
                    cd ..
                    '''

                    archiveArtifacts 'legion/pylint.log'
                    warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''

                    sh '''
                    cd legion_airflow
                    ../.venv/bin/pycodestyle legion_airflow
                    ../.venv/bin/pycodestyle tests
                    ../.venv/bin/pydocstyle legion_airflow

                    ../.venv/bin/pylint legion_airflow >> pylint.log || exit 0
                    ../.venv/bin/pylint tests >> pylint.log || exit 0
                    cd ..
                    '''

                    archiveArtifacts 'legion_airflow/pylint.log'
                    warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '',  excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[   parserName: 'PyLint', pattern: 'legion_airflow/pylint.log']], unHealthy: ''

                }, 'Build Jenkins plugin': {
                    sh """
                    mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml clean
                    mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${params.ReleaseVersion}
                    mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml install
                    """
                    archiveArtifacts 'k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi'
    
                    withCredentials([[
                         $class: 'UsernamePasswordMultiBinding',
                         credentialsId: 'nexus-local-repository',
                         usernameVariable: 'USERNAME',
                         passwordVariable: 'PASSWORD']]) {
                        sh """
                        curl -v -u $USERNAME:$PASSWORD \
                        --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                        ${params.JenkinsPluginsRepositoryStore}/${params.ReleaseVersion}/legion-jenkins-plugin.hpi
        
                        curl -v -u $USERNAME:$PASSWORD \
                        --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                        ${params.JenkinsPluginsRepositoryStore}/latest/legion-jenkins-plugin.hpi
                        """
                    }
                }
            )

            stage('Run Python tests') {
                    sh """
                    cd legion
                    VERBOSE=true ../.venv/bin/nosetests --with-coverage --cover-package legion --with-xunit --cover-html  --logging-level DEBUG -v || true
                    """
                    junit 'legion/nosetests.xml'
    
                    sh """
                    cd legion && cp -rf cover/ \"${params.LocalDocumentationStorage}\$(../.venv/bin/python3.6 -c 'import legion; print(legion.__version__);')-cover/\"
                    """
            }

            parallel (
                'Build Base Docker image': {
                    dockerCacheArg = (params.EnableDockerCache) ? '' : '--no-cache'
                    sh """
                    cd base-python-image
                    docker build $dockerCacheArg -t "legion/base-python-image:${params.ReleaseVersion}" .
                    """
                    TagAndUploadDockerImage("base-python-image")
                }, 'Build docs': {
                    fullBuildNumber = env.BUILD_NUMBER
                    fullBuildNumber.padLeft(4, '0')

                    sh '''
                    cd legion
                    LEGION_VERSION="\$(../.venv/bin/python3 -c 'import legion; print(legion.__version__);')"
                    cd docs
                    sphinx-apidoc -f --private -o source/ ../legion/ -V "\$LEGION_VERSION"
                    sed -i "s/'1.0'/'\$LEGION_VERSION'/" source/conf.py
                    make html
                    find build/html -type f -name '*.html' | xargs sed -i -r 's/href="(.*)\\.md"/href="\\1.html"/'
                    cd ../../
                    '''

                    sh "cd legion && cp -rf docs/build/html/ \"${params.LocalDocumentationStorage}\$(../.venv/bin/python3 -c 'import legion; print(legion.__version__);')/\""
                }
            )
            parallel (
                'Build Grafana Docker image': {
                    sh """
                    cd k8s/grafana
                    docker build $dockerCacheArg --build-arg pip_extra_index_params=" --extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${params.ReleaseVersion}" -t legion/k8s-grafana:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("k8s-grafana")
                }, 'Build Edge Docker image': {
                    sh """
                    rm -rf k8s/edge/static/docs
                    cp -rf legion/docs/build/html/ k8s/edge/static/docs/
                    build_time=`date -u +'%d.%m.%Y %H:%M:%S'`
                    sed -i "s/{VERSION}/${params.ReleaseVersion}/" k8s/edge/static/index.html

                    cd k8s/edge
                    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${params.ReleaseVersion}" -t legion/k8s-edge:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("k8s-edge")
                }, 'Build Jenkins Docker image': {
                    sh """
                    cd k8s/jenkins
                    docker build $dockerCacheArg --build-arg version="${params.ReleaseVersion}" --build-arg jenkins_plugin_version="${params.ReleaseVersion}" --build-arg jenkins_plugin_server="${params.JenkinsPluginsRepository}" -t legion/k8s-jenkins:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("k8s-jenkins")
                }, 'Build Bare model 1': {
                    sh """
                    cd k8s/test-bare-model-api/model-1
                    docker build $dockerCacheArg --build-arg version="${params.ReleaseVersion}" -t legion/test-bare-model-api-model-1:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("test-bare-model-api-model-1")
                }, 'Build Bare model 2': {
                    sh """
                    cd k8s/test-bare-model-api/model-2
                    docker build $dockerCacheArg --build-arg version="${params.ReleaseVersion}" -t legion/test-bare-model-api-model-2:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("test-bare-model-api-model-2")
                }, 'Build Edi Docker image': {
                    sh """
                    cd k8s/edi
                    docker build $dockerCacheArg --build-arg version="${params.ReleaseVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${params.ReleaseVersion}" --build-arg source_image="legion/base-python-image" -t legion/k8s-edi:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("k8s-edi")
                }, 'Build Airflow Docker image': {
                    sh """
                    cd k8s/airflow
                    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${params.ReleaseVersion}" -t legion/k8s-airflow:${params.ReleaseVersion} .
                    """
                    TagAndUploadDockerImage("k8s-airflow")
                }, 'Upload Legion package to PyPi': {
                    print('Upload Legion package to Pypi repository')
                    if (params.UploadLegionPackage){
                        sh """
                        twine upload -r ${params.PyPiDistributionTargetName} legion/dist/legion-${params.ReleaseVersion}.*
                        """
                    } else {
                        print("Skipping package upload")
                    }
                }
            )

            stage('Set GIT release Tag'){
                if (params.PushGitTag){
                print('Set Release tag')
                sh """
                if [ `git tag |grep ${params.ReleaseVersion}` ]; then
                    git tag -d ${params.ReleaseVersion}
                    git push origin :refs/tags/${params.ReleaseVersion}
                fi
                git tag -a ${params.ReleaseVersion}  -m "Release ${params.ReleaseVersion}"
                git push origin :refs/tags/${params.ReleaseVersion}
                """
                } else {
                    print("Skipping release git tag push")
                }
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
                    sh """
                    sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                    git commit -a -m "Update Legion version to ${nextVersion}" && git push origin develop
                    """
                }
                else {
                    print("Skipping version string update")
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
        print(currentBuild.result)
    }

    print("Release version ${params.ReleaseVersion}")
}

