node {
    def legion = load legion()

    legion.pod(cpu: '7', image: 'alpine:3.8') {
        stage('System info'){
            sh "df -h"
            sh "cat /proc/cpuinfo"
            sh "free -g"
        }
    }
}
