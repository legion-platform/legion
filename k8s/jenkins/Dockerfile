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

RUN apt-get update && apt-get install --yes docker-ce

# Copy bootstrap scripts
COPY scripts/security.groovy /usr/share/jenkins/ref/init.groovy.d/security.groovy
COPY scripts/create_jobs.groovy /usr/share/jenkins/ref/init.groovy.d/create_jobs.groovy
COPY scripts/slack_notifier.groovy /usr/share/jenkins/ref/init.groovy.d/slack_notifier.groovy

# Copy plugins installation script
COPY scripts/install-plugins.sh /usr/local/bin/install-plugins.sh

# Prepare plugins
ARG jenkins_plugin_server="http://nexus-local.cc.epm.kharlamov.biz/jenkins"
ENV JENKINS_UC_EXPERIMENTAL=$jenkins_plugin_server
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

ARG jenkins_plugin_version="latest"
ENV JENKINS_PLUGIN_VERSION=$jenkins_plugin_version
RUN echo "legion-jenkins-plugin:experimental=$JENKINS_PLUGIN_VERSION" >> /usr/share/jenkins/ref/plugins.txt && \
    echo "INSTALLING NEXT PLUGINS:" && \
    cat /usr/share/jenkins/ref/plugins.txt && \
    chmod +x /usr/local/bin/install-plugins.sh

# Install plugins
USER jenkins
RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
