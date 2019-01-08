FROM python:3.6@sha256:4f309bf7925db6e21f7f1b7db99aa76576007441136f5e22d4fc422491255872

# Docker CLI (without engine, is used for testing)
ENV DOCKERVERSION=18.03.1-ce

# Install python package dependencies and docker CLI
RUN apt-get update && apt-get install -y software-properties-common \
	&& apt-get install -y build-essential libssl-dev libffi-dev zlib1g-dev libjpeg-dev git jq=1.5+dfsg-1.3\
	&& apt-get clean all
  && curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
  && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 -C /usr/local/bin docker/docker \
  && rm docker-${DOCKERVERSION}.tgz

# Install Kops
ENV KOPS_VERSION=1.10.0
ADD https://github.com/kubernetes/kops/releases/download/${KOPS_VERSION}/kops-linux-amd64 /usr/local/bin/kops
RUN chmod a+x /usr/local/bin/kops

# Install kubectl
ENV KUBECTL_VERSION=v1.10.6
ADD https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl /usr/local/bin/kubectl
RUN chmod a+x /usr/local/bin/kubectl

# Install Helm
ENV HELM_VERSION=v2.10.0
ADD https://kubernetes-helm.storage.googleapis.com/helm-${HELM_VERSION}-linux-amd64.tar.gz /tmp/helm/
RUN tar xzf /tmp/helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -C /tmp/helm && \
    mv /tmp/helm/linux-amd64/helm /usr/local/bin/helm && rm -rf /tmp/helm

RUN pip install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13 

# Install additional tools for build purposes
RUN pip install Sphinx==1.8.0 sphinx_rtd_theme==0.4.1 sphinx-autobuild==0.7.1 \
  recommonmark==0.4.0 twine==1.11.0 awscli==1.16.85 ansible==2.7.2 yq==2.7.1

# Add sources
ADD legion /src/legion
RUN cd /src/legion/requirements && pipenv install --system --dev
RUN cd /src/legion \
  && python setup.py collect_data \
  && python setup.py develop \
  && python setup.py sdist \
  && python setup.py bdist_wheel

ADD legion_test /src/legion_test
RUN cd /src/legion_test/requirements && pipenv install --system --dev
RUN cp /src/legion/legion/version.py /src/legion_test/legion_test/version.py \
  && cd /src/legion_test \
  && python setup.py develop \
  && python setup.py sdist \
  && python setup.py bdist_wheel

ADD legion_airflow /src/legion_airflow
RUN cd /src/legion_airflow/requirements && pipenv install --system --dev
RUN cd /src/legion_airflow \
  && cp /src/legion/legion/version.py /src/legion_airflow/legion_airflow/version.py \
  && python setup.py develop \
  && python setup.py sdist \
  && python setup.py bdist_wheel