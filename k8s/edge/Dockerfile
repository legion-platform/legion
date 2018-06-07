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
FROM openresty/openresty:1.13.6.2-alpine

# Dumb-init
ENV DUMB_INIT_VERSION 1.2.0
RUN set -ex \
  && apk add --no-cache --virtual .install-deps openssl \
  && wget "https://github.com/Yelp/dumb-init/releases/download/v${DUMB_INIT_VERSION}/dumb-init_${DUMB_INIT_VERSION}_amd64" \
  && wget "https://github.com/Yelp/dumb-init/releases/download/v${DUMB_INIT_VERSION}/sha256sums" \
  && grep "dumb-init_${DUMB_INIT_VERSION}_amd64$" sha256sums | sha256sum -c \
  && rm sha256sums \
  && mv dumb-init_${DUMB_INIT_VERSION}_amd64 /usr/bin/dumb-init \
  && chmod +x /usr/bin/dumb-init \
  && apk del .install-deps

# Python3
RUN apk update \
  && apk add python3 python3-dev bash g++ zlib zlib-dev jpeg jpeg-dev \
  && python3 -m pip install argparse jinja2 kubernetes urllib3 aionotify==0.2.0

RUN python3 -m pip install --upgrade pip==9.0.3
RUN python3 -m pip install "Pillow==5.0.0"
RUN python3 -m pip install "numpy==1.14.3"

# LUA
RUN set -x \
  && apk add --no-cache --virtual .install-deps ca-certificates gnupg openssl git curl luarocks5.3 \
  && luarocks-5.3 install lua-resty-statsd 3.0.3-1 \
  && apk del .install-deps

# Install Legion
ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN python3 -m pip install $pip_extra_index_params legion$pip_legion_version_string

# Staff
COPY start.sh /start.sh
COPY statistics_sender.lua /usr/local/share/lua/5.3/statistics_sender.lua
COPY static /static
COPY nginx.conf.ltmpl /nginx.conf.ltmpl

ENTRYPOINT ["dumb-init", "--"]
CMD ["/start.sh"]
