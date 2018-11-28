FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# add ansible repository
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:ansible/ansible-2.7

# install ansible with system utilities
RUN apt-get update && apt-get install -y \
    ansible=2.7.2-1ppa~bionic apt-transport-https bash curl tar openssh-client \
    sshpass git ca-certificates python-pip apt-utils locales && \
    apt-get clean && apt-get autoclean

# setup locale
RUN locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8
COPY k8s/ansible/default_locale /etc/default/locale
RUN chmod 0755 /etc/default/locale
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

 # Install ansible dependencies
RUN apt-get install -y \
    python-yaml python-jinja2 python-boto python-boto3 python-psycopg2 \
    postgresql-client python-crypto python-cryptography && \
    apt-get clean && apt-get autoclean

# Configure ansible
RUN /bin/echo -e "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts

# Install Kops
ADD https://github.com/kubernetes/kops/releases/download/1.10.0/kops-linux-amd64 /usr/local/bin/kops
RUN chmod a+x /usr/local/bin/kops

# Install kubectl
ADD https://storage.googleapis.com/kubernetes-release/release/v1.10.6/bin/linux/amd64/kubectl /usr/local/bin/kubectl
RUN chmod a+x /usr/local/bin/kubectl

# Install Helm
ENV HELM_VERSION=v2.10.0
ADD https://kubernetes-helm.storage.googleapis.com/helm-${HELM_VERSION}-linux-amd64.tar.gz /tmp/helm/
RUN tar xzf /tmp/helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -C /tmp/helm && \
    mv /tmp/helm/linux-amd64/helm /usr/local/bin/helm && rm -rf /tmp/helm

# Deploy Legion
COPY deploy/ansible /opt/legion/deploy/ansible
COPY deploy/helms /opt/legion/deploy/helms
COPY deploy/profiles/profiles_template.yaml /opt/legion/deploy/profiles/profiles_template.yaml
COPY deploy/profiles/secrets_template.yaml /opt/legion/deploy/profiles/secrets_template.yaml

WORKDIR /opt/legion/deploy/