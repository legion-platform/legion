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
# Args to build
ARG JUPYTERLAB_VERSION=0.35.6

# Image for building ready-to-distribute plugin frontend
FROM python:3.6.8-stretch AS plugin-frontend-rebuilder
ARG JUPYTERLAB_VERSION

ENV WORK_DIR="/opt/legion-plugin"
WORKDIR "${WORK_DIR}/"

RUN \
  apt-get update && \
  apt-get install -yqq apt-transport-https && \
  echo "deb https://deb.nodesource.com/node_10.x stretch main" > /etc/apt/sources.list.d/nodesource.list && \
  wget -qO- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
  echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list && \
  wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
  apt-get update && \
  apt-get install -yqq nodejs yarn && \
  pip install -U pip && pip install pipenv && \
  npm i -g npm@^6 && \
  rm -rf /var/lib/apt/lists/*

# Install jupyterlab
RUN pip3 install --disable-pip-version-check jupyterlab==$JUPYTERLAB_VERSION

COPY legion/jupyterlab-plugin/package.json \
     legion/jupyterlab-plugin/yarn.lock \
     "${WORK_DIR}/"

RUN yarn install --non-interactive --ignore-scripts

COPY legion/jupyterlab-plugin/tsconfig.json \
     legion/jupyterlab-plugin/tslint.json \
     "${WORK_DIR}/"
COPY legion/jupyterlab-plugin/src "${WORK_DIR}/src"
COPY legion/jupyterlab-plugin/style "${WORK_DIR}/style"
COPY legion/jupyterlab-plugin/jupyter-config "${WORK_DIR}/jupyter-config"

RUN yarn build && yarn lint && npm pack .

# Run installation w/o any code to warm up nodejs cache
RUN jupyter lab build && mv /opt/legion-plugin/jupyter-legion-*.tgz jupyter_legion.tgz

RUN jupyter labextension install --no-build jupyter_legion.tgz && \
    jupyter labextension install @jupyterlab/git jupyterlab_toastify jupyterlab-jupytext@0.19

# We have to remove folder with node_modules and other build-related staff that is not required for running
RUN rm -rf /usr/local/share/jupyter/lab/staging

# Main image
FROM python:3.6.8-stretch
ARG JUPYTERLAB_VERSION
SHELL ["/bin/bash", "-c"]

ENV WORK_DIR="/opt/legion"
WORKDIR "${WORK_DIR}/"
ARG MINICONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh
# Install conda
RUN apt-get update -y && apt-get install -y wget && \
    wget https://github.com/krallin/tini/releases/download/v0.18.0/tini-amd64 -qO /bin/tiny && \
    chmod a+x /bin/tiny && \
    wget ${MINICONDA_URL} -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    ln -s /opt/conda/bin/conda /usr/bin/conda
RUN  pip install --disable-pip-version-check --upgrade pip==19.2.2 pipenv==2018.10.13 ptvsd==4.2.2 jupyterlab==$JUPYTERLAB_VERSION

COPY legion/sdk/Pipfile legion/sdk/Pipfile.lock "${WORK_DIR}/legion/sdk/"
RUN  cd legion/sdk && pipenv install --system --three
COPY legion/cli/Pipfile legion/cli/Pipfile.lock "${WORK_DIR}/legion/cli/"
RUN  cd legion/cli && pipenv install --system --three

COPY --from=plugin-frontend-rebuilder /usr/local/share/jupyter /usr/local/share/jupyter

COPY containers/jupyterlab/legion-doc.txt /opt/legion/
COPY containers/jupyterlab/conda-update.sh /usr/bin/conda-update

COPY legion/sdk "${WORK_DIR}/legion/sdk"
COPY legion/cli "${WORK_DIR}/legion/cli"
COPY legion/jupyterlab-plugin "${WORK_DIR}/legion/jupyterlab-plugin"

RUN pip3 install --no-deps -e legion/sdk && \
    pip3 install --no-deps -e legion/cli && \
    pip3 install -e legion/jupyterlab-plugin && \
    pip3 install jupyterlab-git jupytext==1.1.7 && \
    jupyter serverextension enable --py legion.jupyterlab && \
    jupyter serverextension enable --py jupyterlab_git && \
    jupyter nbextension install --py jupytext && \
    jupyter nbextension enable --py jupytext && \
    echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/motd' >> /etc/bash.bashrc && \
    cat /opt/legion/legion-doc.txt > /etc/motd

COPY containers/jupyterlab/jupyter_notebook_config.py /etc/jupyter/
