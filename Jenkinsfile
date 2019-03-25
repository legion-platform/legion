import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
    static String dockerCacheArg = null
}

def chartNames = null

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
            param_pypi_repository = "${params.PyPiRepository}"
            param_local_pypi_distribution_target_name = "${params.LocalPyPiDistributionTargetName}"
            param_test_pypi_distribution_target_name = "${params.testPyPiDistributionTargetName}"
            param_public_pypi_distribution_target_name = "${params.PublicPyPiDistributionTargetName}"
            param_pypi_distribution_target_name = "${params.PyPiDistributionTargetName}"
            param_docker_registry = "${params.DockerRegistry}"
            param_docker_hub_registry = "${params.DockerHubRegistry}"
            param_git_deploy_key = "${params.GitDeployKey}"
            ///Job parameters
            sharedLibPath = "deploy/legionPipeline.groovy"
    }

    stages {
        stage('Checkout and set build vars') {
            steps {
                cleanWs()
                checkout scm
                script {
                    legion = load "${env.sharedLibPath}"
                    Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
                    Globals.rootCommit = Globals.rootCommit.trim()
                    println("Root commit: " + Globals.rootCommit)

                    def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
                    def date = new Date()
                    def buildDate = dateFormat.format(date)

                    Globals.dockerCacheArg = (env.param_enable_docker_cache.toBoolean()) ? '' : '--no-cache'
                    println("Docker cache args: " + Globals.dockerCacheArg)

                    wrap([$class: 'BuildUser']) {
                        BUILD_USER = binding.hasVariable('BUILD_USER') ? "${BUILD_USER}" : "null"
                    }

                    Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user='${BUILD_USER}' --label build_date=${buildDate}"
                    println("Docker labels: " + Globals.dockerLabels)

                    print("Check code for security issues")
                    sh "bash install-git-secrets-hook.sh install_hooks && git secrets --scan -r"

                    /// Define build version
                    if (env.param_stable_release) {
                        if (env.param_release_version ) {
                            Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id --build-version=${env.param_release_version} legion/legion/version.py ${env.BUILD_NUMBER} '${BUILD_USER}'"
                        } else {
                            print('Error: ReleaseVersion parameter must be specified for stable release')
                            exit 1
                        }
                    } else {
                        Globals.buildVersion = sh returnStdout: true, script: "python tools/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} '${BUILD_USER}'"
                    }

                    Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                    env.BuildVersion = Globals.buildVersion

                    currentBuild.description = "${Globals.buildVersion} ${env.param_git_branch}"
                    print("Build version " + Globals.buildVersion)
                    print('Building shared artifact')
                    envFile = 'file.env'
                    sh """
                    rm -f $envFile
                    touch $envFile
                    echo "LEGION_VERSION=${Globals.buildVersion}" >> $envFile
                    """
                    archiveArtifacts envFile
                    sh "rm -f $envFile"
                }
            }
        }

        // Set Git Tag in case of stable release
        stage('Set GIT release Tag'){
            steps {
                script {
                    if (env.param_stable_release) {
                        if (env.param_push_git_tag.toBoolean()){
                            print('Set Release tag')
                            sshagent(["${env.param_git_deploy_key}"]) {
                                sh """
                                if [ `git tag |grep -x ${env.param_release_version}` ]; then
                                    if [ ${env.param_force_tag_push} = "true" ]; then
                                        echo 'Removing existing git tag'
                                        git tag -d ${env.param_release_version}
                                        git push origin :refs/tags/${env.param_release_version}
                                    else
                                        echo 'Specified tag already exists!'
                                        exit 1
                                    fi
                                fi
                                git tag ${env.param_release_version}
                                git push origin ${env.param_release_version}
                                """
                            }
                        } else {
                            print("Skipping release git tag push")
                        }
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
                    if (env.param_stable_release) {
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

        stage('Build Legion inside Docker') {
            steps {
                script {
                    legion.buildLegionImage('legion-docker-agent', '.', 'pipeline.Dockerfile')
                    legion.uploadDockerImage('legion-docker-agent')
                }
            }
        }

        stage('Run Python code analyzers') {
            steps {
                script{
                    docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
                        sh '''
                        bash analyze_code.sh
                        '''

                        archiveArtifacts 'legion-pylint.log'
                        step([
                            $class                     : 'WarningsPublisher',
                            parserConfigurations       : [[
                                                                parserName: 'PYLint',
                                                                pattern   : 'legion-pylint.log'
                                                        ]],
                            unstableTotalAll           : '0',
                            usePreviousBuildAsReference: true
                        ])
                    }
                }
            }
        }

        stage('Run tests and upload artofacts'){
            parallel {
                stage("Upload Legion package") {
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
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
        """
                                }
                                sh """
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/dist/legion-*'
                                twine upload -r ${env.param_local_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion_test/dist/legion_test-*'
                                """

                                if (env.param_stable_release) {
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
        """
                                        }
                                        sh """
                                        twine upload -r ${env.param_pypi_distribution_target_name} --config-file /tmp/.pypirc '/src/legion/dist/legion-*'
                                        """
                                    } else {
                                        print("Skipping package upload")
                                    }
                                }
                            }
                        }
                    }
                }

                stage('Build docs') {
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside() {
                                sh """
                                cd legion/docs
                                sphinx-apidoc -f --private -o source/ ../legion/ -V '${Globals.buildVersion}'
                                sed -i 's/\'1.0\'/\'${Globals.buildVersion}\'/' source/conf.py
                                make html
                                find build/html -type f -name '*.html' | xargs sed -i -r 's/href=\"(.*)\\.md\"/href=\"\\1.html\"/'
                                cd ../../
                                """

                                sh "tar -czf legion_docs_${Globals.buildVersion}.tar.gz legion/docs/build/html/"
                                archiveArtifacts artifacts: "legion_docs_${Globals.buildVersion}.tar.gz"
                            }
                        }
                    }
                }

                stage("Run Python tests") {
                    steps {
                        script {
                            docker.image("legion/legion-docker-agent:${Globals.buildVersion}").inside("-v /var/run/docker.sock:/var/run/docker.sock -u root --net host") {
                                sh """
                                export TEMP_DIRECTORY="\$(pwd)"
                                cd /src/legion
                                VERBOSE=true \
                                DEBUG=true \
                                BASE_IMAGE_VERSION="${Globals.buildVersion}" \
                                SANDBOX_PYTHON_TOOLCHAIN_IMAGE="legion/python-toolchain:${Globals.buildVersion}" \
                                    nosetests --processes=10 \
                                    --process-timeout=600 \
                                    --with-coverage \
                                    --cover-package legion \
                                    --with-xunitmp \
                                    --cover-xml \
                                    --cover-html \
                                    --logging-level DEBUG \
                                    -v || true

                                cd -
                                cp /src/legion/nosetests.xml legion/nosetests.xml
                                cp /src/legion/coverage.xml legion/coverage.xml
                                cp -r /src/legion/cover legion/cover
                                """

                                junit 'legion/nosetests.xml'
                                cobertura coberturaReportFile: 'legion/coverage.xml'
                                publishHTML (target: [
                                    allowMissing: false,
                                    alwaysLinkToLastBuild: false,
                                    keepAll: true,
                                    reportDir: 'legion/cover',
                                    reportFiles: 'index.html',
                                    reportName: "Test Coverage Report"
                                ])

                                sh """
                                    rm -rf legion/nosetests.xml
                                    rm -rf legion/coverage.xml
                                    rm -rf legion/cover
                                """
                            }
                        }
                    }
                }
            }
        }

        stage("CI Stage") {
            steps {
                script {
                    if (env.param_stable_release) {
                        stage('Update Legion version string'){
                            //Update version.py file in legion package with new version string
                            if (env.param_update_version_string.toBoolean()){
                                print('Update Legion package version string')
                                if (env.param_next_version){
                                    sshagent(["${env.param_git_deploy_key}"]) {
                                        sh """
                                        git reset --hard
                                        git checkout develop
                                        sed -i -E "s/__version__.*/__version__ = \'${nextVersion}\'/g" legion/legion/version.py
                                        git commit -a -m "Bump Legion version to ${nextVersion}" && git push origin develop
                                        """
                                    }
                                } else {
                                    throw new Exception("next_version must be specified with update_version_string parameter")
                                }
                            }
                            else {
                                print("Skipping version string update")
                            }
                        }

                        stage('Update Master branch'){
                            if (env.param_update_master.toBoolean()){
                                sshagent(["${env.param_git_deploy_key}"]) {
                                    sh """
                                    git reset --hard
                                    git checkout develop
                                    git checkout master && git pull -r origin master
                                    git pull -r origin develop
                                    git push origin master
                                    """
                                }
                            }
                            else {
                                print("Skipping Master branch update")
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                legion = load "${sharedLibPath}"
                legion.notifyBuild(currentBuild.currentResult)
            }
            deleteDir()
        }
    }
}
