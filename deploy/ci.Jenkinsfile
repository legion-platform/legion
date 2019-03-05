pipeline {
    agent any

    environment {
        //Input parameters
        param_git_branch = "${params.GitBranch}"
        param_profile = "${params.Profile}"
        param_enable_docker_cache = "${params.EnableDockerCache}"
        param_deploy_legion = "${params.DeployLegion}"
        param_create_jenkins_tests = "${params.CreateJenkinsTests}"
        param_use_regression_tests = "${params.UseRegressionTests}"
        param_tests_tags = "${params.TestsTags}"
        param_pypi_repo = "${params.PypiRepo}"
        param_docker_repo = "${params.DockerRepo}"
        param_helm_repo = "${params.HelmRepo}"
        param_build_legion_job_name = "${params.BuildLegionJobName}"
        param_terminate_cluster_job_name = "${params.TerminateClusterJobName}"
        param_create_cluster_job_name = "${params.CreateClusterJobName}"
        param_deploy_legion_job_name = "${params.DeployLegionJobName}"
        param_deploy_legion_enclave_job_name = "${params.DeployLegionEnclaveJobName}"
        param_terminate_legioin_enclave_job_name = "${params.TerminateLegionEnclaveJobName}"
        //Job parameters
        sharedLibPath = "deploy/legionPipeline.groovy"
        legionVersion = null
        commitID = null
        ansibleHome =  "/opt/legion/deploy/ansible"
        ansibleVerbose = '-v'
        helmLocalSrc = 'false'
        mergeBranch = "ci/${params.GitBranch}"
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    print('Set interim merge branch')
                    sh """
                    echo ${env.mergeBranch}
                    if [ `git branch | grep ${env.mergeBranch}` ]; then
                        echo 'Removing existing git tag'
                        git branch -D ${env.mergeBranch}
                        git push origin --delete ${env.mergeBranch}
                    fi
                    git branch ${env.mergeBranch}
                    git push origin ${env.mergeBranch}
                    """

                    legion = load "${env.sharedLibPath}"
                    legion.buildDescription()
                    commitID = env.mergeBranch
                }
            }
        }

       stage('Build') {
           steps {
               script {
                   result = build job: env.param_build_legion_job_name, propagate: true, wait: true, parameters: [
                           [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
                           string(name: 'EnableDockerCache', value: env.param_enable_docker_cache)
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

                   // \ Load variables
                   def map = [:]
                   def envs = sh returnStdout: true, script: "cat file.env"

                   envs.split("\n").each {
                       kv = it.split('=', 2)
                       print "Loaded ${kv[0]} = ${kv[1]}"
                       map[kv[0]] = kv[1]
                   }

                   legionVersion = map["LEGION_VERSION"]

                   print "Loaded version ${legionVersion}"
                   // Load variables

                   if (!legionVersion) {
                       error 'Cannot get legion release version number'
                   }
               }
           }
       }

       stage('Terminate Cluster if exists') {
           steps {
               script {
                   result = build job: env.param_terminate_cluster_job_name, propagate: true, wait: true, parameters: [
                           [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
                           string(name: 'LegionVersion', value: legionVersion),
                           string(name: 'Profile', value: env.param_profile),
                   ]
               }
           }
       }

       stage('Create Cluster') {
           steps {
               script {
                   result = build job: env.param_create_cluster_job_name, propagate: true, wait: true, parameters: [
                           [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
                           string(name: 'Profile', value: env.param_profile),
                           string(name: 'LegionVersion', value: legionVersion),
                           booleanParam(name: 'SkipKops', value: false)
                   ]
               }
           }
       }

       stage('Deploy Legion & run tests') {
           steps {
               script {
                   result = build job: env.param_deploy_legion_job_name, propagate: true, wait: true, parameters: [
                           [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
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

       stage('Deploy Legion Enclave') {
           steps {
               script {
                   result = build job: env.param_deploy_legion_enclave_job_name, propagate: true, wait: true, parameters: [
                           [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
                           string(name: 'Profile', value: env.param_profile),
                           string(name: 'TestsTags', value: env.param_tests_tags ?: ""),
                           string(name: 'LegionVersion', value: legionVersion),
                           string(name: 'EnclaveName', value: 'enclave-ci')
                   ]
               }
           }
       }

       stage('Terminate Legion Enclave') {
           steps {
               script {
                   result = build job: env.param_terminate_legioin_enclave_job_name, propagate: true, wait: true, parameters: [
                           [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
                           string(name: 'Profile', value: env.param_profile),
                           string(name: 'LegionVersion', value: legionVersion),
                           string(name: 'EnclaveName', value: 'enclave-ci')
                   ]
               }
           }
       }
   }

    post {
        always {
            script {
                legion = load "${sharedLibPath}"
                result = build job: env.param_terminate_cluster_job_name, propagate: true, wait: true, parameters: [
                        [$class: 'GitParameterValue', name: 'GitBranch', value: env.mergeBranch],
                       string(name: 'LegionVersion', value: legionVersion),
                        string(name: 'Profile', value: env.param_profile)]

                legion.notifyBuild(currentBuild.currentResult)
            }
        }
        cleanup {
            script {
                print('Remove interim merge branch')
                sh """
                    if [ `git branch | grep ${env.mergeBranch}` ]; then
                        git branch -D ${env.mergeBranch}
                        git push origin --delete ${env.mergeBranch}
                    fi
                """
            }
            deleteDir()
        }
    }
}
