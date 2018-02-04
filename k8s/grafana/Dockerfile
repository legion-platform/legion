#
#   Copyright 2017 EPAM Systems
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
#
FROM grafana/grafana:4.5.0

RUN apt-get update && \
    apt-get install --yes \
    python3 python3-pip  && \
    pip3 install Jinja2>=2.9 && \
    apt-get clean

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod a+rwx /entrypoint.sh

ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN pip3 install --force-reinstall -U pip
RUN pip3 install $pip_extra_index_params legion_test$pip_legion_version_string

ENTRYPOINT ["/entrypoint.sh"]

