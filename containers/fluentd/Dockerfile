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

FROM fluent/fluentd:v1.7-debian as builder
USER root
RUN apt-get -qq update && apt-get -y install zlib1g-dev libxml2-dev gcc make patch

# Install required fluentd plugins
RUN gem install -N fluent-plugin-s3:1.1.11 fluent-plugin-gcs:0.4.0 fluent-plugin-azure-storage-append-blob:0.1.1

FROM fluent/fluentd:v1.7-debian

COPY --from=builder /usr/local/bundle/ /usr/local/bundle/
