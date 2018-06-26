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

RUN apk add --update \
    ca-certificates curl openrc docker \
    nginx pcre pcre-dev supervisor

RUN rc-update add docker boot 

EXPOSE 5000

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

# Make NGINX run on the foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/conf.d/
COPY uwsgi.ini /etc/uwsgi/
COPY app_uwsgi.ini /usr/local/lib/python3.5/dist-packages/legion/uwsgi.ini
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY chmod-docker-and-run-edi.sh /usr/local/bin/chmod-docker-and-run-edi.sh

ENV UWSGI_INI /usr/local/lib/python3.5/dist-packages/legion/uwsgi.ini

#ENTRYPOINT chmod a+rwx /var/run/docker.sock
CMD ["/usr/bin/supervisord"]

ENTRYPOINT ["/usr/local/bin/chmod-docker-and-run-edi.sh"]

ARG pip_extra_index_params=""
ARG pip_legion_version_string=""

RUN pip install --disable-pip-version-check $pip_extra_index_params legion$pip_legion_version_string
