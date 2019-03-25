FROM python:3.6.8

# Install python package dependencies and docker CLI
RUN apt-get update && apt-get install -y software-properties-common \
	&& apt-get install -y build-essential libssl-dev libffi-dev zlib1g-dev libjpeg-dev git  \
  jq=1.5+dfsg-1.3 xvfb=2:1.19.2-1+deb9u5 \
  # firefox is not pinned deliberately because debian repo constantly rotate intermediate releases
  firefox-esr \
	&& apt-get clean all

RUN pip install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13

# Docker CLI (without engine, is used for testing)
ENV DOCKER_VERSION=18.03.1-ce
RUN  curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz \
  && tar xzvf docker-${DOCKER_VERSION}.tgz --strip 1 -C /usr/local/bin docker/docker \
  && rm docker-${DOCKER_VERSION}.tgz

# Install updated firefox version
ENV FIREFOX_VERSION=64.0.2
ADD https://download.mozilla.org/?product=firefox-${FIREFOX_VERSION}&os=linux64&lang=en-US firefox.tar.bz2
RUN mkdir /opt/firefox && \
    tar xjf firefox.tar.bz2 -C /opt/firefox/ && \
    rm -rf /usr/bin/firefox && \
    ln -s /opt/firefox/firefox/firefox /usr/bin/firefox && \
    rm -rf firefox.tar.bz2
    
# Install Geckodriver for selenium tests
ENV GECKO_VERSION=0.22.0
ADD https://github.com/mozilla/geckodriver/releases/download/v${GECKO_VERSION}/geckodriver-v${GECKO_VERSION}-linux64.tar.gz geckodriver.tar.gz
RUN tar xzf geckodriver.tar.gz -C /usr/local/bin/ && \
    rm -rf geckodriver*
RUN chmod a+x /usr/local/bin/geckodriver

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

# Install requirements for legion package
ADD legion/requirements/Pipfile /src/requirements/legion/Pipfile
ADD legion/requirements/Pipfile.lock /src/requirements/legion/Pipfile.lock
RUN cd /src/requirements/legion && pipenv install --system --dev

# Install requirements for legion_test package
ADD legion_test/requirements/Pipfile /src/requirements/legion_test/Pipfile
ADD legion_test/requirements/Pipfile.lock /src/requirements/legion_test/Pipfile.lock
RUN cd /src/requirements/legion_test && pipenv install --system --dev

# Install additional tools for build purposes
RUN pip install Sphinx==1.8.0 sphinx_rtd_theme==0.4.1 sphinx-autobuild==0.7.1 \
    recommonmark==0.4.0 twine==1.11.0 ansible==2.6.4 awscli==1.16.19 yq==2.7.2

# Add sources

ADD legion /src/legion
RUN cd /src/legion \
  && python setup.py collect_data \
  && python setup.py develop \
  && python setup.py sdist \
  && python setup.py bdist_wheel

ADD legion_test /src/legion_test
RUN cp /src/legion/legion/version.py /src/legion_test/legion_test/version.py \
  && cd /src/legion_test \
  && python setup.py develop \
  && python setup.py sdist \
  && python setup.py bdist_wheel
