node {
    def legion = load legion()

    legion.pod(cpu: '7') {
        stage('System info'){
            sh "df -h"
            sh "cat /proc/cpuinfo"
            sh "free -g"
        }
    }
}
