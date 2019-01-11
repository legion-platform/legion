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
ARG version=latest
FROM legion/base-python-image:${version}

EXPOSE 5000

COPY uwsgi.ini /etc/uwsgi/

# Install Legion
ARG pip_extra_index_params=""
ARG pip_legion_version_string=""
RUN pip3 install --disable-pip-version-check $pip_extra_index_params legion$pip_legion_version_string

ENTRYPOINT []
CMD ["/usr/local/bin/uwsgi", "--strict", "--ini", "/etc/uwsgi/uwsgi.ini"]