class Globals {
    static String rootCommit = null
    static String buildVersion = null
}

def UploadDockerImageLocal(imageName) {
    sh """
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    docker push ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    """
}

def UploadDockerImagePublic(imageName) {
    sh """
    # Push stable image to local registry
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerRegistry}/${imageName}:latest
    docker push ${params.DockerRegistry}/${imageName}:${Globals.buildVersion}
    docker push ${params.DockerRegistry}/${imageName}:latest
    # Push stable image to DockerHub
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerHubRegistry}/${imageName}:${Globals.buildVersion}
    docker tag legion/${imageName}:${Globals.buildVersion} ${params.DockerHubRegistry}/${imageName}:latest
    docker push ${params.DockerHubRegistry}/${imageName}:${Globals.buildVersion}
    docker push ${params.DockerHubRegistry}/${imageName}:latest
    """
}

def UploadDockerImage(imageName) {
    if (params.StableRelease) {
         UploadDockerImagePublic(imageName)
    } else {
        UploadDockerImageLocal(imageName)
    }
}


node {
    try {
        timestamps {
            stage('Checkout GIT'){
                checkout scm
                Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                Globals.rootCommit = Globals.rootCommit.trim()
            }

            stage('Install build dependencies'){
                sh '''
                sudo rm -rf .venv
                virtualenv .venv -p $(which python3.6)
                sudo chmod a+r -R .
                cd legion
                ../.venv/bin/pip install -r requirements/base.txt
                ../.venv/bin/pip install -r requirements/test.txt
                cd -
                cd legion_test
                ../.venv/bin/python3.6 setup.py develop
                '''
            }

            stage('Set Legion build version'){
                if (params.StableRelease) {
                    if (params.ReleaseVersion){
                        Globals.buildVersion = sh returnStdout: true, script: ".venv/bin/update_version_id --build-version=${params.ReleaseVersion} legion/legion/version.py"
                    } else {
                        print('Error: ReleaseVersion parameter must be specified for stable release')
                        exit 1
                    }
                } else {
                    Globals.buildVersion = sh returnStdout: true, script: ".venv/bin/update_version_id legion/legion/version.py"
                }
                Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                print("Build version " + Globals.buildVersion)
                print('Building shared artifact')
                envFile = 'file.env'
                sh """
                rm -f $envFile
                touch $envFile
                echo "LEGION_VERSION=${Globals.buildVersion}" >> $envFile
                """
                archiveArtifacts envFile
            }

            parallel (
                'Build Python packages': {

                    print('Build legion_test')
                    sh """
                    cp legion/legion/version.py legion_test/legion_test/version.py
                    cd legion_test
                    ../.venv/bin/python3.6 setup.py sdist 
                    ../.venv/bin/python3.6 setup.py bdist_wheel
                    ../.venv/bin/python3.6 setup.py develop
                    """

                    print('Build legion')
                    sh """
                    cd legion
                    ../.venv/bin/python3.6 setup.py sdist 
                    ../.venv/bin/python3.6 setup.py bdist_wheel
                    ../.venv/bin/python3.6 setup.py develop
                    """

                    print('Build legion_airflow')
                    sh """
                    cp legion/legion/version.py legion_airflow/legion_airflow/version.py
                    cd legion_airflow
                    ../.venv/bin/pip install -r requirements/base.txt
                    ../.venv/bin/pip install -r requirements/test.txt
                    ../.venv/bin/python3.6 setup.py sdist 
                    ../.venv/bin/python3.6 setup.py bdist_wheel
                    ../.venv/bin/python3.6 setup.py develop
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
                    mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${Globals.buildVersion}
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
                        ${params.JenkinsPluginsRepositoryStore}/${Globals.buildVersion}/legion-jenkins-plugin.hpi
                        """
        
                        if (params.StableRelease){
                            sh """
                            curl -v -u $USERNAME:$PASSWORD \
                            --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                            ${params.JenkinsPluginsRepositoryStore}/latest/legion-jenkins-plugin.hpi
                            """
                        }
                    }
                }
            )
            
            parallel(
                'Build Base Docker image':{
                    sh """
                    cd base-python-image
                    docker build -t "legion/base-python-image:${Globals.buildVersion}" .
                    """
                    UploadDockerImage('base-python-image')
                }, 'Upload Legion to local PyPi repo':{
                    sh """
                    twine upload -r ${params.LocalPyPiDistributionTargetName} legion/dist/legion-${Globals.buildVersion}.*
                    twine upload -r ${params.LocalPyPiDistributionTargetName} legion_airflow/dist/legion_airflow-${Globals.buildVersion}.*
                    twine upload -r ${params.LocalPyPiDistributionTargetName} legion_test/dist/legion_test-${Globals.buildVersion}.*
                    """
                }
            )

            parallel (
                'Build Grafana Docker image': {
                    sh """
                    cd k8s/grafana
                    docker build --build-arg pip_extra_index_params=" --extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-grafana:${Globals.buildVersion} .
                    """
                }, 'Build Edge Docker image': {
                    sh """
                    rm -rf k8s/edge/static/docs
                    cp -rf legion/docs/build/html/ k8s/edge/static/docs/
                    build_time=`date -u +'%d.%m.%Y %H:%M:%S'`
                    sed -i "s/{VERSION}/${Globals.buildVersion}/" k8s/edge/static/index.html
                    sed -i "s/{COMMIT}/${Globals.rootCommit}/" k8s/edge/static/index.html
                    sed -i "s/{BUILD_INFO}/#${env.BUILD_NUMBER} \$build_time UTC/" k8s/edge/static/index.html

                    cd k8s/edge
                    docker build --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edge:${Globals.buildVersion} .
                    """
                }, 'Build Jenkins Docker image': {
                    sh """
                    cd k8s/jenkins
                    docker build --build-arg version="${Globals.buildVersion}" --build-arg jenkins_plugin_version="${Globals.buildVersion}" --build-arg jenkins_plugin_server="${params.JenkinsPluginsRepository}" -t legion/k8s-jenkins:${Globals.buildVersion} .
                    """
                }, 'Build Bare model 1': {
                    sh """
                    cd k8s/test-bare-model-api/model-1
                    docker build --build-arg version="${Globals.buildVersion}" -t legion/test-bare-model-api-model-1:${Globals.buildVersion} .
                    """
                }, 'Build Bare model 2': {
                    sh """
                    cd k8s/test-bare-model-api/model-2
                    docker build --build-arg version="${Globals.buildVersion}" -t legion/test-bare-model-api-model-2:${Globals.buildVersion} .
                    """
                }, 'Build Edi Docker image': {
                    sh """
                    cd k8s/edi
                    docker build --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-edi:${Globals.buildVersion} .
                    """
                    
                }, 'Build Airflow Docker image': {
                    sh """
                    cd k8s/airflow
                    docker build --build-arg version="${Globals.buildVersion}" --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.buildVersion}" -t legion/k8s-airflow:${Globals.buildVersion} .
                    """
                }, 'Run Python tests': {
                    sh """
                    cd legion
                    VERBOSE=true BASE_IMAGE_VERSION="${Globals.buildVersion}" ../.venv/bin/nosetests --with-coverage --cover-package legion --with-xunit --cover-html  --logging-level DEBUG -v || true
                    """
                    junit 'legion/nosetests.xml'
    
                    sh """
                    cd legion && cp -rf cover/ \"${params.LocalDocumentationStorage}\$(../.venv/bin/python3.6 -c 'import legion; print(legion.__version__);')-cover/\"
                    """
                }
            )
            parallel (
                'Upload Grafana Docker Image':{
                    UploadDockerImage('k8s-grafana')
                }, 'Upload Edge Docker Image':{
                    UploadDockerImage('k8s-edge')
                }, 'Upload Jenkins Docker image': {
                    UploadDockerImage('k8s-jenkins')
                }, 'Upload Bare model 1': {
                    UploadDockerImage('test-bare-model-api-model-1')
                }, 'Upload Bare model 2': {
                    UploadDockerImage('test-bare-model-api-model-2')
                }, 'Upload Edi Docker image': {
                    UploadDockerImage('k8s-edi')
                }, 'Upload Airflow Docker image': {
                    UploadDockerImage('k8s-airflow')
                }, 'Upload Legion to PyPi repo': {
                    if (params.UploadLegionPackage){
                        sh """
                        twine upload -r ${params.PyPiDistributionTargetName} legion/dist/legion-${Globals.buildVersion}.*
                        """
                    } else {
                        print("Skipping package upload")
                    }
                }
            )

            if (params.StableRelease) {
                stage('Set GIT release Tag'){
                    if (params.PushGitTag){
                        print('Set Release tag')
                        sh """
                        if [ `git tag |grep ${params.ReleaseVersion}` ]; then
                            echo 'Remove existing git tag'
                            git tag -d ${params.ReleaseVersion}
                            git push origin :refs/tags/${params.ReleaseVersion}
                        fi
                        git tag ${params.ReleaseVersion}
                        git push origin ${params.ReleaseVersion}
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
                        git reset --hard
                        git checkout -b feat/${nextVersion}-version-bump
                        sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                        git commit -a -m "Update Legion version to ${nextVersion}" && git push -f origin feat/${nextVersion}-version-bump
                        """
                    }
                    else {
                        print("Skipping version string update")
                    }
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
        notifyBuild(currentBuild.result)
    }

    print("Build version ${Globals.buildVersion}")
}



def notifyBuild(String buildStatus = 'STARTED') {
    // build status of null means successful
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    def previousBuild = currentBuild.getPreviousBuild()
    def previousBuildResult = previousBuild != null ? previousBuild.result : null

    def currentBuildResultSuccessful = buildStatus == 'SUCCESSFUL' || buildStatus == 'SUCCESS'
    def previousBuildResultSuccessful = previousBuildResult == 'SUCCESSFUL' || previousBuildResult == 'SUCCESS'

    def masterOrDevelopBuild = params.GitBranch == 'origin/develop' || params.GitBranch == 'origin/master'

    print("NOW SUCCESSFUL: ${currentBuildResultSuccessful}, PREV SUCCESSFUL: ${previousBuildResultSuccessful}, MASTER OR DEV: ${masterOrDevelopBuild}")

    if (!masterOrDevelopBuild)
        return

    // Skip green -> green
    if (currentBuildResultSuccessful && previousBuildResultSuccessful)
        return

    // Default values
    def colorCode = '#FF0000'
    def summary = """\
    @here Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}* (previous: ${previousBuildResult})
    branch *${params.GitBranch}*
    commit *${Globals.rootCommit}*
    version *${Globals.buildVersion}*
    Manage: <${env.BUILD_URL}|Open>, <${env.BUILD_URL}/consoleFull|Full logs>, <${env.BUILD_URL}/parameters/|Parameters>
    """.stripIndent()

    // Override default values based on build status
    if (buildStatus == 'STARTED') {
        colorCode = '#FFFF00'
    } else if (buildStatus == 'SUCCESSFUL') {
        colorCode = '#00FF00'
    } else {
        colorCode = '#FF0000'
    }

    slackSend (color: colorCode, message: summary)
}
