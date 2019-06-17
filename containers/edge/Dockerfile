#
#    Copyright 2019 EPAM Systems
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
FROM openresty/openresty:1.13.6.2-bionic

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    WORK_DIR="/opt/legion" \
    NGINX_DIR="/usr/local/openresty/nginx" \
    DEBIAN_FRONTEND=noninteractive

WORKDIR "${WORK_DIR}/"

RUN apt update -y && \
    apt install -y openssl libffi-dev libssl-dev \
       python3 python3-dev python3-pip g++ \
       ca-certificates gnupg openssl git curl dumb-init libnginx-mod-http-lua

RUN    luarocks install lua-resty-statsd          3.0.3-1 \
    && luarocks install lua-cmsgpack              0.4.0 \
    && luarocks install lua-cjson                 2.1.0.6-1 \
    && luarocks install basexx                    0.4.0-1 \
    && luarocks install lua-resty-jwt             0.2.0-0 \
    && luarocks install lua-resty-jit-uuid        0.0.7-1 \
    && luarocks install lua-resty-reqargs         1.4-1 \
    && luarocks install nginx-lua-prometheus      0.20181120-2

RUN pip3 install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13

COPY legion/sdk/Pipfile legion/sdk/Pipfile.lock "${WORK_DIR}/legion/sdk/"
RUN  cd legion/sdk && pipenv install --system --three
COPY legion/services/Pipfile legion/services/Pipfile.lock "${WORK_DIR}/legion/services/"
RUN  cd legion/services && pipenv install --system --three

COPY legion/sdk "${WORK_DIR}/legion/sdk"
COPY legion/services "${WORK_DIR}/legion/services"

RUN pip3 install --no-deps -e "${WORK_DIR}/legion/sdk" && \
    pip3 install --no-deps -e "${WORK_DIR}/legion/services"

COPY containers/edge/nginx.conf.ltmpl "${WORK_DIR}/"
COPY containers/edge/lua/ /usr/local/openresty/luajit/
COPY containers/edge/start.sh /usr/bin/

RUN cp /usr/local/openresty/luajit/share/lua/5.1/nginx/prometheus.lua /usr/local/openresty/luajit/

ENTRYPOINT ["dumb-init", "--"]
CMD ["start.sh"]