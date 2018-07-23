#   Copyright 2018 Bruno Faria
#   Repository: https://github.com/brunocfnba/docker-airflow
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

#Airflow Image
FROM ubuntu:16.04

ENV AIRFLOW_HOME /home/airflow

ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN apt-get update && apt-get install -y \
 wget \
 python3.5 \
 python3.5-dev \
 vim \
 cron \
 libkrb5-dev \
 libsasl2-dev \
 libssl-dev \
 libffi-dev \
 build-essential \
 libblas-dev \
 liblapack-dev \
 python3-pip \
 apt-utils \
 curl \
 netcat \
 iputils-ping \
 openssh-client \
 python-requests \
 libpq-dev \
 libmysqlclient-dev \
 sshpass \
 sudo \
 redis-tools \
 locales

RUN locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8

RUN service cron stop \
 && useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow

RUN pip3 install --upgrade pip==9.0.3 \
 && pip3 install Cython \
 && pip3 install cryptography \
 && pip3 install apache-airflow[postgres,jdbc,password,mysql,celery,redis,s3]==1.9.0 \
 && pip3 install pyOpenSSL \
 && pip3 install ndg-httpsclient \
 && pip3 install pyasn1 \
 && pip3 install psycopg2-binary \
 && pip3 install redis \
 && pip3 install hiredis

RUN apt-get install -y git && \
    cd  /home/airflow && \
    mkdir temp && cd temp && \
    git clone https://github.com/teamclairvoyant/airflow-rest-api-plugin.git && \
    mkdir -p /home/airflow/plugins && \
    touch /home/airflow/plugins/__init__.py && \
    mv /home/airflow/temp/airflow-rest-api-plugin/plugins /home/airflow/plugins/rest_api && \
    rm -rf /home/airflow/temp


RUN rm -rf \
    /var/lib/apt/lists/* \
    /tmp/* \
    /var/tmp/* \
    /usr/share/man \
    /usr/share/doc \
    /usr/share/doc-base


COPY entrypoint.sh /home/airflow/init.sh

# setup locale
RUN locale-gen en_CA.UTF-8
COPY default_locale /etc/default/locale
RUN chmod 0755 /etc/default/locale
ENV LC_ALL=en_CA.UTF-8
ENV LANG=en_CA.UTF-8
ENV LANGUAGE=en_CA.UTF-8

COPY requirements.txt /home/airflow/requirements.txt
RUN pip install -r /home/airflow/requirements.txt && \
    pip install $pip_extra_index_params legion$pip_legion_version_string && \
    pip install $pip_extra_index_params legion_airflow$pip_legion_version_string

RUN chown -R airflow: ${AIRFLOW_HOME} && chmod -R 775 ${AIRFLOW_HOME} && \
    chmod a+x /home/airflow/init.sh

COPY create_secrets.py /home/airflow/create_secrets.py

EXPOSE 8080

USER airflow
WORKDIR ${AIRFLOW_HOME}

ENTRYPOINT ["sh", "/home/airflow/init.sh"]
