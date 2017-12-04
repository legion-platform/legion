pipeline {
	agent { 
		docker {
			image 'drun.kharlamov.biz/drun/base-python-image:latest'
			args '-v drun:/drun -u 0:0 --network=drun_drun_root -e "DOCKER_TLS_VERIFY=1" -e "DOCKER_HOST=${DOCKER_HOST}" -e "DOCKER_CERT_PATH=/home/jenkins/.docker/" -e "MODEL_SERVER_URL=http://edge:90"'
		}
	}
	environment {
        def notebookName = 'Recognizing digits.ipynb'
        def scriptFile = Jenkins.instance.getItemByFullName(env.JOB_NAME).definition.getScriptPath()
        def rootDir = scriptFile.substring(0, scriptFile.lastIndexOf('/'))
	}
	stages {
		stage('install drun'){
		    steps {
				sh '''
				pip install -i https://drun.kharlamov.biz/pypi/ drun
				'''
			}
		}
		stage('run performance tests'){
		    steps {
		        sh "cd ${rootDir}/performance/ && locust -f test_basic.py --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${params.host} --only-summary --logfile locust.log"
				archiveArtifacts rootDir + '/performance/locust.log'
		    }
		}
	}
}
