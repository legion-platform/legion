#
#    Copyright 2017 EPAM Systems
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
FROM drun/base-python-image

RUN apt-get update && apt-get install --yes \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian jessie stable"

RUN apt-get update && apt-get install --yes docker-ce


ARG pip_extra_index_params=""
ARG pip_drun_version_string=""

RUN pip install $pip_extra_index_params drun$pip_drun_version_string

ENV TINI_VERSION v0.16.1
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

COPY chmod-docker-and-run-edi.sh /usr/local/bin/chmod-docker-and-run-edi.sh
RUN chmod a+rwx /usr/local/bin/chmod-docker-and-run-edi.sh
CMD ["/usr/local/bin/chmod-docker-and-run-edi.sh"]