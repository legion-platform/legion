#
#    Copyright 2019 EPAM Systems
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

FROM fluent/fluentd:v1.7

USER root

ARG REPO_URL=https://github.com/legion-platform/fluent-plugin-azure-storage-append-blob.git
ARG GIT_PARAMS="-c advice.detachedHead=false clone --branch 0.1.1"

# Install required fluentd plugins
RUN apk update \
 && apk add --no-cache --virtual .build-deps \
        build-base git \
        ruby-dev gnupg zlib-dev \
 && gem install fluent-plugin-s3 -v 1.1.11 \
 && gem install fluent-plugin-gcs -v 0.4.0 \
 && git ${GIT_PARAMS} ${REPO_URL} /tmp/build-azure \
 && cd /tmp/build-azure && gem build *.gemspec && gem install *.gem \
 && apk del .build-deps \
 && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem
