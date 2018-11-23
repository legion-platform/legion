FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# add ansible repository
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:ansible/ansible-2.7

# install ansible with system utilities
RUN apt-get update && apt-get install -y \
    ansible=2.7.2-1ppa~bionic apt-transport-https bash curl tar openssh-client \
    sshpass git ca-certificates python-pip apt-utils locales

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
    postgresql-client python-crypto python-cryptography 

# Configure ansible
RUN /bin/echo -e "[local]\nlocalhost ansible_connection=local" > /etc/ansible/hosts

# Install Helm
ADD https://raw.githubusercontent.com/helm/helm/v2.11.0/scripts/get /tmp/get_helm.sh
RUN bash /tmp/get_helm.sh

# Cleanup temp resources
RUN apt-get clean && apt-get autoclean

# Deploy Legion
COPY deploy/ansible /opt/legion/deploy/ansible
COPY deploy/helms /opt/legion/deploy/helms
COPY deploy/profiles /opt/legion/deploy/profiles

WORKDIR /opt/deploy