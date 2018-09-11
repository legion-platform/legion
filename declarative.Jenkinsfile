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