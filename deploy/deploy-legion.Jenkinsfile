def targetBranch = params.GitBranch

node {
    try{
        stage('Checkout GIT'){
            def scmVars = checkout scm
            targetBranch = scmVars.GIT_COMMIT

            currentBuild.description = "${params.Profile} ${params.GitBranch}"
        }
        
        stage('Install packages'){
                sh '''
                sudo rm -rf .venv
                virtualenv .venv -p $(which python3)
    
                cd legion
                ../.venv/bin/python3 setup.py develop
                cd ..

                cd legion_test
                ../.venv/bin/python3 setup.py develop
                '''
        }

        
        stage('Deploy Legion') {
            if (params.DeployLegion){
                dir('deploy/ansible'){
                    withCredentials([file(credentialsId: params.Profile, variable: 'CREDENTIAL_SECRETS')]) {
                        withAWS(credentials: 'kops') {
                            wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
                                ansiblePlaybook(
                                    playbook: 'deploy-legion.yml',
                                    extras: ' --extra-vars "profile=${Profile} base_version=${BaseVersion}  local_version=${LocalVersion}"',
                                    colorized: true
                                )
                            }
                        }
                    }
                }
            }
            else {
                    print("Skipping Legion Deployment")
            }
        }
        
        stage('Create jenkins jobs'){
            if (params.CreateJenkinsTests){
                sh """
                cd legion_test
                ../.venv/bin/pip install -r requirements/base.txt
                ../.venv/bin/pip install -r requirements/test.txt
                ../.venv/bin/python setup.py develop
                cd ..

                .venv/bin/create_example_jobs \
                "https://jenkins.${params.Profile}" \
                examples \
                . \
                "git@github.com:epam/legion.git" \
                ${targetBranch} \
                --connection-timeout 600 \
                --git-root-key "legion-root-key" \
                --model-host "" \
                --dynamic-model-prefix "DYNAMIC MODEL"
                """
            }
            else {
                println('Skipping Jenkins Jobs creation')
            }
        }

        stage('Run regression tests'){
            if (params.UseRegressionTests){
                withAWS(credentials: 'kops') {
                    sh '''
                    cd legion
                    ../.venv/bin/pip install -r requirements/base.txt
                    ../.venv/bin/pip install -r requirements/test.txt
                    ../.venv/bin/python setup.py develop
                    cd ..
                    
                    cd legion_test
                    ../.venv/bin/pip install -r requirements/base.txt
                    ../.venv/bin/pip install -r requirements/test.txt
                    ../.venv/bin/python setup.py develop

                    echo "Starting robot tests"
                    cd ../tests/robot
                    ../../.venv/bin/pip install yq

                    PATH_TO_PROFILE="../../deploy/profiles/$Profile.yml"
                    CLUSTER_NAME=$(yq -r .cluster_name $PATH_TO_PROFILE)
                    CLUSTER_STATE_STORE=$(yq -r .state_store $PATH_TO_PROFILE)
                    echo "Loading kubectl config from $CLUSTER_STATE_STORE for cluster $CLUSTER_NAME"

                    kops export kubecfg --name $CLUSTER_NAME --state $CLUSTER_STATE_STORE
                    DISPLAY=:99 PROFILE=$Profile BASE_VERSION=$BaseVersion LOCAL_VERSION=$LocalVersion \
                     ../../.venv/bin/python3 -m robot.run *.robot || true

                    echo "Starting python tests"
                    cd ../python

                    kops export kubecfg --name $CLUSTER_NAME --state $CLUSTER_STATE_STORE
                    PROFILE=$Profile BASE_VERSION=$BaseVersion LOCAL_VERSION=$LocalVersion \
                    ../../.venv/bin/nosetests --with-coverage --cover-package legion --with-xunit --cover-html || true
                    '''
                    step([
                        $class : 'RobotPublisher',
                        outputPath : 'tests/robot/',
                        outputFileName : "*.xml",
                        disableArchiveOutput : false,
                        passThreshold : 100,
                        unstableThreshold: 95.0,
                        onlyCritical : true,
                        otherFiles : "*.png",
                    ])
                }
                junit 'tests/python/nosetests.xml'
            }
            else {
                println('Skipped due to UseRegressionTests property')
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
    profile *<https://${params.Profile}|${params.Profile}>*
    version *${params.BaseVersion} ${params.LocalVersion}*
    Deploy *${params.DeployLegion}*,  Create Jenkins tests *${params.CreateJenkinsTests}*, Use regression tests *${params.UseRegressionTests}*
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