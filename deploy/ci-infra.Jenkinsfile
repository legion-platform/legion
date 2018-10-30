def legionVersion = "latest"

node {
    try {
        stage('Terminate Cluster if exists') {
            result = build job: params.TerminateClusterJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
            ]
        }

        stage('Create Cluster') {
            result = build job: params.CreateClusterJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    booleanParam(name: 'Skip_kops', value: false),
            ]
        }

        stage('Deploy Legion & run tests') {
            result = build job: params.DeployLegionJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    string(name: 'LegionVersion', value: legionVersion),
                    string(name: 'TestsTags', value: "infra"),
                    booleanParam(name: 'DeployLegion', value: true),
                    booleanParam(name: 'CreateJenkinsTests', value: true),
                    booleanParam(name: 'UseRegressionTests', value: true),
            ]
        }

        stage('Deploy Legion Enclave') {
            result = build job: params.DeployLegionEnclaveJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    string(name: 'LegionVersion', value: legionVersion),
                    string(name: 'EnclaveName', value: 'enclave-ci')
            ]
        }

        stage('Terminate Legion Enclave') {
            result = build job: params.TerminateLegionEnclaveJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
                    string(name: 'EnclaveName', value: 'enclave-ci')
            ]
        }

    }
    catch (e) {
        // If there was an exception thrown, the build failed
        currentBuild.result = "FAILED"
        throw e
    }
    finally {
        stage('Terminate Cluster') {
            result = build job: params.TerminateClusterJobName, propagate: true, wait: true, parameters: [
                    [$class: 'GitParameterValue', name: 'GitBranch', value: params.GitBranch],
                    string(name: 'Profile', value: params.Profile),
            ]
        }
    }

}