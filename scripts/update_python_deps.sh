#!/usr/bin/env bash
set -e

PROJECTS="legion/sdk legion/cli legion/robot legion/packager/rest containers/pipeline-agent legion/jupyterlab-plugin"
ROOT_DIR="$(pwd)"

for project in ${PROJECTS}
do
    echo "Update dependencies in ${ROOT_DIR}/${project}"
    cd "${ROOT_DIR}/${project}"

    pipenv update
done
