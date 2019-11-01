import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

pipeline {
    agent { label 'ec2builder'}

    options{
            buildDiscarder(logRotator(numToKeepStr: '35', artifactNumToKeepStr: '35'))
    }
    environment {
            /// Input parameters
            //Enable docker cache parameter
            param_enable_docker_cache = "${params.EnableDockerCache}"
            //Build major version release and optionally push it to public repositories
            param_stable_release = "${params.StableRelease}"
            //Release version to tag all artifacts to
            param_release_version = "${params.ReleaseVersion}"
            //Git Branch to build package from
            param_git_branch = "${params.GitBranch}"
             //Legion CICD repo url (for pipeline methods import)
            param_legion_cicd_repo = "${params.LegionCicdRepo}"
            //Legion repo branch (tag or branch name)
            param_legion_cicd_branch = "${params.LegionCicdBranch}"
            //Push release git tag
            param_push_git_tag = "${params.PushGitTag}"
            //Rewrite git tag i exists
            param_force_tag_push = "${params.ForceTagPush}"
            //Push release to master bransh
            param_update_master = "${params.UpdateMaster}"
            //Upload legion python package to pypi
            param_upload_legion_package = "${params.UploadLegionPackage}"
            //Set next releases version explicitly
            param_next_version = "${params.NextVersion}"
            // Update version string
            param_update_version_string = "${params.UpdateVersionString}"
            // Release version to be used as docker cache source
            param_docker_cache_source = "${params.DockerCacheSource}"
            //Artifacts storage parameters
            param_helm_repo_git_url = "${params.HelmRepoGitUrl}"
            param_helm_repo_git_branch = "${params.HelmRepoGitBranch}"
            param_helm_repository = "${params.HelmRepository}"
            param_pypi_repository = "${params.PyPiRepository}"
            param_local_pypi_distribution_target_name = "${params.LocalPyPiDistributionTargetName}"
            param_test_pypi_distribution_target_name = "${params.testPyPiDistributionTargetName}"
            param_public_pypi_distribution_target_name = "${params.PublicPyPiDistributionTargetName}"
            param_pypi_distribution_target_name = "${params.PyPiDistributionTargetName}"
            param_jenkins_plugins_repository_store = "${params.JenkinsPluginsRepositoryStore}"
            param_jenkins_plugins_repository = "${params.JenkinsPluginsRepository}"
            param_docker_registry = "${params.DockerRegistry}"
            param_docker_hub_registry = "${params.DockerHubRegistry}"
            param_git_deploy_key = "${params.GitDeployKey}"
            legionCicdGitlabKey = "${params.legionCicdGitlabKey}"
            ///Job parameters
            updateVersionScript = "scripts/update_version_id"
            sharedLibPath = "legion-cicd/pipelines/legionPipeline.groovy"
            pathToCharts= "${WORKSPACE}/helms"
            gcpCredential = "${params.GCPCredential}"
            documentationLocation = "${params.DocumentationGCS}"
    }

    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    sh 'echo RunningOn: $(curl http://checkip.amazonaws.com/)'

                    // import Legion components
                    sshagent(["${env.legionCicdGitlabKey}"]) {
                        print ("Checkout Legion-cicd repo")
                        sh"""#!/bin/bash -ex
                        mkdir -p \$(getent passwd \$(whoami) | cut -d: -f6)/.ssh && ssh-keyscan git.epam.com >> \$(getent passwd \$(whoami) | cut -d: -f6)/.ssh/known_hosts
                        if [ ! -d "legion-cicd" ]; then
                            git clone ${env.param_legion_cicd_repo} legion-cicd
                        fi
                        cd legion-profiles && git checkout ${env.param_legion_cicd_branch}
                        """

                        print ("Load legion pipeline common library")
                        legion = load "${env.sharedLibPath}"
                    }

                    dir("${WORKSPACE}/legion-cicd"){
                      print("Check code for security issues")
                      sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                      legion.setBuildMeta(env.updateVersionScript)
                    }
                }
            }
        }

        // Set Git Tag in case of stable release
        stage('Set GIT release Tag'){
            steps {
                script {
                    print (env.param_stable_release)
                    if (env.param_stable_release.toBoolean() && env.param_push_git_tag.toBoolean()){
                        legion.setGitReleaseTag("${env.param_git_deploy_key}")
                    }
                    else {
                        print("Skipping release git tag push")
                    }
                }
            }
        }

        stage("Docker login") {
            steps {
                withCredentials([[
                 $class: 'UsernamePasswordMultiBinding',
                 credentialsId: 'nexus-local-repository',
                 usernameVariable: 'USERNAME',
                 passwordVariable: 'PASSWORD']]) {
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${env.param_docker_registry}"
                }
                script {
                    if (env.param_stable_release.toBoolean()) {
                        withCredentials([[
                        $class: 'UsernamePasswordMultiBinding',
                        credentialsId: 'dockerhub',
                        usernameVariable: 'USERNAME',
                        passwordVariable: 'PASSWORD']]) {
                            sh "docker login -u ${USERNAME} -p ${PASSWORD}"
                        }
                    }
                }
            }
        }
        stage("Build Docker images & Run Tests") {
            parallel {
                stage("Build Jupyterlab Docker image"){
                    steps {
                        script {
                            legion.buildLegionImage('jupyterlab-dependencies', ".", "containers/jupyterlab/Dockerfile", "--target plugin-frontend-rebuilder")
                            legion.buildLegionImage('jupyterlab', '.', 'containers/jupyterlab/Dockerfile', "--cache-from legion/jupyterlab-dependencies:${Globals.buildVersion}")
                        }
                    }
                }
                stage("Build REST packager Docker image"){
                    steps {
                        script {
                            legion.buildLegionImage('packager-rest', '.', 'containers/ai-packagers/rest/Dockerfile')
                        }
                    }
                }
                stage('Build pipeline Docker agent') {
                    steps {
                        script {
                            legion.buildLegionImage('legion-pipeline-agent', '.', 'containers/pipeline-agent/Dockerfile')
                            legion.uploadDockerImage('legion-pipeline-agent')
                        }
                    }
                }
                stage('Build documentation builder') {
                    steps {
                        script {
                            legion.buildLegionImage('docs-builder', '.', 'containers/docs-builder/Dockerfile')
                            legion.uploadDockerImage('docs-builder')
                        }
                    }
                }
                stage("Build Fluentd Docker image") {
                    steps {
                        script {
                            legion.buildLegionImage('k8s-fluentd', 'containers/fluentd')
                        }
                    }
                }
                stage("Build model trainer and operator images") {
                    steps {
                        script {
                            legion.buildLegionImage('operator-dependencies', ".", "containers/operator/Dockerfile", "--target builder")
                            legion.buildLegionImage('k8s-operator', ".", "containers/operator/Dockerfile", "--target operator --cache-from legion/operator-dependencies:${Globals.buildVersion}")
                            legion.buildLegionImage('k8s-edi', ".", "containers/operator/Dockerfile", "--target edi --cache-from legion/operator-dependencies:${Globals.buildVersion}")
                            legion.buildLegionImage('service-catalog', ".", "containers/operator/Dockerfile", "--target service-catalog --cache-from legion/operator-dependencies:${Globals.buildVersion}")
                            legion.buildLegionImage('k8s-model-trainer', ".", "containers/operator/Dockerfile", "--target model-trainer --cache-from legion/operator-dependencies:${Globals.buildVersion}")
                            legion.buildLegionImage('k8s-model-packager', ".", "containers/operator/Dockerfile", "--target model-packager --cache-from legion/operator-dependencies:${Globals.buildVersion}")

                            docker.image("legion/operator-dependencies:${Globals.buildVersion}").inside() {
                                sh """
                                    gocover-cobertura < "\${OPERATOR_DIR}/operator-cover.out" > ./operator-cover.xml
                                    cp "\${OPERATOR_DIR}/operator-report.xml" "\${OPERATOR_DIR}/linter-output.txt" ./
                                """

                                junit 'operator-report.xml'
                                stash name: "operator-cover", includes: "operator-cover.xml"

                                sh 'rm -rf operator-report.xml operator-cover.xml'

                                def linterContent = readFile "linter-output.txt"

                                // If the linter result contains an error, then we mark the build as unstable.
                                if (linterContent?.trim()) {
                                  currentBuild.result = 'UNSTABLE'
                                }

                                archiveArtifacts 'linter-output.txt'
                            }
                        }
                    }
                }
                stage("Build feedback images") {
                    steps {
                        script {
                            legion.buildLegionImage('feedback-dependencies', ".", "containers/feedback-aggregator/Dockerfile", "--target builder")
                            legion.buildLegionImage('k8s-feedback-aggregator', ".", "containers/feedback-aggregator/Dockerfile", "--target aggregator --cache-from legion/feedback-dependencies:${Globals.buildVersion}")
                            legion.buildLegionImage('k8s-feedback-collector', ".", "containers/feedback-aggregator/Dockerfile", "--target collector --cache-from legion/feedback-dependencies:${Globals.buildVersion}")

                            docker.image("legion/feedback-dependencies:${Globals.buildVersion}").inside() {
                                sh """
                                    gocover-cobertura < "\${FEEDBACK_DIR}/feedback-cover.out" > ./feedback-cover.xml
                                    cp "\${FEEDBACK_DIR}/feedback-report.xml" ./
                                """

                                junit 'feedback-report.xml'
                                stash name: "feedback-cover", includes: "feedback-cover.xml"

                                sh 'rm -rf feedback-report.xml feedback-cover.xml'
                            }
                        }
                    }
                }
            }
        }
        stage("Run tests") {
            parallel {
                stage('Build docs') {
                    steps {
                        script {

                            docker.image("legion/docs-builder:${Globals.buildVersion}").inside() {
                                sh """
                                cd docs
                                /generate.sh
                                cp out/pdf/legion-docs.pdf ${WORKSPACE}/legion-docs.pdf
                                rm out/pdf/legion-docs.pdf
                                zip -r ${WORKSPACE}/${Globals.buildVersion}.zip out/*
                                """
                                archiveArtifacts artifacts: "legion-docs.pdf"
                                archiveArtifacts artifacts: "${Globals.buildVersion}.zip"
                            }

                            withCredentials([
                            file(credentialsId: "${env.gcpCredential}", variable: 'gcpCredential')]) {
                                docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-u root -e GOOGLE_CREDENTIALS=${gcpCredential}") {                                
                                    sh "gsutil cp ${WORKSPACE}/legion-docs.pdf ${env.documentationLocation}/${Globals.buildVersion}.pdf"                            
                                    sh "gsutil cp ${WORKSPACE}/${Globals.buildVersion}.zip ${env.documentationLocation}/${Globals.buildVersion}.zip"
                                }
                            }
                        }
                    }
                }
                stage("Run python unittests") {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root --net host") {
                                sh """
                                    cd /opt/legion
                                    make unittests || true
                                """
                                sh 'cp -r /opt/legion/target/legion-cover.xml /opt/legion/target/nosetests.xml /opt/legion/target/cover ./'
                                junit 'nosetests.xml'

                                stash name: "python-cover", includes: "legion-cover.xml"

                                publishHTML (target: [
                                        allowMissing: false,
                                        alwaysLinkToLastBuild: false,
                                        keepAll: true,
                                        reportDir: 'cover',
                                        reportFiles: 'index.html',
                                        reportName: "Test Coverage Report"
                                ])
                                sh 'rm -rf *-cover.xml nosetests.xml cover'
                            }
                        }
                    }
                }
                stage('Run Python code analyzers') {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside() {
                                def statusCode = sh script:'make lint', returnStatus:true

                                if (statusCode != 0) {
                                    currentBuild.result = 'UNSTABLE'
                                }

                                archiveArtifacts 'target/pylint/legion.log'
                                archiveArtifacts 'target/pydocstyle/legion.log'
                                step([
                                        $class                     : 'WarningsPublisher',
                                        parserConfigurations       : [[
                                                                              parserName: 'PYLint',
                                                                              pattern   : 'target/pylint/legion.log'
                                                                      ]],
                                        unstableTotalAll           : '0',
                                        usePreviousBuildAsReference: true
                                ])
                            }
                        }
                    }
                }
            }
        }

        stage('Upload artifacts'){
            parallel {
                stage("Upload coverage files") {
                    steps {
                        script {
                            unstash 'feedback-cover'
                            unstash 'operator-cover'
                            unstash 'python-cover'

                            cobertura coberturaReportFile: '*-cover.xml'
                        }
                    }
                }
                stage("Upload Legion package") {
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside() {
                                withCredentials([[
                                $class: 'UsernamePasswordMultiBinding',
                                credentialsId: 'nexus-local-repository',
                                usernameVariable: 'USERNAME',
                                passwordVariable: 'PASSWORD']]) {
                                sh """
                                cat > /tmp/.pypirc << EOL
                                [distutils]
                                index-servers =
                                  ${env.param_local_pypi_distribution_target_name}
                                [${env.param_local_pypi_distribution_target_name}]
                                repository=${env.param_pypi_repository.split('/').dropRight(1).join('/')}/
                                username=${env.USERNAME}
                                password=${env.PASSWORD}
                                EOL
                                """.stripIndent()
                                }
                                sh """
                                cat /tmp/.pypirc
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/sdk/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/cli/dist/legion-*'
                                # twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/packager/rest/dist/legion-*'
                                """

                                if (env.param_stable_release.toBoolean()) {
                                    if (env.param_upload_legion_package.toBoolean()){
                                        withCredentials([[
                                        $class: 'UsernamePasswordMultiBinding',
                                        credentialsId: 'pypi-repository',
                                        usernameVariable: 'USERNAME',
                                        passwordVariable: 'PASSWORD']]) {
                                            sh """
                                            cat > /tmp/.pypirc << EOL
                                            [distutils]
                                            index-servers =
                                              ${env.param_test_pypi_distribution_target_name}
                                              ${env.param_public_pypi_distribution_target_name}
                                            [${env.param_test_pypi_distribution_target_name}]
                                            repository=https://test.pypi.org/legacy/
                                            username=${env.USERNAME}
                                            password=${env.PASSWORD}
                                            [${env.param_public_pypi_distribution_target_name}]
                                            repository=https://upload.pypi.org/legacy/
                                            username=${env.USERNAME}
                                            password=${env.PASSWORD}
                                            EOL
                                            """.stripIndent()
                                        }
                                        sh """
                                        twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/sdk/dist/legion-*'
                                        twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/opt/legion/legion/cli/dist/legion-*'
                                        """
                                    } else {
                                        print("Skipping package upload")
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Package and upload helm charts'){
                    steps {
                        script {
                            docker.image("legion/legion-pipeline-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root") {
                                legion.uploadHelmCharts(env.pathToCharts)
                            }
                        }
                    }
                }
                stage("Upload model trainer image") {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-model-trainer')
                        }
                    }
                }
                stage("Upload model packager image") {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-model-packager')
                        }
                    }
                }
                stage("Upload model service catalog image") {
                    steps {
                        script {
                            legion.uploadDockerImage('service-catalog')
                        }
                    }
                }
                stage("Upload operator image") {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-operator')
                        }
                    }
                }
                stage("Upload feedback aggregator image") {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-feedback-aggregator')
                        }
                    }
                }
                stage("Upload feedback collector image") {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-feedback-collector')
                        }
                    }
                }
                stage('Upload Edi Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-edi')
                        }
                    }
                }
                stage("Upload REST packager Docker image"){
                    steps {
                        script {
                            legion.uploadDockerImage('packager-rest')
                        }
                    }
                }
                stage("Upload jupyterlab Docker image"){
                    steps {
                        script {
                            legion.uploadDockerImage('jupyterlab')
                        }
                    }
                }
                stage("Upload jupyterlab-dependencies Docker image"){
                    steps {
                        script {
                            legion.uploadDockerImage('jupyterlab-dependencies')
                        }
                    }
                }
                stage('Upload Fluentd Docker image') {
                    steps {
                        script {
                            legion.uploadDockerImage('k8s-fluentd')
                        }
                    }
                }
                stage('Upload Operator dependencies') {
                    steps {
                        script {
                            legion.uploadDockerImage('operator-dependencies')
                        }
                    }
                }
                stage('Upload Feedback dependencies') {
                    steps {
                        script {
                            legion.uploadDockerImage('feedback-dependencies')
                        }
                    }
                }
            }
        }

        stage("Update Legion version string") {
            steps {
                script {
                    if (env.param_stable_release.toBoolean() && env.param_update_version_string.toBoolean()) {
                        legion.updateVersionString(env.versionFile)
                    }
                    else {
                        print("Skipping version string update")
                    }
                }
            }
        }

        stage('Update Master branch'){
            steps {
                script {
                    if (env.param_update_master.toBoolean()){
                        legion.updateMasterBranch()
                    }
                    else {
                        print("Skipping Master branch update")
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                // import Legion components
                sshagent(["${env.legionCicdGitlabKey}"]) {
                    print ("Checkout Legion-cicd repo")
                    sh"""#!/bin/bash -ex
                      mkdir -p \$(getent passwd \$(whoami) | cut -d: -f6)/.ssh && ssh-keyscan git.epam.com >> \$(getent passwd \$(whoami) | cut -d: -f6)/.ssh/known_hosts
                      if [ ! -d "legion-cicd" ]; then
                      git clone ${env.param_legion_cicd_repo} legion-cicd
                      fi
                      cd legion-profiles && git checkout ${env.param_legion_cicd_branch}
                    """
                    print ("Load legion pipeline common library")
                    legion = load "${env.sharedLibPath}"
                }
                dir("${WORKSPACE}/legion-cicd") {
                    legion.notifyBuild(currentBuild.currentResult)
                }
            }
            deleteDir()
        }
    }
}
