#
#    Copyright 2018 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
FROM ubuntu:18.04

ENV DEBIAN_FRONTEND="noninteractive" \
    LANG="C.UTF-8" \
    LANGUAGE="C:en" \
    LC_ALL="C.UTF-8" \
    WORK_DIR="/opt/legion"

WORKDIR "${WORK_DIR}/"
ARG MINICONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh

RUN apt-get update -qq && \
    apt-get install -y python3.6 wget curl python3-pip vim software-properties-common uidmap && \
    add-apt-repository -y ppa:projectatomic/ppa && \
    apt-get update -qq && \
    apt-get -qq -y install runc buildah iptables libdevmapper-event1.02.1

RUN wget https://github.com/krallin/tini/releases/download/v0.18.0/tini-amd64 -qO /bin/tiny && \
    chmod a+x /bin/tiny

RUN pip3 install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13

COPY legion/sdk/Pipfile legion/sdk/Pipfile.lock "${WORK_DIR}/legion/sdk/"
RUN  cd legion/sdk && pipenv install --system --three
COPY legion/packager/rest/Pipfile legion/packager/rest/Pipfile.lock "${WORK_DIR}/legion/packager/rest/"
RUN  cd legion/packager/rest && pipenv install --system --three

COPY legion/sdk "${WORK_DIR}/legion/sdk"
RUN pip3 install --no-deps -e legion/sdk
COPY legion/packager/rest "${WORK_DIR}/legion/packager/rest"
RUN pip3 install --no-deps -e legion/packager/rest

COPY containers/ai-packagers/rest/registries.conf \
     containers/ai-packagers/rest/storage.conf \
       /etc/containers/
