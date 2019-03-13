pipeline {
    agent any

    environment {
        //Input parameters
        param_git_branch = "${params.GitBranch}"
        param_profile = "${params.Profile}"
        param_legion_version = "${params.LegionVersion}"
        param_deploy_legion = "${params.DeployLegion}"
        param_create_jenkins_tests = "${params.CreateJenkinsTests}"
        param_use_regression_tests = "${params.UseRegressionTests}"
        param_tests_tags = "${params.TestsTags}"
        param_pypi_repo = "${params.PypiRepo}"
        param_docker_repo = "${params.DockerRepo}"
        param_helm_repo = "${params.HelmRepo}"
        param_build_legion_job_name = "${params.BuildLegionJobName}"
        param_deploy_legion_job_name = "${params.DeployLegionJobName}"
        param_debug_run = "${params.DebugRun}"
        //Job parameters
        sharedLibPath = "deploy/legionPipeline.groovy"
        legionVersion = null
        commitID = null
        cleanupContainerVersion = "latest"
        ansibleHome =  "/opt/legion/deploy/ansible"
        ansibleVerbose = '-v'
        helmLocalSrc = 'false'
    }


    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    legion = load "${env.sharedLibPath}"
                    legion.buildDescription()
                    commitID = env.GIT_COMMIT
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    result = build job: env.param_build_legion_job_name, propagate: true, wait: true, parameters: [
                            [$class: 'GitParameterValue', name: 'GitBranch', value: env.param_git_branch],
                    ]

                    buildNumber = result.getNumber()
                    print 'Finished build id ' + buildNumber.toString()

                    // Save logs
                    logFile = result.getRawBuild().getLogFile()
                    sh """
                    cat "${logFile.getPath()}" | perl -pe 's/\\x1b\\[8m.*?\\x1b\\[0m//g;' > build-log.txt 2>&1
                    """
                    archiveArtifacts 'build-log.txt'

                    // Copy artifacts
                    copyArtifacts filter: '*', flatten: true, fingerprintArtifacts: true, projectName: env.param_build_legion_job_name, selector: specific      (buildNumber.toString()), target: ''
                    sh 'ls -lah'

                    // Load variables
                    def map = [:]
                    def envs = sh returnStdout: true, script: "cat file.env"

                    envs.split("\n").each {
                        kv = it.split('=', 2)
                        print "Loaded ${kv[0]} = ${kv[1]}"
                        map[kv[0]] = kv[1]
                    }

                    legionVersion = map["LEGION_VERSION"]

                    print "Loaded version ${legionVersion}"
                    // \ Load variables

                    if (!legionVersion) {
                        error 'Cannot get legion release version number'
                    }
                }
            }
        }

        stage('Deploy Legion & run tests') {
            steps {
                script {
                    result = build job: env.param_deploy_legion_job_name, propagate: true, wait: true, parameters: [
                            [$class: 'GitParameterValue', name: 'GitBranch', value: env.param_git_branch],
                            string(name: 'Profile', value: env.param_profile),
                            string(name: 'LegionVersion', value: legionVersion),
                            string(name: 'TestsTags', value: env.param_tests_tags ?: ""),
                            booleanParam(name: 'DeployLegion', value: true),
                            booleanParam(name: 'CreateJenkinsTests', value: true),
                            booleanParam(name: 'UseRegressionTests', value: true)
                    ]
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
        }
        cleanup {
            script {
                legion.cleanupClusterSg(param_legion_version ?: cleanupContainerVersion)
            }
            deleteDir()
        }
    }
}