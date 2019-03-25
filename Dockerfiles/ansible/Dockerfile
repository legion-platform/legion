FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# install system utilities
RUN apt-get update && apt-get install -y \
    python-pip apt-transport-https bash curl tar openssh-client \
    sshpass git ca-certificates python-pip apt-utils locales && \
    apt-get clean && apt-get autoclean

# setup locale
RUN locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8
COPY k8s/ansible/default_locale /etc/default/locale
RUN chmod 0755 /etc/default/locale
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

# Install ansible from pip
RUN pip install ansible==2.7.2

 # Install ansible dependencies
RUN apt-get install -y \
    python-yaml=3.12-1build2 python-jinja2=2.10-1 python-boto=2.44.0-1ubuntu2 python-boto3=1.4.2-1 \
    python-psycopg2=2.7.4-1 postgresql-client=10+190 python-crypto=2.6.1-8ubuntu2 \
    python-cryptography=2.1.4-1ubuntu1.2 awscli=1.14.44-1ubuntu1 && \
    apt-get clean && apt-get autoclean

# Configure ansible
RUN mkdir -p /etc/ansible/ && /bin/echo -e "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts

# Install Kops
ENV KOPS_VERSION=1.11.0
ADD https://github.com/kubernetes/kops/releases/download/${KOPS_VERSION}/kops-linux-amd64 /usr/local/bin/kops
RUN chmod a+x /usr/local/bin/kops

# Install kubectl
ENV KUBECTL_VERSION=v1.11.6
ADD https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl /usr/local/bin/kubectl
RUN chmod a+x /usr/local/bin/kubectl

# Install Helm
ENV HELM_VERSION=v2.10.0
ADD https://kubernetes-helm.storage.googleapis.com/helm-${HELM_VERSION}-linux-amd64.tar.gz /tmp/helm/
RUN tar xzf /tmp/helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -C /tmp/helm && \
    mv /tmp/helm/linux-amd64/helm /usr/local/bin/helm && rm -rf /tmp/helm

# Deploy Legion
COPY deploy/ansible /opt/legion/deploy/ansible
COPY deploy/profiles/profiles_template.yaml /opt/legion/deploy/profiles/profiles_template.yaml
COPY deploy/profiles/secrets_template.yaml /opt/legion/deploy/profiles/secrets_template.yaml

WORKDIR /opt/legion/deploy/
