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

RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.8/main' > /etc/apk/repositories \ 
	&& echo 'http://dl-cdn.alpinelinux.org/alpine/v3.8/community' >> /etc/apk/repositories \
        && apk upgrade -U -a

ADD requirements.txt /root/requirements.txt

RUN apk add --update --no-cache \
    python3 g++ python3-dev py-pip py-setuptools file wget git fribidi\
    tiff-dev jpeg-dev zlib-dev tcl-dev tk-dev python2-tkinter \
    python3-tkinter-tests freetype-dev lcms2-dev libwebp harfbuzz \
    libstdc++ musl-dev linux-headers build-base pcre pcre-dev\
    openblas-dev freetype-dev pkgconfig py-scipy=1.0.1-r1 py-numpy=1.14.3-r1\
    && ln -s locale.h /usr/include/xlocale.h

RUN pip3 install --disable-pip-version-check --upgrade pip==9.0.3
RUN pip3 install --disable-pip-version-check  --no-cache-dir -r /root/requirements.txt

WORKDIR /app
