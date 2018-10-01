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
FROM ubuntu:16.04

ENV DEBIAN_FRONTEND=noninteractive

# Add Python3.6 repository
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa 

RUN apt-get update && apt-get install -y --no-install-recommends python3.6 \
    g++ apt-utils build-essential python3.6-dev python3-pip python3-setuptools libpython3.6-dev \
    apt-transport-https file wget curl git libtiff5-dev libjpeg8-dev zlib1g-dev \
    tcl8.6-dev tk8.6-dev python-tk python3-tk libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev \
    libfribidi-dev tcl8.6-dev tk8.6-dev python-tk python3-tk libpcre3 libpcre3-dev locales && \
    apt-get clean && apt-get autoclean

# setup locale
RUN locale-gen en_US.UTF-8 && update-locale LANG=en_US.UTF-8
COPY default_locale /etc/default/locale
RUN chmod 0755 /etc/default/locale
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

RUN ln -sf /usr/bin/python3.6 /usr/bin/python3

COPY requirements.txt /root/requirements.txt

RUN pip3 install --disable-pip-version-check --upgrade pip==9.0.3 numpy==1.14.3
RUN pip3 install --disable-pip-version-check --no-cache-dir -r /root/requirements.txt

WORKDIR /app
