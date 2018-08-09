#
#    Copyright 2018 EPAM Systems
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

FROM k8s.gcr.io/fluentd-elasticsearch:v2.0.4

# Add testing repo for python3.6
RUN echo "deb http://http.us.debian.org/debian/ testing main" >> /etc/apt/sources.list

# Install fluentd-s3 plugin, legion requirements and clean up apt cache
RUN gem install fluent-plugin-s3 -v '~>1.0.0' && \
    apt-get update && apt-get install -y --no-install-recommends python3 \
      g++ apt-utils python3-dev python3-pip python3-setuptools file wget git \
      libtiff5-dev libjpeg62-turbo-dev zlib1g-dev \
      libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev \
      tcl8.6-dev tk8.6-dev python-tk python3-tk procps locales && \
      apt-get clean && apt-get autoclean

# setup locale
RUN sed --in-place '/en_US.UTF-8/s/^#//' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8 
ENV LANGUAGE en_US:en 
ENV LC_ALL en_US.UTF-8

RUN pip3 install --disable-pip-version-check --no-cache-dir "numpy==1.14.3"

# Copy bootstrap script
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Copy template
COPY fluentd.t /etc/fluent/fluentd.t

# Install legion
ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN pip3 install $pip_extra_index_params legion$pip_legion_version_string

CMD /run.sh $FLUENTD_ARGS