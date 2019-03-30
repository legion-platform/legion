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
ENV HELM_VERSION=v2.10.0
RUN curl -fsSLO https://kubernetes-helm.storage.googleapis.com/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    mkdir -p /tmp/helm && mv helm-${HELM_VERSION}-linux-amd64.tar.gz /tmp/helm && \
    tar xzf /tmp/helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -C /tmp/helm && \
    mv /tmp/helm/linux-amd64/helm /usr/local/bin/helm && rm -rf /tmp/helm

# Install python dependecies
COPY containers/pipeline-agent/Pipfile containers/pipeline-agent/Pipfile.lock /src/legion/
RUN  cd /src/legion && pipenv install --system --three
COPY legion/sdk/Pipfile legion/sdk/Pipfile.lock /src/legion/sdk/
RUN  cd /src/legion/sdk && pipenv install --system --three
COPY legion/services/Pipfile legion/services/Pipfile.lock /src/legion/services/
RUN  cd /src/legion/services && pipenv install --system --three
COPY legion/cli/Pipfile legion/cli/Pipfile.lock /src/legion/cli/
RUN  cd /src/legion/cli && pipenv install --system --three
COPY legion/robot/Pipfile legion/robot/Pipfile.lock /src/legion/robot/
RUN  cd /src/legion/robot && pipenv install --system --three
COPY legion/tests/unit/requirements/Pipfile legion/tests/unit/requirements/Pipfile.lock /src/legion/tests/unit/
RUN  cd /src/legion/tests/unit && pipenv install --system --three --dev
COPY legion/toolchains/python/Pipfile legion/toolchains/python/Pipfile.lock /src/legion/toolchains/python/
RUN  cd /src/legion/toolchains/python && pipenv install --system --three

COPY scripts /src/scripts
RUN chmod -R a+x /src/scripts/*
COPY Makefile /src/Makefile
COPY docs /src/docs
COPY legion /src/legion

RUN cd /src/ && make BUILD_PARAMS="--no-deps" install-all