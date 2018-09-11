import java.text.SimpleDateFormat

class Globals {
    static String rootCommit = null
    static String buildVersion = null
    static String dockerLabels = null
}

pipeline {
	agent { 
		dockerfile {
			filename 'pipeline.Dockerfile'
		}
	}

	stages {
		stage('Checkout') {
			steps {
				checkout scm
				Globals.rootCommit = sh returnStdout: true, script: 'git rev-parse --short HEAD 2> /dev/null | sed  "s/\\(.*\\)/\\1/"'
				Globals.rootCommit = Globals.rootCommit.trim()
			}
            def dateFormat = new SimpleDateFormat("yyyyMMddHHmmss")
            def date = new Date()
            def buildDate = dateFormat.format(date)

            Globals.dockerLabels = "--label git_revision=${Globals.rootCommit} --label build_id=${env.BUILD_NUMBER} --label build_user=${env.BUILD_USER} --label build_date=${buildDate}"
            println(Globals.dockerLabels)

            if (params.StableRelease) {
                stage('Set GIT release Tag'){
                    if (params.PushGitTag){
                        print('Set Release tag')
                        sh """
                        if [ `git tag |grep ${params.ReleaseVersion}` ]; then
                            if [ ${params.ForceTagPush} = "true" ]; then
                                echo 'Removing existing git tag'
                                git tag -d ${params.ReleaseVersion}
                                git push origin :refs/tags/${params.ReleaseVersion}
                            else
                                echo 'Specified tag already exists!'
                                exit 1
                            fi
                        fi
                        git tag ${params.ReleaseVersion}
                        git push origin ${params.ReleaseVersion}
                        """
                    } else {
                        print("Skipping release git tag push")
                    }
                }
            }
		}
		stage('Set Legion build version') {
			steps {
                if (params.StableRelease) {
                    if (params.ReleaseVersion){
                        Globals.buildVersion = sh returnStdout: true, script: ".venv/bin/update_version_id --build-version=${params.ReleaseVersion} legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                    } else {
                        print('Error: ReleaseVersion parameter must be specified for stable release')
                        exit 1
                    }
                } else {
                    Globals.buildVersion = sh returnStdout: true, script: ".venv/bin/update_version_id legion/legion/version.py ${env.BUILD_NUMBER} ${env.BUILD_USER}"
                }
                Globals.buildVersion = Globals.buildVersion.replaceAll("\n", "")

                currentBuild.description = "${Globals.buildVersion} ${params.GitBranch}"
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
		}
	}
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