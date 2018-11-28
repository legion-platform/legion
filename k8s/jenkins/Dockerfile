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

# Copy plugins installation script & set run mode
COPY scripts/install-plugins.sh /usr/local/bin/install-plugins.sh
RUN chmod +x /usr/local/bin/install-plugins.sh

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

# Prepare env variables from build arguments
ARG update_center_url="https://updates.jenkins.io"
ENV JENKINS_UC=$update_center_url

ARG update_center_download_url="https://updates.jenkins.io/download"
ENV JENKINS_UC_DOWNLOAD=$update_center_download_url

ARG update_center_experimental_url="https://updates.jenkins.io/experimental"
ENV JENKINS_UC_EXPERIMENTAL=$update_center_experimental_url

# Install plugins
USER jenkins

RUN echo "INSTALLING BASE PLUGINS:" && \
    cat /usr/share/jenkins/ref/plugins.txt && \
    /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt

# Non-cached section

ARG legion_plugin_version="latest"
ENV JENKINS_PLUGIN_VERSION=$legion_plugin_version

RUN rm -f /usr/share/jenkins/ref/plugins.txt && \
    echo "legion-jenkins-plugin:experimental=$JENKINS_PLUGIN_VERSION" > /usr/share/jenkins/ref/plugins.txt && \
    echo "INSTALLING LEGION PLUGINS:" && \
    cat /usr/share/jenkins/ref/plugins.txt && \
    /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt
