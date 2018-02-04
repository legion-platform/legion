#
#   Copyright 2017 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
FROM jenkins/jenkins:lts

USER root
RUN apt-get update && apt-get install --yes \
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

ENV JENKINS_OPTS="--prefix=/jenkins"

COPY security.groovy /usr/share/jenkins/ref/init.groovy.d/security.groovy
COPY create_jobs.groovy /usr/share/jenkins/ref/init.groovy.d/create_jobs.groovy

ENV JENKINS_UC_EXPERIMENTAL="http://nexus.epm.kharlamov.biz/jenkins"
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
