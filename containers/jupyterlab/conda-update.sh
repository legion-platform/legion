#!/usr/bin/env bash
set -e
set -o xtrace

CONDA_ENV_PATH=${2}
ENV_NAME=$(basename "$(dirname "${CONDA_ENV_PATH}")")

. /opt/conda/etc/profile.d/conda.sh
conda create -n "${ENV_NAME}" python=3.6 -y || true
conda activate "${ENV_NAME}"
conda env update -n "${ENV_NAME}" -f "${CONDA_ENV_PATH}"
pip install ipykernel || true
python -m ipykernel install --name "${ENV_NAME}" || true
