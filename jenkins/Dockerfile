FROM jenkins/jenkins:lts

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV JENKINS_OPTS="--prefix=/jenkins"

COPY security.groovy /usr/share/jenkins/ref/init.groovy.d/security.groovy
COPY create_jobs.groovy /usr/share/jenkins/ref/init.groovy.d/create_jobs.groovy

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
