#
#    Copyright 2019 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

FROM python:3.6.8

# Install python package dependencies and docker CLI
RUN apt-get update && apt-get install -y software-properties-common \
	&& apt-get install -y make build-essential libssl-dev libffi-dev zlib1g-dev libjpeg-dev git  \
  jq=1.5+dfsg-1.3 && apt-get clean all

RUN pip install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13

# Docker CLI (without engine, is used for testing)
ENV DOCKER_VERSION=18.03.1-ce
RUN  curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz \
  && tar xzvf docker-${DOCKER_VERSION}.tgz --strip 1 -C /usr/local/bin docker/docker \
  && rm docker-${DOCKER_VERSION}.tgz

# Install Kops
ENV KOPS_VERSION=1.11.0
RUN wget https://github.com/kubernetes/kops/releases/download/${KOPS_VERSION}/kops-linux-amd64 -qO /usr/local/bin/kops && \
    chmod a+x /usr/local/bin/kops

# Install kubectl
ENV KUBECTL_VERSION=v1.11.6
RUN curl -fsSLO https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    chmod a+x /usr/local/bin/kubectl

# Install Helm
ENV HELM_VERSION=v2.14.0
RUN curl -fsSLO https://kubernetes-helm.storage.googleapis.com/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    mkdir -p /tmp/helm && mv helm-${HELM_VERSION}-linux-amd64.tar.gz /tmp/helm && \
    tar xzf /tmp/helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -C /tmp/helm && \
    mv /tmp/helm/linux-amd64/helm /usr/local/bin/helm && rm -rf /tmp/helm

# Used for robot tests
COPY examples /opt/legion/

# Install python dependecies
COPY containers/pipeline-agent/Pipfile containers/pipeline-agent/Pipfile.lock /opt/legion/legion/
RUN  cd /opt/legion/legion && pipenv install --system --three
COPY legion/sdk/Pipfile legion/sdk/Pipfile.lock /opt/legion/legion/sdk/
RUN  cd /opt/legion/legion/sdk && pipenv install --system --three
COPY legion/services/Pipfile legion/services/Pipfile.lock /opt/legion/legion/services/
RUN  cd /opt/legion/legion/services && pipenv install --system --three
COPY legion/cli/Pipfile legion/cli/Pipfile.lock /opt/legion/legion/cli/
RUN  cd /opt/legion/legion/cli && pipenv install --system --three
COPY legion/robot/Pipfile legion/robot/Pipfile.lock /opt/legion/legion/robot/
RUN  cd /opt/legion/legion/robot && pipenv install --system --three
COPY legion/tests/unit/requirements/Pipfile legion/tests/unit/requirements/Pipfile.lock /opt/legion/legion/tests/unit/
RUN  cd /opt/legion/legion/tests/unit && pipenv install --system --three --dev
COPY legion/toolchains/python/Pipfile legion/toolchains/python/Pipfile.lock /opt/legion/legion/toolchains/python/
RUN  cd /opt/legion/legion/toolchains/python && pipenv install --system --three
COPY legion/jupyterlab-plugin/Pipfile legion/jupyterlab-plugin/Pipfile.lock /opt/legion/legion/jupyterlab-plugin/
RUN  cd /opt/legion/legion/jupyterlab-plugin && pipenv install --system --three

COPY scripts /opt/legion/scripts
RUN chmod -R a+x /opt/legion/scripts/*
COPY Makefile /opt/legion/Makefile
COPY docs /opt/legion/docs
COPY examples /opt/legion/examples
COPY legion /opt/legion/legion

RUN cd /opt/legion/ && make BUILD_PARAMS="--no-deps" install-all