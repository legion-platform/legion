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
FROM python:3.6.8-stretch

EXPOSE 5000

RUN pip3 install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13 uwsgi==2.0.18

COPY legion/sdk/Pipfile legion/sdk/Pipfile.lock "${WORK_DIR}/legion/sdk/"
RUN  cd legion/sdk && pipenv install --system --three
COPY legion/services/Pipfile legion/services/Pipfile.lock "${WORK_DIR}/legion/services/"
RUN  cd legion/services && pipenv install --system --three

COPY legion/sdk "${WORK_DIR}/legion/sdk"
COPY legion/services "${WORK_DIR}/legion/services"

RUN pip3 install --no-deps -e "${WORK_DIR}/legion/sdk" && \
    pip3 install --no-deps -e "${WORK_DIR}/legion/services"

COPY containers/edi/edi_uwsgi.ini containers/edi/model_builder_uwsgi.ini /etc/uwsgi/

ENTRYPOINT []
CMD ["/usr/local/bin/uwsgi", "--strict", "--ini", "/etc/uwsgi/edi_uwsgi.ini"]