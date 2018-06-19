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
FROM legion/base-python-image

RUN apt-get update && apt-get install --yes \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian jessie stable"

RUN apt-get update && apt-get install --yes docker-ce

# Standard set up Nginx
ENV NGINX_VERSION 1.13.7-1~stretch
ENV NJS_VERSION   1.13.7.0.1.15-1~stretch

RUN set -x \
	&& apt-get update \
	&& apt-get install --no-install-recommends --no-install-suggests -y nginx libpcre3 libpcre3-dev

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 5000

# Install uWSGI
RUN pip install uwsgi

# Make NGINX run on the foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/conf.d/
COPY uwsgi.ini /etc/uwsgi/

RUN apt-get update && apt-get install -y supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV UWSGI_INI /usr/local/lib/python3.5/dist-packages/legion/uwsgi.ini

ENV NGINX_MAX_UPLOAD 0

ENV LISTEN_PORT 5000

COPY chmod-docker-and-run-edi.sh /usr/local/bin/chmod-docker-and-run-edi.sh
RUN chmod a+rwx /usr/local/bin/chmod-docker-and-run-edi.sh
ENTRYPOINT ["/usr/local/bin/chmod-docker-and-run-edi.sh"]

COPY app_uwsgi.ini /usr/local/lib/python3.5/dist-packages/legion/uwsgi.ini
RUN rm /etc/nginx/sites-enabled/default

CMD ["/usr/bin/supervisord"]

ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN pip install $pip_extra_index_params legion$pip_legion_version_string
