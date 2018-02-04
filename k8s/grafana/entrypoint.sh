#!/bin/bash
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

if [ ! -f /var/lib/grafana/bootstrapped ] && [ ! -z ${GF_GRAPHITE_DATASOURCE} ]; then
	./run.sh "${@}" &

    echo "Bootstrapping grafana for ${GF_GRAPHITE_DATASOURCE}..."
	legion_bootstrap_grafana "http://localhost:3000/" "${GF_GRAPHITE_DATASOURCE}"
    echo "Grafana has been bootstrapped"

	touch /var/lib/grafana/bootstrapped

	for job in `jobs -p`
    do
        wait $job
    done

else
	exec ./run.sh "${@}"
fi