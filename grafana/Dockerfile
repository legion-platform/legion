#
#   Copyright 2017 EPAM Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
FROM grafana/grafana

COPY ./entrypoint.sh /entrypoint.sh
COPY ./bootstrap_grafana.sh /bootstrap_grafana.sh

RUN chmod a+rwx /entrypoint.sh
RUN chmod a+rwx /bootstrap_grafana.sh

ENTRYPOINT ["/entrypoint.sh"]

