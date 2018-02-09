node {
    def legion = load legion()

    legion.container(null) {
        stage('clone repo') {
            checkout scm
        }

        stage('run perf tests'){
            legion.runPerformanceTests('test_basic.py')
        }
    }
}
