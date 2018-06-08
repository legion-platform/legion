class Globals {
    static String rootCommit = null
    static String baseVersion = null
    static String localVersion = null
}

node {
    try {
        stage('Checkout GIT'){
            checkout scm
            Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed "s/\\(.*\\)/\\1/"'
            Globals.rootCommit = Globals.rootCommit.trim()
        }
        stage('Install build dependencies'){
            sh '''
            sudo rm -rf .venv
            virtualenv .venv -p $(which python3)
            sudo chmod a+r -R .
    	    cd legion
    	    ../.venv/bin/pip3 install -r requirements/base.txt
    	    ../.venv/bin/pip3 install -r requirements/test.txt
    	    '''
        }
        stage('Build Python packages') {
            sh '''
			cd legion_test
    		../.venv/bin/python3 setup.py sdist
    		../.venv/bin/python3 setup.py bdist_wheel
    		../.venv/bin/python3 setup.py develop
    		cd -
    		'''

            def version = sh returnStdout: true, script: '.venv/bin/update_version_id --extended-output legion/legion/version.py'
            print("Detected legion version:\n" + version)

            version = version.split("\n")
            Globals.baseVersion = version[1]
            Globals.localVersion = version[2]

            currentBuild.description = "${Globals.baseVersion} ${Globals.localVersion} ${params.GitBranch}"
            print("Base version " + Globals.baseVersion + " local version " + Globals.localVersion)

            print('Building shared artifact')
            envFile = 'file.env'
            sh """
            rm -f $envFile
            touch $envFile
            echo "BASE_VERSION=${Globals.baseVersion}" >> $envFile
            echo "LOCAL_VERSION=${Globals.localVersion}" >> $envFile
            """
            archiveArtifacts envFile

            print('Build and distributing legion_test')
            sh """
			cp legion/legion/version.py legion_test/legion_test/version.py
			cd legion_test
    		../.venv/bin/python3 setup.py sdist
    		../.venv/bin/python3 setup.py sdist upload -r ${params.PyPiDistributionTargetName}
    		../.venv/bin/python3 setup.py bdist_wheel
    		../.venv/bin/python3 setup.py develop
    		cd -
    		"""

            print('Build and distributing etl')
            sh """
              cp legion/legion/version.py etl/etl/version.py
              cd etl
              ../.venv/bin/pip install -r requirements/base.txt
              ../.venv/bin/pip install -r requirements/test.txt
              ../.venv/bin/python3 setup.py sdist
              ../.venv/bin/python3 setup.py sdist upload -r ${params.PyPiDistributionTargetName}
              ../.venv/bin/python3 setup.py bdist_wheel
              ../.venv/bin/python3 setup.py develop
              cd -
            """

            print('Build and distributing legion')
            sh """
    		cd legion
    		../.venv/bin/python3 setup.py sdist
    		../.venv/bin/python3 setup.py sdist upload -r ${params.PyPiDistributionTargetName}
    		../.venv/bin/python3 setup.py bdist_wheel
    		../.venv/bin/python3 setup.py develop
    		cd -
    		"""
        }
        stage('Build docs'){
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

            sh "cd legion && cp -rf docs/build/html/ \"${params.LocalDocumentationStorage}\$(python3 -c 'import legion; print(legion.__version__);')/\""
        }
        stage('Run Python code analyzers'){
            sh '''
    		cd legion
    		../.venv/bin/pycodestyle legion
    		../.venv/bin/pycodestyle tests
    		../.venv/bin/pydocstyle legion

    		export TERM="linux"
    		rm -f pylint.log
    		../.venv/bin/pylint legion >> pylint.log || exit 0
    		../.venv/bin/pylint tests >> pylint.log || exit 0
    		cd ..
    		'''
            sh '''
              cd etl
              ../.venv/bin/pycodestyle slack
              ../.venv/bin/pycodestyle tests
              ../.venv/bin/pydocstyle slack

              export TERM="linux"
              ../.venv/bin/pylint slack >> pylint.log || exit 0
              ../.venv/bin/pylint tests >> pylint.log || exit 0
              cd ..
            '''

            archiveArtifacts 'legion/pylint.log'
            warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '', excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''
        }
        stage('Build Jenkins plugin'){
            sh """
            mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml clean
            mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml versions:set -DnewVersion=${Globals.baseVersion}-${Globals.localVersion}
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
                ${params.JenkinsPluginsRepositoryStore}/${Globals.baseVersion}-${Globals.localVersion}/legion-jenkins-plugin.hpi

                curl -v -u $USERNAME:$PASSWORD \
                --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                ${params.JenkinsPluginsRepositoryStore}/${Globals.baseVersion}/legion-jenkins-plugin.hpi

                curl -v -u $USERNAME:$PASSWORD \
                --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                ${params.JenkinsPluginsRepositoryStore}/latest/legion-jenkins-plugin.hpi
                """
            }
        }
        stage('Build Docker images'){

            dockerCacheArg = (params.EnableDockerCache) ? '' : '--no-cache'

            sh """
            cd base-python-image
            docker build $dockerCacheArg -t legion/base-python-image .
			"""

            sh """
    	    cd k8s/grafana
    	    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.baseVersion}+${Globals.localVersion}" -t legion/k8s-grafana .
    	    """

            sh """
            rm -rf k8s/edge/static/docs
            cp -rf legion/docs/build/html/ k8s/edge/static/docs/

            build_time=`date -u +'%d.%m.%Y %H:%M:%S'`

            sed -i "s/{VERSION}/${Globals.baseVersion} ${Globals.localVersion}/" k8s/edge/static/index.html
            sed -i "s/{COMMIT}/${Globals.rootCommit}/" k8s/edge/static/index.html
            sed -i "s/{BUILD_INFO}/#${env.BUILD_NUMBER} \$build_time UTC/" k8s/edge/static/index.html

    	    cd k8s/edge
    	    docker build $dockerCacheArg -t legion/k8s-edge .
    	    """

            sh """
    	    cd k8s/jenkins
    	    docker build $dockerCacheArg --build-arg jenkins_plugin_version="${Globals.baseVersion}-${Globals.localVersion}" --build-arg jenkins_plugin_server="${params.JenkinsPluginsRepository}" -t legion/k8s-jenkins .
    	    """

            sh """
    	    cd k8s/edi
    	    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.baseVersion}+${Globals.localVersion}" --build-arg source_image="legion/base-python-image" -t legion/k8s-edi .
    	    """

            sh """
    	    cd k8s/airflow
          docker build $dockerCacheArg -t legion/k8s-airflow --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${Globals.baseVersion}+${Globals.localVersion}" .
    	    """
        }
        stage('Publish Docker images'){
            if (params.PushDockerImages){
                def images = ["legion/base-python-image", "legion/k8s-edge", "legion/k8s-jenkins", "legion/k8s-grafana", "legion/k8s-edi", "legion/k8s-airflow"]

                images.each {
                    sh """
    				docker tag ${it} ${params.DockerRegistry}/${it}:latest
    				docker tag ${it} ${params.DockerRegistry}/${it}:${Globals.baseVersion}
    				docker tag ${it} ${params.DockerRegistry}/${it}:${Globals.baseVersion}-${Globals.localVersion}
    				docker push ${params.DockerRegistry}/${it}:latest
    				docker push ${params.DockerRegistry}/${it}:${Globals.baseVersion}
    				docker push ${params.DockerRegistry}/${it}:${Globals.baseVersion}-${Globals.localVersion}
    				"""
                }
            }
            else {
                println('Skipped due to PushDockerImages property')
            }
        }
        stage('Run Python tests'){
            sh '''
            cd legion
            ../.venv/bin/nosetests --with-coverage --cover-package legion --with-xunit --cover-html
            '''
            junit 'legion/nosetests.xml'

            sh "cd legion && cp -rf cover/ \"${params.LocalDocumentationStorage}\$(../.venv/bin/python3 -c 'import legion; print(legion.__version__);')-cover/\""
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

    print("Base version ${Globals.baseVersion} local version ${Globals.localVersion}")
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
    version *${Globals.baseVersion}  ${Globals.localVersion}*
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
