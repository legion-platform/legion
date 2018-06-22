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
FROM alpine:3.7

ADD requirements.txt /root/requirements.txt

# Theano requires C++ compiler to produce effective code
RUN apk add --update \
    python3
RUN apk add --update \
    g++ python3-dev py-pip py-setuptools file wget git \
    tiff-dev jpeg-dev zlib-dev
RUN apk add --update \
    tcl-dev tk-dev python2-tkinter python3-tkinter-tests \
    freetype-dev lcms2-dev libwebp harfbuzz fribidi

RUN pip3 install --upgrade pip==9.0.3 \
    && pip3 install -r /root/requirements.txt

WORKDIR /app
