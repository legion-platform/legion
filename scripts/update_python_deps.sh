#!/usr/bin/env bash
set -e

PROJECTS="legion/sdk legion/cli legion/services legion/robot legion/toolchains/python legion/tests/unit/requirements containers/pipeline-agent legion/jupyterlab-plugin"
ROOT_DIR="$(pwd)"

for project in ${PROJECTS}
do
    echo "Update dependencies in ${ROOT_DIR}/${project}"
    cd "${ROOT_DIR}/${project}"

    pipenv update
done