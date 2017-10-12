#!/bin/bash

if [ ! -f /var/lib/grafana/bootstrapped ] && [ ! -z ${GF_GRAPHITE_DATASOURCE} ]; then
	./run.sh "${@}" &
	sleep 120

	/bootstrap_grafana.sh

	pkill grafana-server
	sleep 10
	
	touch /var/lib/grafana/bootstrapped

	exec ./run.sh "${@}"
else
	exec ./run.sh "${@}"
fi