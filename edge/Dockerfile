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
FROM openresty/openresty:alpine

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

ENV CTMPL_VERSION 0.19.3
RUN set -x \
  && apk add --no-cache --virtual .install-deps ca-certificates gnupg openssl \
  && gpg --keyserver keys.gnupg.net --recv-keys 91A6E7F85D05C65630BEF18951852D87348FFC4C \
  && wget https://releases.hashicorp.com/consul-template/${CTMPL_VERSION}/consul-template_${CTMPL_VERSION}_linux_amd64.zip \
  && wget https://releases.hashicorp.com/consul-template/${CTMPL_VERSION}/consul-template_${CTMPL_VERSION}_SHA256SUMS \
  && wget https://releases.hashicorp.com/consul-template/${CTMPL_VERSION}/consul-template_${CTMPL_VERSION}_SHA256SUMS.sig \
  && gpg --batch --verify consul-template_${CTMPL_VERSION}_SHA256SUMS.sig consul-template_${CTMPL_VERSION}_SHA256SUMS \
  && grep consul-template_${CTMPL_VERSION}_linux_amd64.zip consul-template_${CTMPL_VERSION}_SHA256SUMS | sha256sum -c \
  && unzip -d /bin consul-template_${CTMPL_VERSION}_linux_amd64.zip \
  && rm -rf consul-template_* /root/.gnupg \
  && apk del .install-deps

RUN set -x \
  && apk add --no-cache --virtual .install-deps ca-certificates gnupg openssl git curl luarocks5.3 \
  && luarocks-5.3 install lua-resty-statsd 3.0.3-1 \
  && apk del .install-deps


COPY start.sh /start.sh
COPY statistics_sender.lua /usr/local/share/lua/5.3/statistics_sender.lua

ENTRYPOINT ["dumb-init", "--"]
CMD ["/start.sh"]

