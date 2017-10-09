FROM jenkins/jenkins:lts

USER root
RUN apt-get update
RUN apt-get install --yes \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian jessie stable"

RUN apt-get update
RUN apt-get install --yes docker-ce
USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV JENKINS_OPTS="--prefix=/jenkins"

COPY security.groovy /usr/share/jenkins/ref/init.groovy.d/security.groovy
COPY create_jobs.groovy /usr/share/jenkins/ref/init.groovy.d/create_jobs.groovy

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
