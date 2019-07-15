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
FROM python:3.6.8-stretch
ARG JUPYTERLAB_VERSION

ENV WORK_DIR="/opt/legion"
WORKDIR "${WORK_DIR}/"

RUN wget https://github.com/krallin/tini/releases/download/v0.18.0/tini-amd64 -qO /bin/tiny && \
    chmod a+x /bin/tiny

RUN pip3 install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13

COPY legion/packer/rest/Pipfile legion/packer/rest/Pipfile.lock "${WORK_DIR}/legion/packer/rest/"
RUN  cd legion/packer/rest && pipenv install --system --three

COPY legion/packer/rest "${WORK_DIR}/legion/packer/rest"

RUN pip3 install --no-deps -e legion/packer/rest
