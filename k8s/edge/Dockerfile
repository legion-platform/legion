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
FROM openresty/openresty:1.13.6.2-bionic

RUN apt update -y && \
    apt install -y openssl libffi-dev libssl-dev \
       python3 python3-dev python3-pip g++ \
       ca-certificates gnupg openssl git curl dumb-init

RUN    luarocks install lua-resty-statsd          3.0.3-1 \
    && luarocks install lua-cmsgpack              0.4.0 \
    && luarocks install lua-cjson                 2.1.0.6-1 \
    && luarocks install basexx                    0.4.0-1 \
    && luarocks install lua-resty-jwt             0.2.0-0 \
    && luarocks install lua-resty-jit-uuid        0.0.7-1 \
    && luarocks install lua-resty-reqargs         1.4-1

RUN pip3 install --disable-pip-version-check --upgrade pip==18.1 pipenv==2018.10.13

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8
RUN pipenv install -v --system --deploy --three

# Install Legion
ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN python3 -m pip install $pip_extra_index_params legion$pip_legion_version_string

WORKDIR /

RUN python3 -m compileall /usr/local/lib/python3.6/dist-packages

# Staff
ADD start.sh /start.sh
ADD nginx-jwt.lua \
    statistics_sender.lua \
    blacklisted_tokens.lua \
    fluentd_logger.lua \
    request_id_generator.lua \
    edge.lua \
      /usr/local/openresty/luajit/

ADD nginx.conf.ltmpl /nginx.conf.ltmpl

ENTRYPOINT ["dumb-init", "--"]
CMD ["/start.sh"]