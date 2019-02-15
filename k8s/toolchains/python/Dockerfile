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
ARG version=latest

FROM legion/legion-docker-agent:${version}

FROM legion/base-python-image:${version}

# Install Legion and custom scripts to image
COPY --from=0 /src/legion/dist/*.whl ./
COPY legion-doc.txt \
        /opt/legion/

COPY jupyter_notebook_config.py /etc/jupyter/

RUN pip3 install --disable-pip-version-check ./legion*.whl \
  && rm -f ./legion*.whl \
  && pip3 install --disable-pip-version-check ptvsd==4.2.2 \
  && echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/motd' >> /etc/bash.bashrc \
  && cat /opt/legion/legion-doc.txt > /etc/motd