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
FROM jenkins/jenkins:2.121.3

USER root
RUN apt-get update && apt-get install --yes \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian jessie stable"

RUN apt-get update && apt-get install --yes docker-ce

# Copy bootstrap scripts
COPY scripts/security.groovy /usr/share/jenkins/ref/init.groovy.d/security.groovy
COPY scripts/create_jobs.groovy /usr/share/jenkins/ref/init.groovy.d/create_jobs.groovy

# Copy plugins installation script
COPY scripts/install-plugins.sh /usr/local/bin/install-plugins.sh

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

# Prepare env variables from build arguments
ARG JENKINS_UC="https://updates.jenkins.io"
ENV JENKINS_UC=$JENKINS_UC

ARG JENKINS_UC_DOWNLOAD="https://updates.jenkins.io/download"
ENV JENKINS_UC_DOWNLOAD=$JENKINS_UC_DOWNLOAD

ARG JENKINS_UC_EXPERIMENTAL="https://updates.jenkins.io/experimental"
ENV JENKINS_UC_EXPERIMENTAL=$JENKINS_UC_EXPERIMENTAL

RUN echo "INSTALLING BASE PLUGINS:" && \
    cat /usr/share/jenkins/ref/plugins.txt && \
    chmod +x /usr/local/bin/install-plugins.sh

# Non-cached section

ARG JENKINS_PLUGIN_VERSION="latest"
ENV JENKINS_PLUGIN_VERSION=$JENKINS_PLUGIN_VERSION

RUN "printenv"

RUN echo "legion-jenkins-plugin:experimental=$JENKINS_PLUGIN_VERSION" > /usr/share/jenkins/ref/plugins.txt && \
    echo "INSTALLING LEGION PLUGINS:" && \
    cat /usr/share/jenkins/ref/plugins.txt && \
    chmod +x /usr/local/bin/install-plugins.sh

# Install plugins
USER jenkins
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
