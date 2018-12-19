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
FROM openresty/openresty:1.13.6.2-alpine-fat

ENV DUMB_INIT_VERSION 1.2.0

# Dumb-init, python3, lua
RUN set -ex \
  && apk add --no-cache --virtual .install-deps openssl libffi-dev openssl-dev \
       python3 python3-dev bash g++ zlib zlib-dev jpeg jpeg-dev \
       ca-certificates gnupg openssl git curl \
  && wget "https://github.com/Yelp/dumb-init/releases/download/v${DUMB_INIT_VERSION}/dumb-init_${DUMB_INIT_VERSION}_amd64" \
  && wget "https://github.com/Yelp/dumb-init/releases/download/v${DUMB_INIT_VERSION}/sha256sums" \
  && grep "dumb-init_${DUMB_INIT_VERSION}_amd64$" sha256sums | sha256sum -c \
  && rm sha256sums \
  && mv dumb-init_${DUMB_INIT_VERSION}_amd64 /usr/bin/dumb-init \
  && chmod +x /usr/bin/dumb-init

RUN    luarocks install lua-resty-statsd          3.0.3-1 \
    && luarocks install lua-cmsgpack              0.4.0 \
    && luarocks install lua-cjson                 2.1.0.6-1 \
    && luarocks install basexx                    0.4.0-1 \
    && luarocks install lua-resty-jwt             0.2.0-0 \
    && luarocks install lua-resty-jit-uuid        0.0.7-1 \
    && luarocks install lua-resty-reqargs         1.4-1

# Section (till nginx-jwt installation) below is a temporal approach to decrease build time and the source of Pipfile's - legion/Pipfile* that have been copied here
# This workaround should be removed as soon as #226 is done
RUN ln -sf /usr/bin/python3.6 /usr/bin/python3
RUN pip3 install --disable-pip-version-check --upgrade pip==9.0.3 pipenv==2018.10.13

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --system --deploy --python python3.6

# Install Legion
ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN python3 -m pip install $pip_extra_index_params legion$pip_legion_version_string

WORKDIR /

RUN python3 -m compileall /usr/lib/python3.6/site-packages

# Staff
ADD start.sh /start.sh
ADD static /static
ADD nginx-jwt.lua \
    statistics_sender.lua \
    blacklisted_tokens.lua \
    fluentd_logger.lua \
    edge.lua \
      /usr/local/openresty/luajit/

ADD nginx.conf.ltmpl /nginx.conf.ltmpl

ENTRYPOINT ["dumb-init", "--"]
CMD ["/start.sh"]