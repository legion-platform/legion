#!/usr/bin/env bash

docker run -ti --rm \
   --net=host \
   -e "PYDEVD_HOST=$PYDEVD_HOST" \
   -e "PYDEVD_PORT=$PYDEVD_PORT" \
   -e "MODEL_FILE=/model.bin" \
   -v /home/kirill/work/legion-root:/work-directory \
   -v /var/run/docker.sock:/var/run/docker.sock \
   nexus.cc.epm.kharlamov.biz:443/legion/base-python-image:0.9.0-20181115095551.1049.fc721cf \
   sh -c "pip install --extra-index-url https://nexus.cc.epm.kharlamov.biz/repository/pypi-hosted/simple legion==0.9.0-20181115095551.1049.fc721cf ptvsd==4.2.0 && cd /work-directory && bash"