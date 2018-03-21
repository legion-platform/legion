node {
    def rootCommit
    def baseVersion
    def localVersion

    try {
        stage('Checkout GIT'){
            checkout scm
            rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed "s/\\(.*\\)/\\1/"'
            rootCommit = rootCommit.trim()
        }
        stage('Install build dependencies'){
            sh '''
            sudo chmod a+r -R .
    	    cd legion
    	    sudo pip3 install -r requirements/base.txt
    	    sudo pip3 install -r requirements/test.txt
    	    '''
        }
        stage('Build Jenkins plugin'){
            if (params.BuildNewJenkinsPlugin){
                sh 'mvn -f k8s/jenkins/legion-jenkins-plugin/pom.xml clean install'
                archiveArtifacts 'k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi'

                withCredentials([[
                     $class: 'UsernamePasswordMultiBinding',
                     credentialsId: 'nexus-local-repository',
                     usernameVariable: 'USERNAME',
                     passwordVariable: 'PASSWORD']]) {
                    sh """
                    curl -v -u $USERNAME:$PASSWORD \
                    --upload-file k8s/jenkins/legion-jenkins-plugin/target/legion-jenkins-plugin.hpi \
                    ${params.JenkinsPluginsRepositoryPath}
                    """
                }

            }
            else {
                println('Skipped due to BuildNewJenkinsPlugin property')
            }
        }
        stage('Build Python packages') {
            sh '''
			cd legion_test
    		sudo python3 setup.py sdist
    		sudo python3 setup.py bdist_wheel
    		sudo python3 setup.py develop
    		cd -
    		'''

            def version = sh returnStdout: true, script: 'update_version_id --extended-output legion/legion/version.py'
            print("Detected legion version:\n" + version)

            version = version.split("\n")
            baseVersion = version[1]
            localVersion = version[2]

            print("Base version " + baseVersion + " local version " + localVersion)

            print('Building shared artifact')
            envFile = 'file.env'
            sh """
            rm -f $envFile
            touch $envFile
            echo "BASE_VERSION=$baseVersion" >> $envFile
            echo "LOCAL_VERSION=$localVersion" >> $envFile
            """
            archiveArtifacts envFile

            print('Build and distributing legion_test')
            sh """
			cp legion/legion/version.py legion_test/legion_test/version.py
			cd legion_test
    		sudo python3 setup.py sdist
    		sudo python3 setup.py sdist upload -r ${params.PyPiDistributionTargetName}
    		sudo python3 setup.py bdist_wheel
    		sudo python3 setup.py develop
    		cd -
    		"""

            print('Build and distributing legion')
            sh """
    		cd legion
    		sudo python3 setup.py sdist
    		sudo python3 setup.py sdist upload -r ${params.PyPiDistributionTargetName}
    		sudo python3 setup.py bdist_wheel
    		sudo python3 setup.py develop
    		cd -
    		"""
        }
        stage('Build docs'){
            fullBuildNumber = env.BUILD_NUMBER
            fullBuildNumber.padLeft(4, '0')

            sh '''
    		cd legion
    		LEGION_VERSION="\$(python3 -c 'import legion; print(legion.__version__);')"

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
    		pycodestyle legion
    		pycodestyle tests
    		pydocstyle legion

    		export TERM="linux"
    		rm -f pylint.log
    		pylint legion >> pylint.log || exit 0
    		pylint tests >> pylint.log || exit 0
    		cd ..
    		'''

            archiveArtifacts 'legion/pylint.log'
            warnings canComputeNew: false, canResolveRelativePaths: false, categoriesPattern: '', defaultEncoding: '', excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[parserName: 'PyLint', pattern: 'legion/pylint.log']], unHealthy: ''
        }
        stage('Build Docker images'){

            dockerCacheArg = (params.EnableDockerCache) ? '' : '--no-cache'

            sh """
            cd base-python-image
            docker build $dockerCacheArg -t legion/base-python-image .
			"""

            sh """
    	    cd k8s/jupyterhub
    	    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${baseVersion}+${localVersion}" -t legion/jupyterhub .
    	    """

            sh """
    	    cd k8s/grafana
    	    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${baseVersion}+${localVersion}" -t legion/k8s-grafana .
    	    """

            sh """
            rm -rf k8s/edge/static/docs
            cp -rf legion/docs/build/html/ k8s/edge/static/docs/

            build_time=`date -u +'%d.%m.%Y %H:%M:%S'`

            sed -i "s/{VERSION}/${baseVersion} ${localVersion}/" k8s/edge/static/index.html
            sed -i "s/{COMMIT}/${rootCommit}/" k8s/edge/static/index.html
            sed -i "s/{BUILD_INFO}/#${env.BUILD_NUMBER} \$build_time UTC/" k8s/edge/static/index.html

    	    cd k8s/edge
    	    docker build $dockerCacheArg -t legion/k8s-edge .
    	    """

            sh """
    	    cd k8s/jenkins
    	    docker build $dockerCacheArg --no-cache --build-arg jenkins_plugin_server="${params.JenkinsPluginsRepository}" -t legion/k8s-jenkins .
    	    """

            sh """
    	    cd k8s/edi
    	    docker build $dockerCacheArg --build-arg pip_extra_index_params="--extra-index-url ${params.PyPiRepository}" --build-arg pip_legion_version_string="==${baseVersion}+${localVersion}" --build-arg source_image="legion/base-python-image" -t legion/k8s-edi .
    	    """

            sh """
    	    cd k8s/airflow
    	    docker build $dockerCacheArg -t legion/k8s-airflow .
    	    """
        }
        stage('Publish Docker images'){
            if (params.PushDockerImages){
                def images = ["legion/base-python-image", "legion/jupyterhub", "legion/k8s-edge", "legion/k8s-jenkins", "legion/k8s-grafana", "legion/k8s-edi", "legion/k8s-airflow"]

                images.each {
                    sh """
    				docker tag ${it} ${params.DockerRegistry}/${it}:latest
    				docker tag ${it} ${params.DockerRegistry}/${it}:${baseVersion}
    				docker tag ${it} ${params.DockerRegistry}/${it}:${baseVersion}-${localVersion}
    				docker push ${params.DockerRegistry}/${it}:latest
    				docker push ${params.DockerRegistry}/${it}:${baseVersion}
    				docker push ${params.DockerRegistry}/${it}:${baseVersion}-${localVersion}
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
            nosetests --with-coverage --cover-package legion --with-xunit --cover-html
            '''
            junit 'legion/nosetests.xml'

            sh "cd legion && cp -rf cover/ \"${params.LocalDocumentationStorage}\$(python3 -c 'import legion; print(legion.__version__);')-cover/\""
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

    print("Base version " + baseVersion + " local version " + localVersion)
}



def notifyBuild(String buildStatus = 'STARTED') {
    // build status of null means successful
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    // Default values
    def colorName = 'RED'
    def colorCode = '#FF0000'
    def subject = "Job *${env.JOB_NAME}* #${env.BUILD_NUMBER} - *${buildStatus}*"
    def summary = "@channel ${subject} \nbranch *${params.GitBranch}*\n<${env.BUILD_URL}|Open>"

    // Override default values based on build status
    if (buildStatus == 'STARTED') {
        color = 'YELLOW'
        colorCode = '#FFFF00'
    } else if (buildStatus == 'SUCCESSFUL') {
        color = 'GREEN'
        colorCode = '#00FF00'
    } else {
        color = 'RED'
        colorCode = '#FF0000'
    }

    // Send notifications
    if (params.SLACK_NOTIFICATION_ENABLED){
        slackSend (color: colorCode, message: summary)
    }
}