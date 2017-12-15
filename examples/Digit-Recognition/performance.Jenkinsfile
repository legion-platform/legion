node {
    def drun = load drun()

    drun.container('drun.kharlamov.biz/drun/base-python-image:latest') {
        stage('clone'){
            git url: 'https://github.com/akharlamov/drun-examples.git'
            sh '''
            pip install -i https://drun.kharlamov.biz/pypi/ drun
            '''
        }
        stage('run performance tests'){
            sh "cd Digit-Recognition/performance/ && locust -f test_basic.py --no-web -c ${params.testUsers} -r ${params.testHatchRate} -n ${params.testRequestsCount} --host ${params.host} --only-summary --logfile locust.log"
            archiveArtifacts 'Digit-Recognition/performance/locust.log'
        }
    }
}